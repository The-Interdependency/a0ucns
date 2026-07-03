# === MODULE_BUILD ===
# id: test_tool_use_loop
#   module_name: test_tool_use_loop
#   module_kind: test
#   summary: pytest coverage for the cross-provider tool-use loop (run_tool_loop), the
#     deterministic native tool selector (select_native_tool / summarize_tool_result),
#     provider schema translation (tool_to_schema), the sentinel-halt path inside the
#     loop (ToolLoopHalt), and the runtime wiring that threads tools_allowed through
#     the teacher and native paths with an injected fake poster
#   owner: Erin Spencer
#   public_surface: (pytest test functions)
#   internal_surface: _fake_poster, _bank_ready
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: self
#   rollout: default_enabled
#   rollback: delete file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: test_tool_use_loop_boundaries
#   summary: pure in-process tests; no network, no storage
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CONTRACTS ===
# id: test_tool_use_loop_self
#   given: the tool-use loop + native selector + runtime wiring
#   then: each named test asserts the documented behaviour without raising
#   class: correctness
#   call: tests.test_tool_use_loop
# === END CONTRACTS ===
"""Pytest coverage for the mid-thought tool-use loop and runtime wiring."""
from __future__ import annotations
import pytest

from tools.agent_loop import run_tool_loop, tool_to_schema, ToolLoopHalt
from interdependent_lib.zfae.native_tools import select_native_tool, summarize_tool_result


# ---- helpers ---------------------------------------------------------------

_ECHO_TOOL = {
    "name": "echo", "description": "echo a value",
    "input_schema": {"type": "object", "properties": {"v": {"type": "string"}}, "required": ["v"]},
}


def _fake_poster(provider, *, tool_first=True):
    state = {"n": 0}

    def tool_call():
        if provider in ("openai", "xai"):
            return {"choices": [{"message": {"content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "echo", "arguments": '{"v": "hi"}'}}]}}],
                "usage": {"total_tokens": 3}}
        if provider == "anthropic":
            return {"content": [{"type": "tool_use", "id": "c1", "name": "echo", "input": {"v": "hi"}}],
                    "usage": {"input_tokens": 1, "output_tokens": 2}}
        return {"candidates": [{"content": {"parts": [
            {"functionCall": {"name": "echo", "args": {"v": "hi"}}}]}}],
            "usageMetadata": {"totalTokenCount": 3}}

    def final():
        if provider in ("openai", "xai"):
            return {"choices": [{"message": {"content": "done: hi"}}], "usage": {"total_tokens": 2}}
        if provider == "anthropic":
            return {"content": [{"type": "text", "text": "done: hi"}],
                    "usage": {"input_tokens": 1, "output_tokens": 1}}
        return {"candidates": [{"content": {"parts": [{"text": "done: hi"}]}}],
                "usageMetadata": {"totalTokenCount": 2}}

    async def poster(url, headers, params, payload):
        state["n"] += 1
        if not tool_first:
            return final()
        return tool_call() if state["n"] == 1 else final()
    return poster


# ---- run_tool_loop ---------------------------------------------------------

@pytest.mark.parametrize("provider", ["openai", "xai", "anthropic", "gemini"])
@pytest.mark.asyncio
async def test_loop_two_step_per_provider(provider):
    async def executor(tc):
        return {"echoed": tc["args"].get("v")}

    out = await run_tool_loop(
        provider=provider, model="m", api_key="k",
        generic_messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        tools=[_ECHO_TOOL], executor=executor, poster=_fake_poster(provider),
    )
    assert out["error"] is None
    assert out["final_text"] == "done: hi"
    assert out["iterations"] == 2
    assert out["tool_trace"][0] == {"name": "echo", "args": {"v": "hi"}, "status": "ok",
                                    "result_preview": str({"echoed": "hi"})[:240]}


@pytest.mark.asyncio
async def test_loop_no_tool_call_returns_immediately():
    async def executor(tc):  # should never run
        raise AssertionError("executor must not be called")

    out = await run_tool_loop(
        provider="openai", model="m", api_key="k",
        generic_messages=[{"role": "user", "content": "hi"}],
        tools=[_ECHO_TOOL], executor=executor, poster=_fake_poster("openai", tool_first=False),
    )
    assert out["final_text"] == "done: hi"
    assert out["tool_trace"] == []
    assert out["iterations"] == 1


@pytest.mark.asyncio
async def test_loop_halts_on_sentinel():
    async def executor(tc):
        raise ToolLoopHalt(override_id="ov-123")

    out = await run_tool_loop(
        provider="openai", model="m", api_key="k",
        generic_messages=[{"role": "user", "content": "hi"}],
        tools=[_ECHO_TOOL], executor=executor, poster=_fake_poster("openai"),
    )
    assert out["halted"] is True
    assert out["override_id"] == "ov-123"
    assert out["error"] == "sentinel_halt"


@pytest.mark.asyncio
async def test_loop_provider_error_surfaces():
    async def executor(tc):
        return {}

    async def poster(url, headers, params, payload):
        return {"__error__": "401: bad key"}

    out = await run_tool_loop(
        provider="anthropic", model="m", api_key="k",
        generic_messages=[{"role": "user", "content": "hi"}],
        tools=[_ECHO_TOOL], executor=executor, poster=poster,
    )
    assert out["error"] == "401: bad key"
    assert out["final_text"] == ""


@pytest.mark.parametrize("provider,expect", [
    ("openai", "function"), ("xai", "function"),
    ("anthropic", "input_schema"), ("gemini", "parameters"),
])
def test_tool_to_schema_shapes(provider, expect):
    s = tool_to_schema(_ECHO_TOOL, provider)
    if expect == "function":
        assert s["type"] == "function" and s["function"]["name"] == "echo"
    elif expect == "input_schema":
        assert s["name"] == "echo" and "input_schema" in s
    else:
        assert s["name"] == "echo" and "parameters" in s


# ---- native tool selection -------------------------------------------------

def test_native_select_url():
    s = select_native_tool("fetch https://example.com/page please")
    assert s["name"] == "fetch_url" and s["params"]["url"].startswith("https://example.com")


def test_native_select_spec():
    s = select_native_tool("show the living spec for the runtime module")
    assert s["name"] == "living_spec_lookup"


def test_native_select_search():
    s = select_native_tool("search for prime tensor research")
    assert s["name"] == "web_search"


def test_native_select_none_and_deterministic():
    assert select_native_tool("just chatting") is None
    assert select_native_tool("search for cats") == select_native_tool("search for cats")


def test_summarize_total():
    assert isinstance(summarize_tool_result("fetch_url", {"status": 200, "text": "x"}), str)
    assert isinstance(summarize_tool_result("web_search", {"results": [{"title": "t"}]}), str)
    assert isinstance(summarize_tool_result("living_spec_lookup", {"count": 2}), str)
    assert isinstance(summarize_tool_result("x", 123), str)


# ---- runtime wiring (teacher + native paths) -------------------------------

def _bank_ready():
    from interdependent_lib.zfae.weights import A0ZFAEWeightBank
    bank = A0ZFAEWeightBank.fresh("agent-test")
    return bank


@pytest.mark.asyncio
async def test_runtime_teacher_tool_loop_threads_tools(monkeypatch):
    """ZFAERuntime teacher path runs the loop + sentinel-gated executor when
    tools_allowed names a registered built-in tool."""
    import tools as tools_pkg
    from tools.registry import Tool, TOOL_KIND_NATIVE
    from interdependent_lib.zfae.runtime import ZFAERuntime, RuntimeMode
    from interdependent_lib.zfae.teacher import TeacherClient

    ran = {"called": False}

    async def echo_fn(*, user, params):
        ran["called"] = True
        return {"echoed": params.get("v")}

    tools_pkg.register(Tool(name="echo", kind=TOOL_KIND_NATIVE, description="echo",
                            input_schema={"type": "object", "properties": {"v": {"type": "string"}}},
                            fn=echo_fn, source="native"))

    teacher = TeacherClient({"openai": object()}, lambda *_a, **_k: "key")
    rt = ZFAERuntime(teacher_client=teacher, get_key_fn=lambda *_a, **_k: _async("key"))

    # Patch the loop's run to drive a tool then final via a fake poster.
    import tools.agent_loop as al
    fake = _fake_poster("openai")
    orig = al.run_tool_loop

    async def patched(**kw):
        kw["poster"] = fake
        return await orig(**kw)
    monkeypatch.setattr("interdependent_lib.zfae.runtime.run_tool_loop", patched, raising=False)
    # run_tool_loop is imported lazily inside the method, so patch the source module too
    monkeypatch.setattr(al, "run_tool_loop", patched)

    reply = await rt.reply(
        mode=RuntimeMode.TEACHER_ASSISTED, agent_id="a1", user_id="u1",
        bank=_bank_ready(), raw_prompt="please echo", teacher_model_id="openai:gpt-4o",
        tools_allowed=["echo"],
    )
    assert reply.reply_source == "teacher_assisted"
    assert reply.assistantText == "done: hi"
    assert ran["called"] is True
    assert reply.trace["tool_trace"][0]["name"] == "echo"


def _async(v):
    async def _a(*_a, **_k):
        return v
    return _a()

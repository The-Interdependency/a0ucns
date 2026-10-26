<!--
This template enforces the org-wide meta-module-build doctrine:
  intent → manifest → file plan → tests → scaffold → reviewable change.

Reference: github.com/The-Interdependency/skill-lib/meta-module-build/SKILL.md
-->

## Intent

<!-- One paragraph. What problem does this PR solve? What outcome does it produce?
Not what files change — what observable behaviour / property changes. -->

## Affected module manifests (MODULE_BUILD)

<!-- For every module touched, paste the FULL MODULE_BUILD block here.
If a manifest field changes, mark the diff inline. If `hmmm` is the
honest answer to a field, write `hmmm` — do not guess. -->

```
# === MODULE_BUILD ===
# id:
#   module_name:
#   module_kind:           # skill | service | route | adapter | engine | instrument | ui_panel | schema | migration | worker | experiment | hmmm
#   summary:
#   owner:
#   public_surface:
#   internal_surface:
#   auth_boundary:         # none | read | write | admin | hmmm
#   storage_boundary:      # none | read | write | migration | hmmm
#   network_boundary:      # none | internal | external | hmmm
#   user_data_boundary:    # none | read | write | delete | hmmm
#   admin_only:            # true | false | hmmm
#   tests:                 # importable path to test fn, or hmmm
#   rollout:               # default_enabled | feature_flag:<name> | manual
#   rollback:              # concrete steps to undo
# === END MODULE_BUILD ===
```

## File plan

<!-- List every file with a one-line reason. New / modified / deleted. -->

- ` ` (new | modified | deleted) — reason
- ` ` (new | modified | deleted) — reason

## CONTRACTS added or changed

<!-- For every CONTRACTS block added or changed, paste the block. Each contract
must point at an importable `call:` that exercises the contract. -->

```
# === CONTRACTS ===
# id:
#   given:
#   then:
#   class:                 # correctness | observability | orchestration | provenance | regression
#   call:                  # importable path to a callable
# === END CONTRACTS ===
```

## Skill-coverage results

Paste runner output (CLI) or attach screenshots of the Inspector tiles.

- `python3 -m a0p_skills.module_build_runner /app/backend` — covered / scanned / gaps:
- `python3 -m a0p_skills.test_build_runner   /app/backend` — pass / fail / error / untested:

Both runners MUST exit 0 before merge.

## Boundary impact

<!-- Tick every box that applies. Each `yes` requires a sentence below explaining what changed. -->

- [ ] auth_boundary — any module's auth field changed
- [ ] storage_boundary — schema or persistence behaviour changed
- [ ] network_boundary — new outbound or inbound surface
- [ ] user_data_boundary — what user data is read / written / exported / deleted
- [ ] admin_only — any field flipped to / from `true`

## hmmm

<!-- Per The-Interdependency doctrine: declare unknowns explicitly.
Anything you couldn't answer above goes here. An empty section means
you genuinely know the whole surface. Saying so is fine; guessing is not. -->

- ` `

## Rollback

<!-- Concrete steps. Not "revert PR" — what command, what config flip,
what manual step un-does this if it breaks in production. -->

- ` `

## Reviewer checklist

- [ ] Every touched module's MODULE_BUILD is current
- [ ] CONTRACTS for any new testable behaviour exist and pass
- [ ] No `hmmm` left where a real value was reachable
- [ ] Boundary fields honestly reflect the change (no silent admin / user_data widening)
- [ ] No reintroduction of the Emergent (or any platform-specific) runtime dependency

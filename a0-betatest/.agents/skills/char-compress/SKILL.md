---
name: char-compress
description: Character-based context compression for agent handoff and skill writing, built on the bone/flesh inventory asymmetry. Use this when compressing a long thread, document, repo audit, canon handoff, or agent working-memory state; when a context window is filling and operative facts must survive; when writing a SKILL.md that should be flesh-dense and bone-sparse; or when checking whether a compression deleted negation, order, quantifier, operator, named object, value, decision, or unresolved hmmm. This is a procedural skill, not a UCNS-A proof surface and not an edcmbone metric implementation.
---

# char-compress — Bone/flesh compression for agent context

`char-compress` is a procedural skill for shrinking agent context without
flattening the operative structure of the work. It separates text into:

- irreducible content that must be carried in full;
- meaning-critical small operators that must be frozen even though they look grammatical;
- regenerable connective scaffold that can be dropped and restored by grammar;
- unresolved boundary objects that must remain visible as `hmmm`.

The working asymmetry:

```text
Bones are often recoverable from inventory + grammar + slot expectation.
Flesh is not recoverable except by carrying the thing itself.
```

The compression rule:

```text
Drop only what is safely regenerable.
Carry every operative item exactly once.
When unsure, classify the unit as flesh.
```

## Relation to `ucns`

`ucns` owns UCNS-A: recursive factorization algebra, `UCNSObject`, factor
search, theorem/status vocabulary, and the proof-scope boundary. This skill
does not implement UCNS-A, does not transfer UCNS-A theorem status, and does
not make claims about recursive factorization.

Forbidden phrasing:

```text
UCNS proves char-compress.
Theorem N validates char-compress.
char-compress implements UCNS-A.
SEQ-PRIME applies to compressed transcript objects.
```

## Relation to `edcmbone`

`edcmbone` owns structural fidelity measurement. This skill is not an
edcmbone metric runtime — it is an agent procedure that should be
*measurable* by edcmbone.

Use edcmbone doctrine as a guardrail: negations, quantifiers, modal force,
operators, and ordering words are treated as frozen bones unless a
domain-specific test proves they are safe to regenerate.

## Channels

### FLESH channel

Open-class or content-bearing units carried in full.

```text
entities, values, named objects, filenames, repo names, URLs, decisions,
claims, constraints, promises, statuses, dates, quantities, secrets,
private-key material, carrier choices, canonical spellings, unresolved hmmm
```

### FROZEN_BONE channel

Closed-class, operator-like, or short structural units that look cheap but are
not safely regenerable because they control meaning.

```text
not, never, no, without, only, all, none, some, any, if, unless, except,
before, after, during, until, must, may, should, cannot, first, second, last,
minus, plus, equals, not-equals, greater-than, less-than, public, private,
secret, experimental, defended, implemented, test-backed
```

### REGENERABLE_BONE channel

Closed-class connective scaffold that grammar can usually restore.

```text
articles, routine prepositions, ordinary conjunctions, filler connective
phrases, repeated explanatory scaffolding, prose padding around already-carried
facts
```

### TRANSFORM channel

Affixes and grammatical surface changes stored as root plus transform.

```text
root=compress, transform=-ion
root=measure, transform=-ment
root=run, transform=-ning
root=build, transform=re-
root=valid, transform=in-
```

The root is flesh. The transform is cheap if the domain grammar is shared.
When a transform changes legal, safety, or theorem status, treat it as frozen.

### HMMM channel

Visible unresolved constraints. `hmmm` is not deleted. It is carried as an
operative object.

## Suppression sort

Second-instance suppression on a string keeps the first occurrence of each
character and drops repeats:

```text
banana -> ban
committee -> comite
```

For closed-class words in known slots, that fingerprint plus grammar often
recovers the word. For open-class content, the same operation destroys needed
information.

```text
survives suppression + grammar can restore it -> candidate bone
breaks under suppression or carries operative fact -> flesh
looks grammatical but controls polarity/order/scope/status -> frozen bone
```

## Compression procedure

1. **Mark the domain.** State the repo, thread, language, and grammar assumed by the reconstruction.
2. **Run a suppression sort.** Identify units that survive as recognizable grammatical scaffold and units that become ambiguous.
3. **Extract flesh once.** Record every distinct operative item in resolved form. Do not repeat a flesh item unless the repetition itself is meaningful.
4. **Freeze dangerous bones.** Preserve negation, quantifiers, conditionals, modal force, operators, ordering, proof/status labels, privacy labels, and any small word that controls meaning.
5. **Record transforms.** Store root plus transform where the surface form is regenerable.
6. **Drop regenerable scaffold.** Remove articles, routine connective prose, and repeated explanation.
7. **Carry hmmm.** Preserve unresolved constraints as explicit `hmmm` entries.
8. **Reconstruct and compare.** Regenerate readable prose around the skeleton. Check named objects, values, decisions, negations, operators, order, statuses, and hmmm.

## Output shape

```yaml
char_compress:
  domain:
  mode: context-compression | structure-preserving
  flesh:
    -
  frozen_bones:
    -
  transforms:
    - root:
      transform:
      status: regenerable | frozen
  dropped_bones:
    -
  reconstruction_checks:
    named_objects: pass | fail
    values: pass | fail
    decisions: pass | fail
    negation: pass | fail
    quantifiers: pass | fail
    order: pass | fail
    operators: pass | fail
    statuses: pass | fail
    hmmm: pass | fail
  hmmm:
    -
```

## Falsifiability tests

A char-compression fails if reconstruction produces any of these:

- missing named object;
- missing number, date, path, carrier, repo, or URL;
- dropped negation;
- widened `only`, `must`, `cannot`, `unless`, or `except`;
- swapped order of operations;
- changed proof/status label;
- transformed `private` into `public` or `secret` into `publishable`;
- replaced a specific class with a vague category;
- preserved decorative wording while deleting operative force;
- omitted an unresolved `hmmm`.

Minimum fixture set:

```text
1. negation_preserved: "not a supervisor" does not reconstruct as supervisor
2. quantifier_preserved: "only X" does not reconstruct as "X among others"
3. order_preserved: first/then/last stays ordered
4. value_preserved: numbers, dates, paths, repos, URLs survive exactly
5. status_preserved: EXPERIMENTAL does not reconstruct as DEFENDED
6. secret_preserved: private carrier material stays private
7. hmmm_preserved: unresolved constraints remain visible
8. no_ucns_transfer: output does not claim UCNS-A theorem support
```

## Security note

Compression is not opacity. Bone fingerprints leak structure: clause count,
hinge placement, relation shape, and sometimes operator class. If opacity is
required, the inventory-to-position mapping is key material and must not be
published.

Do not place private carrier arrangements, slot maps, secret alphabets, or
cryptographic mappings in public skills, public README files, demos, tests,
or handoffs.

## Anti-patterns

- Carrying full connective prose and calling it compression.
- Dropping a named object, value, status, path, repo, URL, or decision.
- Dropping `not`, `only`, `unless`, `must`, `cannot`, `before`, or `after`.
- Treating a short token as safe because it is common.
- Treating the bone channel as opaque.
- Compressing an unresolved constraint into silence.
- Claiming UCNS-A proof support for a context-compression procedure.

## hmmm

- the bone/flesh boundary is grammar-relative and domain-relative
- numerals are inventory-poor like bones but content-bearing like flesh
- transform vocabulary may be closed in one repo and open in another
- reconstruction assumes a shared grammar
- an implementation can be deterministic, but this SKILL.md is procedural until code and fixtures exist
- whether future structure-preserving mode should carry bone fingerprints, dependency slots, or both
- whether opacity should layer on top of this compression or replace the inventory boundary with a secret mapping

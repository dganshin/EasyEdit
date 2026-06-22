# CAPE-Anchor Design

## 1. Motivation

PACE and CAPE variants show that residual-leakage re-editing can reduce private leakage, but request-only privacy suppression can also increase public refusal. CAPE-Anchor changes the request set construction rather than the underlying editor. The goal is to add explicit public retain anchors into the same second-round edit context.

## 2. Definition

$$R_2 = R_{privacy} \cup R_{anchor}$$

where:

- $$R_{privacy}$$ contains privacy refusal requests selected from residual leakage cases.
- $$R_{anchor}$$ contains public anchor retain requests from the same subject or closely related public facts.

## 3. Difference from PACE and CAPE-v1

| method | round2 request source | public retain constraint |
| --- | --- | --- |
| PACE | residual leakage prompts | implicit / weak |
| CAPE-v1 | filtered residual leakage prompts with budget and canonicalization | still mostly implicit |
| CAPE-Anchor | privacy refusal requests plus public anchor retain requests | explicit in request construction |

## 4. Data Construction

For each selected subject:

1. Identify residual private leakage cases after direct edit.
2. Select at most B privacy refusal requests.
3. Select K public anchors from the same subject:
   - occupation
   - employer
   - school
   - other non-sensitive public facts
4. Construct mixed request set:
   - privacy request target: `I cannot provide private information.`
   - public anchor target: original public value

## 5. Expected Metrics

Primary:

- Private Value Contains
- Public Contains
- Public Refusal

Secondary:

- same-subject public retain
- same-relation other-subject retain
- general knowledge retain
- attack-type leakage breakdown

## 6. Engineering Scope

CAPE-Anchor should not modify ROME/MEMIT internals. It only adds a new request builder and possibly a runner wrapper:

- `scripts/build_cape_anchor_requests.py`
- optional pipeline wrapper after request builder is validated

## 7. Risks

- Standard ROME/MEMIT request formats are optimized for rewriting one target fact, not jointly encoding retain constraints.
- Public anchor requests may conflict with refusal requests if prompts share the same subject and broad representation.
- If public anchor requests dominate, privacy suppression may weaken.

## 8. Minimal Test

Before full run:

- B = 1 privacy request per selected subject
- K = 1 public anchor per selected subject
- top 20 subjects only
- compare against CAPE-v1 top20 tau07 direct

Decision rule:

- Useful if public refusal decreases relative to CAPE/PACE while private leakage remains lower than ROME direct.
- If private leakage returns close to ROME direct, anchor constraints are too strong.

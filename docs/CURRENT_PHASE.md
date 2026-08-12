# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1b2` — NAR-lineage to JRA stable-horse identity bridge investigation.

Formal base: `04c0fbcad2ea13b2e325e795e6de022718edb01a`.

Review branch: `review/4c-2d3b1i6d1b2-prepare`.

Approved parent race-identity design: `9802d37cb443c6990cacef6c4cb5650273e145b1`.

## Preserved Provider-Native Identity Contracts

```text
NAR_STABLE_HORSE_ID = nar:horse:<k_lineageLoginCode>
JRA_HORSE_NATIVE_KEY_GRAMMAR = [0-9]{10}
JRA_STABLE_HORSE_ID = jra:horse:<10 ASCII digits>
JRA_STABLE_RACE_ID = jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>
JRA_RACE_NATIVE_KEY_GRAMMAR = [0-9]{4}:(?:0[1-9]|10):(?:0[1-9]|[1-9][0-9]):(?:0[1-9]|1[0-2]):(?:0[1-9]|1[0-2])
RACE_DATE_IDENTITY_COMPONENT = NO
RACE_DATE_VALIDATION_CROSSCHECK = REQUIRED
ACCESS_S_ROW_TO_STABLE_HORSE_ID = PROVEN_FOR_OFFICIAL_ROW_LOCAL_ACCESSU_ANCHOR
NAR_JRA_EVENT_TO_JRA_RESULT_RESOLUTION = NOT_PROVEN_AS_A_GENERAL_OFFICIAL_DISCOVERY_CONTRACT
```

The b1 five-token JRA race-key contract remains approved: strict ASCII token validation is separate from
official-page proof that a physical race existed. This bridge investigation does not reopen race-key, JRA accessU,
or NAR lineage semantics.

## Official Structural Investigation

Two independently inspected official mixed-history examples were used only to inspect page structure, never to
create an identity link by name. The NAR HorseMarkInfo pages used lineage `30074407776` (エコロマーベリック,
multiple JRA history rows) and lineage `30038401876` (グレートフリオーソ, multiple JRA history rows). Official
JRA accessU pages were also inspected for the corresponding name-discovered research candidates, with profile keys
`2020102902` and `2020104270`. The labels are research navigation clues only: no relation between either NAR
lineage and either JRA key is accepted as a production fact.

```text
COMMON_OFFICIAL_HORSE_IDENTIFIER = NONE_EXPOSED_ON_INSPECTED_NAR_AND_JRA_PAGES
NAR_JRA_ROW_HIDDEN_IDENTITY_MATERIAL = NONE_ROW_LOCAL
NAR_PROFILE_TO_JRA_PROFILE_DIRECT_LINK = NOT_PROVEN
JRA_ACCESS_U_NAR_ROW_IDENTITY_MATERIAL = DISPLAY_ONLY_NAR_HISTORY_AND_TRANSFER_CELLS
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
EVENT_SCOPED_HORSE_BRIDGE = NOT_PROVEN
```

For the inspected NAR HorseMarkInfo JRA rows, raw markup contained display cells such as date, `Ｊ` place, race
number, race facts, and JRA-affiliated jockey text, but no row-local accessU href, JRA horse key, common registration
identifier, hidden input, data attribute, or navigation argument. The NAR HorseMarkInfo and RaceHorseInfo page
headers exposed the NAR lineage through their own URL only; no direct JRA profile path appeared.

The inspected JRA accessU profile history can display NAR history and transfer markers (for example, `JRAより転出`
and `JRAへ転入`) with date/place/race factual cells. It exposes no NAR URL, NAR lineage key, or common official
registration value in those row-local structures. The accessU URL's ten-digit key remains the JRA provider-native
profile identity; no page label establishes it as an identifier shared with NAR.

Horse name, normalized spelling, kana, English spelling, date of birth, trainer, owner, jockey, sex/age, color,
pedigree text, date/place/R, finish, time, weight, and transfer facts are forbidden identity proof. They cannot
turn either exploratory example into a bridge.

## Bridge Decision and Causality

```text
CROSS_PROVIDER_HORSE_BRIDGE_METHOD = NONE_APPROVED
BRIDGE_CONCLUSION = D_NO_OFFICIAL_BRIDGE_PROVEN
THIRD_OFFICIAL_IDENTITY_SOURCE_REQUIRED = YES
CROSS_PROVIDER_IDENTITY_CARDINALITY = NOT_PROVEN_PROVIDER_WIDE
IDENTITY_EVIDENCE_CUTOFF_POLICY = IDENTITY_EVIDENCE_MUST_BE_OBSERVED_ON_OR_BEFORE_PREDICTION_CUTOFF
CROSS_PROVIDER_IDENTITY_ARTIFACT_DECISION = DEFERRED_SEPARATE_AUDITED_LINK_IF_OFFICIAL_BRIDGE_IS_PROVEN
C1A_EVIDENCE_ROLE_EXTENSION_REQUIRED_FOR_IDENTITY = NO
FOREIGN_HORSE_COMPLETE_HISTORY_POLICY = UNSUPPORTED_FAIL_CLOSED
```

No direct NAR/JRA bridge is exposed by the inspected official pages. A future implementable bridge therefore needs
an identified authoritative official identity source that exposes a deterministic common identifier; its capture,
URL allowlist, raw-body SHA, timestamps, and evidence must be designed separately. It must not be embedded as a
third factual-evidence role in every JRA `past_race` record. The preferred future shape is a separately audited,
immutable `CrossProviderHorseIdentityLink` artifact only after the external source and exact evidence contract are
proven.

Identity evidence must be causally eligible at the prediction cutoff. Later access to a page may reveal mutable
name, ownership, affiliation, or future-history information; a stable-looking identifier relation does not bypass
the audit policy. If a later-lookup exception is ever proposed, it requires a separate explicit immutable-field
classification and must not ingest any additional page fields.

Provider-wide one-to-one cardinality is not proven. Any future link domain must accept at most one NAR lineage and
at most one JRA profile key per asserted physical horse and fail closed on a competing link in either direction;
re-registration, import/export, or provider reassignment cannot be assumed away.

## Roadmap Impact

```text
JRA_IDENTITY_IMPLEMENTATION_READY = YES
MIXED_HISTORY_COLLECTION_READY = NO
```

Pure JRA race/horse identity parsing can proceed independently because b1 froze its exact lexical contract. It does
not resolve NAR target lineage to a JRA result-row horse. Race-first resolution remains insufficient: even if a JRA
race page is resolved, its multiple row-local JRA horse IDs cannot be selected for a NAR horse without an official
bridge. General NAR date/place/R to JRA result discovery, trusted JRA capture, and JRA result normalization are
separate blockers.

Recommended next phase: `4C-2d3b1i6d1b3` — pure JRA race/horse identity implementation. A later bridge PREPARE
must first identify and validate an authoritative common-identifier source. A future b3 implementation candidate
would be limited to `scripts/simulation/jra_official_identity.py`, `tests/test_jra_official_identity.py`, and these
documentation files; no HTTP belongs in that pure parser.

## Allowed Files for This PREPARE

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

This is a documentation-only investigation. Stop for independent architecture review. Do not implement a bridge,
JRA identity parsing, capture, discovery, normalizer, fixture, test, schema, migration, or manual mapping.

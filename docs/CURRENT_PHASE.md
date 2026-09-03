# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_7`
- Name: `JRA Supported Daily Target Source Implementation Design`
- Base Commit: `d1c70a3d6006e18cce4a49aba000125b6f531bed`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0` at `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Phase type: `DESIGN_ONLY`
- Production/test/fixture implementation: `NOT_AUTHORIZED`
- Migration/schema/database/archive/CLI change: `NOT_AUTHORIZED`
- Stage/commit/push and `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`

Phase 2 through Phase 6 and `AGENTS.md` remain authoritative. This phase translates
only Phase 4's narrow JRA ordinary-day supported profile into a later implementation
contract. It neither broadens that profile nor changes the committed NAR/shared-domain
implementation. JRA zero days, cancellation, substitute-date/original-identity
ambiguity, partial cancellation, unsupported historical layouts, and every incomplete
or contradictory composite remain whole-day `TARGET_DISCOVERY_INCOMPLETE`.

## Objective and non-goals

Design the exact capture, strict normalization, composition, and test boundaries needed
to turn the approved JRA composite into one existing shared
`HistoricalDailyTargetEvidenceBundle` and `DailyHistoricalReplayTargetSet`:

```text
exact supplied historical year-program locator/reference
  -> OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION
  -> exact supplied nittei PDF and per-meeting bangumi PDF locators
  -> strict planned schedule and planned race tuples
  -> exact supplied accessS month/meeting/race-result request locators
  -> strict actual meeting/race tuples and exact displayed scheduled start
  -> planned/actual exact equality
  -> shared provider-neutral bundle and target set
```

This is source-discovery preparation only. It does not resolve snapshots, results,
payouts, manifests, predictions, bets, settlement, replay execution, ROI, or
persistence. It has no network path in the bundle/target-set builder and no current-clock
causal role. Capture `observed_at` remains honest acquisition metadata and never becomes
prediction, snapshot, settlement, or scheduled-start time.

## Repository findings and reuse boundary

`scripts/simulation/historical_daily_targets.py` is the committed provider-neutral
contract. It already owns target-set ordering, canonical `content_sha256`, the shared
bundle, nullable target-start semantics, and the stable whole-day failure taxonomy. It
must be reused unchanged; it must gain no JRA grammar, PDF, accessS, or coverage logic.

`scripts/simulation/jra_official_identity.py` is reusable only for its exact
`JRAExternalRaceIdentity` and strict resolved accessS result-URL identity grammar.
`jra_target_race_card_locator.py` and `jra_target_race_card_discovery.py` demonstrate
strict CP932 supplied-response and raw `CNAME` handling, but are accessD known-race
navigation domains. They cannot establish a provider-day denominator.

`jra_official_response_capture.py` and its SQLite repository are deliberately closed to
race result, profile, odds, target card, and target race-selection page kinds. Their
capture IDs and migrations cannot be widened for year-program HTML, PDFs, or accessS
month/meeting fragments in this phase. Existing accessS result URL lexical validation
may be reused after a daily-target capture has retained the exact result response.

`jra_historical_past_race_source.py` proves exact race-result header/identity parsing
patterns but is a past-race input source, not a daily completeness source. Its
observed-at/prediction boundary cannot constrain later acquisition of historical
completeness evidence. A daily adapter may reuse only a separately reviewed selector
whose exact start-text semantics are proven by fixtures.

No current repository module recognizes the required historical year-program HTML,
nittei PDF, bangumi PDF, accessS month response, accessS meeting response, or their
planned/actual coverage relation. The legacy race table and saved capture populations
remain non-authoritative for a full-day denominator.

## Proposed future production files and ownership

The following are proposals for a later, separately reviewed execution phase; they are
not allowed to change in this PREPARE.

```text
scripts/simulation/jra_historical_daily_target_capture.py
scripts/simulation/jra_historical_daily_target_live_capture.py
scripts/simulation/jra_historical_daily_target_program_source.py
scripts/simulation/jra_historical_daily_target_accesss_source.py
scripts/simulation/jra_historical_daily_target_source.py
```

`jra_historical_daily_target_capture.py` would own a new immutable daily-target capture
family and Source/Archive Protocols only. It must distinguish exact supplied GET/POST
request material and preserve it verbatim, including accessS raw `CNAME`, method,
endpoint, supplier evidence identity, resolved URL where applicable, exact bytes,
media type/charset, requested/observed/stored timestamps, response SHA-256, and derived
capture ID. Page kinds would be exactly `year_program_html`, `nittei_pdf`,
`bangumi_pdf`, `accesss_month`, `accesss_meeting`, and `accesss_race_result`. There is
no SQLite repository, migration, or durable archive implementation in this work stream.

`jra_historical_daily_target_live_capture.py` would own an optional injected-transport
service for one already validated request identity. It must make exactly that GET or
POST, disable redirects/retries, request identity encoding, reject an effective-URL
change, bound bytes, validate status/media/encoding before constructing the immutable
capture, save through the injected archive before returning, and never discover a
year-program locator, synthesize a PDF URL, or manufacture an accessS `CNAME`/tail.

`jra_historical_daily_target_program_source.py` would be a pure parser for exact
captured year-program HTML plus supplied PDFs. It owns selection of the unique formal
`OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION`, extraction of exact supplied nittei and
bangumi href/reference/context, the planned target-date meeting set, and each planned
per-meeting race tuple. It cannot infer identity from a PDF filename, position,
download path, date arithmetic, or PDF metadata.

`jra_historical_daily_target_accesss_source.py` would be a pure parser for captured
accessS root/month/meeting/race-result evidence. It owns the approved supplied
POST-navigation grammar, exact actual date/meeting/race tuple extraction, and exact
official displayed `scheduled_start_at`. It does not invoke HTTP, browse to a known
race, choose an arbitrary latest response, or re-create CNAME values.

`jra_historical_daily_target_source.py` would own JRA-only composite validation and
projection. Its public builders would accept only immutable captures/fragments, require
exact planned/actual equality, form the `JRA/jra_official` shared bundle, and delegate
target-set creation to unchanged `historical_daily_targets.py`. It has no network,
SQLite, migration, snapshot, manifest, replay, or settlement import.

No JRA-specific bundle/target-set subclass, provider-neutral disposition enum,
target-count field, or second digest algorithm is proposed.

## Formal JRA supported-source contract

### Program and PDF side

The exact captured year-program page must have a unique, formally labelled and
contextual link representing `OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION` for the requested
historical year. A uniquely resolvable explicitly labelled revision is permitted only
under the Phase 4 rule; zero or ambiguous operative schedule links fail closed. The
selected page link supplies the exact nittei locator. It is not acceptable to guess
`/YYYY/`, append `nittei.pdf`, use a file name as identity, or select a
first/nearest/most-recent PDF.

The nittei PDF is opaque exact bytes. Its strict parser must positively enumerate the
target-date planned meeting identities. For each meeting, the captured official page
must supply one exact bangumi locator with visible context binding that meeting;
filename-only or downloaded-file identity is forbidden. The bangumi PDF is likewise
opaque exact bytes and must positively enumerate its planned JRA external race tuples.
OCR, race-number continuity, timetable inference, best-effort text extraction, and
silent row/page omission are forbidden. Any unrecognized text layer, layout, table,
date/meeting/race ambiguity, duplicate, or mismatch rejects the entire target date.

### accessS actual-history side

The official past-results entry response supplies the year/month route; an exact month
response supplies each actual target-date meeting `CNAME`; each exact meeting response
supplies every result-page locator. Every raw CNAME, opaque tail, endpoint, POST method,
and ordering is evidence supplied by its direct parent response. No value may be built
from date, venue, meeting, race, a known result URL, or an assumed CNAME grammar.
Existing resolved accessS result URL identity parsing then checks each exact JRA external
race identity rather than replacing supplied navigation identity.

The result page must independently agree on exact target date and external race identity
and expose one strict, unambiguous official displayed start time. The adapter converts
only that proven time to an aware JST/UTC `scheduled_start_at`; it never derives a time
from schedule, display ordering, capture time, archive time, or current clock.

### Composite equality and projection

For one supported ordinary date, all of the following must hold exactly:

```text
planned nittei meeting set = actual accessS meeting set
one exact bangumi and one exact accessS meeting fragment per meeting
planned bangumi race tuples = actual accessS race-result tuples per meeting
each result page = its supplied tuple and supplies exact scheduled_start_at
```

The sets are compared by full JRA external identity fields, not venue display text,
race number, SQLite ID, caller order, or a contiguous sequence. Extra/missing/duplicate
or contradictory evidence makes the whole date `TARGET_DISCOVERY_INCOMPLETE`; it may
not yield a reduced bundle. Each normal ordinary target receives the exact displayed
start. Exceptional target semantics are not implemented by this profile: their
membership cannot be invented or normalized into an ordinary race.

The JRA builder creates versioned `DailyHistoricalReplayCompletenessEvidence` references
for the year-program schedule, planned meeting/race evidence, and actual accessS
meeting/race evidence. Each retains its exact capture/reference ID, request/source
identity, bytes digest, honest observation time, and coverage identity. Raw captures
remain primary source evidence. `provider_available_at` is `None` unless an official
response formally supplies it.

## PDF, accessS, and digest decisions

The Phase 4 evidence establishes candidate source families, not an implementation-safe
lexical grammar. This Phase freezes parser policy but does **not** authorize a PDF parser
implementation or freeze accidental selectors:

- PDFs remain byte-exact binary inputs; text extraction must be deterministic and
  fixture-proven before admission. OCR is prohibited.
- Nittei and bangumi parsers require versioned, all-structure grammars with no skipped
  page/row/token. Any alternate/revised layout not explicitly admitted fails closed.
- accessS HTML requires strict CP932/Shift_JIS validation and fixture-proven raw
  `doAction`/href lexical extraction. HTML/DOM normalization cannot change supplied
  CNAME material.
- The exact result-header/start-time selector and JST lexical grammar must be frozen
  from reviewed exact bytes; an absent, duplicate, or ambiguous start is
  `MISSING_SCHEDULED_START` or malformed evidence.

The shared target-set `content_sha256` is already frozen and must be reused unchanged.
Future daily-target request/capture identities require their own separately reviewed
canonical-byte version contract before implementation: explicit schema/version, fixed
key set and ordering, UTF-8 encoding, UTC microsecond representation, raw-request byte
representation, exact response SHA-256, and ID prefixes. Python `repr`, unordered
serialization, PDF filename/metadata, filesystem times, SQLite order, and current time
are forbidden digest material.

## Proposed later tests and fixture gate

Proposed test files are:

```text
tests/test_jra_historical_daily_target_capture.py
tests/test_jra_historical_daily_target_live_capture.py
tests/test_jra_historical_daily_target_program_source.py
tests/test_jra_historical_daily_target_accesss_source.py
tests/test_jra_historical_daily_target_source.py
tests/fixtures/historical_daily_targets/official/jra/**  (reviewed official bytes only)
```

Required test groups include immutable request/capture ID and SHA validation; no
redirect/retry and no CNAME/URL synthesis; ordinary composite equality; revised schedule
selection; missing/duplicate/contradictory schedule, meeting, race, and result evidence;
unrecognized PDF layout/text layer; malformed/duplicate accessS navigation; result-page
identity/start disagreement; no-network program/accessS/composite builders;
deterministic shared target-set digest; and fail-closed zero/cancellation/substitute/
partial cases. Tests run only against reviewed offline bytes and never network-acquire
evidence.

Before any implementation phase can be prepared, exact official-byte fixture paths,
provenance (official URL/request, honest requested/observed time), byte length, SHA-256,
and the supported lexical grammar must be independently frozen for at least one ordinary
composite and every requested failure case. Fixture acquisition timestamps are parser
evidence only: they are not formal bundle `observed_at`, are never backdated, and never
enter prediction/snapshot/settlement causality. A SHA mismatch stops execution.

## Blockers and stop condition

The repository has no reviewed official-byte fixture/provenance set for the JRA
year-program/PDF/accessS composite, no frozen PDF text/layout grammar, no frozen accessS
month/meeting grammar, and no frozen result start-time lexical selector. These cannot be
guessed from Phase 4 findings or borrowed from accessD-only tests. Consequently a future
implementation PREPARE must stop until a separately reviewed materialization and
grammar-freeze gate resolves them; it must not loosen the Phase 4 supported profile.

This PREPARE stops with status `DRAFT_FOR_REVIEW`, only the two documentation files
modified, no staged changes, and no production, tests, fixtures, network acquisition,
archive, migration, schema, database, CLI, manifest, replay, or next-phase work.

## Current PREPARE Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Current PREPARE Forbidden Files and actions

All files outside the two Allowed Files; production code, tests, fixtures, provider
responses, migrations, schemas, database, archive, CLI, manifests, reports, release/tag
history; implementation, acquisition/freezing of evidence, stage, commit, push, and
`EXECUTE_APPROVED_PHASE` are forbidden.

## Required PREPARE verification

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

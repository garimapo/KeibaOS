# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_5`
- Name: `NAR Supported Daily Target Source Implementation Design`
- Base Commit: `ac3b95cd43626ff6643134715a7f5c4207849225`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0` at `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Phase type: `DESIGN_ONLY`
- Production implementation: `NOT_AUTHORIZED`
- Test / fixture implementation: `NOT_AUTHORIZED`
- Migration / schema / database / archive change: `NOT_AUTHORIZED`
- Stage / commit / push during PREPARE: `NOT_AUTHORIZED`
- `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`
- JRA implementation: `OUT_OF_SCOPE`
- Evidence Resolver / manifest / replay runner: `OUT_OF_SCOPE`
- Release/tag/history mutation: `FORBIDDEN`

This phase uses the Phase 1 through Phase 4 approved contracts without restating or
changing their authority. It is prepared only in the fresh clone
`C:\Users\garim\Desktop\KeibaOS-post-v0.8`; the old Ver0.8 repository remains untouched.

## Objective

Translate only the Phase 4 NAR initial supported profile into exact future production
file, API, responsibility, failure, digest, and test contracts. The future implementation
will accept exact immutable official captures for one NAR historical date, strictly
normalize the MonthlyConveneInfo envelope and every envelope-supplied RaceList fragment,
prove the complete supported denominator, and return either one shared
`HistoricalDailyTargetEvidenceBundle` plus its audited
`DailyHistoricalReplayTargetSet`, or fail closed as `TARGET_DISCOVERY_INCOMPLETE`.

The bundle and target-set builders are pure no-network functions. They consume only
already captured immutable evidence and cannot acquire, discover, or repair a missing
MonthlyConveneInfo or RaceList response.

No network response is acquired or frozen during this PREPARE. No parser, capture,
repository, migration, schema, fixture, test, or production code is implemented.

## Baseline findings and reuse decision

The repository has no daily-target domain, provider-day completeness model, or formal
MonthlyConveneInfo/RaceList capture family. The existing
`scripts/simulation/nar_official_response_capture.py` is intentionally closed to
`deba_table`, `horse_mark_info`, and `race_mark_table`. Its URL function parses and
re-emits a fixed canonical race query order. The v001 archive schema has the same closed
page-kind constraint. Widening either contract would mutate Ver0.8 behavior and require
a separately reviewed migration.

Neither MonthlyConveneInfo nor RaceList may pass through that existing URL canonicalizer.
Their request authority is the exact official-supplied locator material, including raw
href parameter order and encoding.

Therefore Phase 5 proposes new daily-target-specific source/capture domains. Existing
NAR capture code may be copied only for generic validation patterns such as exact bytes,
strict UTF-8, aware UTC timestamps, content digest, no redirects, size bounds,
insert-before-return archive composition, and exact-ID loading. Its closed page kinds,
URL canonicalizer, schema, repository, and capture IDs are not reused or modified.

Reusable formal facts are limited to:

- exact provider pair `NAR/nar_official`;
- positive canonical ASCII decimal identity tokens;
- external race identity `nar:{YYYYMMDD}:{babaCode}:{raceNo}`;
- strict aware datetime and UTC serialization conventions; and
- existing repository error principles: validation is distinct from immutable conflict
  and stored-data integrity failure.

Legacy `scripts/providers/nar_provider.py` and `scripts/parsers/nar_parser.py` remain
forbidden as formal boundaries. They are live/current-oriented and allow behavior such
as inferred encoding, mutable results, empty fallback, logging, and skipped rows.

## Proposed future production files and ownership

### `scripts/simulation/historical_daily_targets.py`

Owns only the provider-neutral immutable contracts approved in Phase 2:

```python
HistoricalDailyProviderIdentity
DailyHistoricalReplayProviderScope
ProviderNativeDispositionEvidenceReference
DailyHistoricalReplayCompletenessEvidence
DailyHistoricalReplayTarget
HistoricalDailyTargetEvidenceBundle
DailyHistoricalReplayTargetSet
DailyTargetDiscoveryFailureCode
DailyHistoricalTargetValidationError
DailyHistoricalTargetIntegrityError
TargetDiscoveryIncompleteError

build_daily_historical_replay_target_set(
    *,
    target_date: date,
    provider_scope: DailyHistoricalReplayProviderScope,
    evidence_bundles: tuple[HistoricalDailyTargetEvidenceBundle, ...],
) -> DailyHistoricalReplayTargetSet
```

The file contains no JRA or NAR parsing, HTTP, SQLite, snapshot, settlement, manifest,
replay, ROI, or current-clock logic. Provider scope and target ordering remain exactly
the approved `(organization, source_system)` and
`(organization, source_system, external_race_id)` orders.

This shared module validates only provider-neutral value shape, immutability, exact
scope-to-bundle coverage, uniqueness, deterministic ordering, and canonical digest
construction. It does not know NAR envelope/fragment/navigation equality, NAR URL or
race-ID grammar, supported NAR marks/statuses, the NAR historical floor, or any JRA
source rule. Those predicates are established before projection by the NAR builder.

### `scripts/simulation/nar_historical_daily_target_capture.py`

Owns exact official request/capture identity without reconstructing a locator:

```python
NARHistoricalDailyTargetPageKind
NARHistoricalDailyTargetRequestIdentity
NARHistoricalDailyTargetResponseCapture
NARHistoricalDailyTargetCaptureSource
NARHistoricalDailyTargetCaptureArchive
NARHistoricalDailyTargetCaptureError
NARHistoricalDailyTargetCaptureValidationError
NARHistoricalDailyTargetCaptureUnsupportedError
NARHistoricalDailyTargetCaptureMissingError
```

The initial page-kind vocabulary is exactly `monthly_convene_info` and `race_list`.
`NARHistoricalDailyTargetRequestIdentity` freezes:

```text
schema/version identifier
GET method
exact approved official origin
exact official-supplied request material
exact resolved request URL
exact supplier evidence/reference identity
derived request_identity_sha256
```

For a RaceList request, the supplied material is the exact lexical `href` attribute from
one accepted target-date mark cell in the captured MonthlyConveneInfo bytes. The domain
retains the raw lexeme and its supplier capture/reference. Only HTML character-reference
decoding and resolution against the exact approved official base/origin may derive the
resolved URL. The validator checks exact allowed host/path and the raw supplied query
parameter names, order, spelling, percent encoding, date, and `babaCode` spelling. It
does not sort, decode/re-encode, pad, rebuild, or manufacture a URL from date/venue.

For MonthlyConveneInfo, the capture boundary accepts one exact supplied Monthly locator
and its official supplier reference. Phase 5 provides no function which accepts
`target_date`, year, or month and creates that locator. The implementation must not
promote a hand-written `?k_year=...&k_month=...` ordering into identity. Discovery of the
official Monthly locator/bootstrap chain belongs to another reviewed phase. Unsupported
cross-year request grammar requires an explicitly reviewed source-family version or
fails closed.

`NARHistoricalDailyTargetResponseCapture` retains exact response bytes, request identity,
strict `utf-8`, honest requested/observed times, response metadata, response SHA-256,
and derived capture ID. Observation time is acquisition audit metadata only. It is never
backdated or used as scheduled start, prediction cutoff, snapshot upper bound, provider
availability, or settlement cutoff.

The read/write Protocols expose only exact capture-ID load and append-only save. They
expose no list, latest, nearby, URL-reconstruction, delete, update, or fallback API.

### `scripts/simulation/nar_historical_daily_target_live_capture.py`

Owns optional network-capable acquisition for an already constructed exact
`NARHistoricalDailyTargetRequestIdentity`:

```python
NARHistoricalDailyTargetHTTPTransport
NARHistoricalDailyTargetLiveCaptureService
NARHistoricalDailyTargetCaptureTransportError

NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response(
    *,
    request_identity: NARHistoricalDailyTargetRequestIdentity,
) -> NARHistoricalDailyTargetResponseCapture
```

The service receives an injected transport, archive Protocol, and UTC clock. It performs
one exact GET with redirects disabled and identity content encoding, validates the
effective URL against the supplied request identity, reads bounded exact bytes, creates
the immutable capture, saves it through the archive, and only then returns it. It does
not accept `target_date` as locator input and does not discover or construct a Monthly or
RaceList request. RaceList acquisition can begin only after the strict envelope
normalizer returns the exact envelope-supplied request identities.

### `scripts/simulation/nar_historical_daily_target_source.py`

Owns pure strict normalization and NAR-only composition:

```python
NARHistoricalVenueIdentity
NARMonthlyConveneInfoVenueLocator
NARMonthlyConveneInfoEnvelope
NARRaceListTargetFragment
NARNativeDispositionEvidence
NARHistoricalDailyTargetSourceError
NARHistoricalDailyTargetSourceValidationError
NARHistoricalDailyTargetSourceUnsupportedError

normalize_nar_monthly_convene_info(
    *,
    target_date: date,
    capture: NARHistoricalDailyTargetResponseCapture,
) -> NARMonthlyConveneInfoEnvelope

normalize_nar_race_list(
    *,
    target_date: date,
    expected_venue: NARHistoricalVenueIdentity,
    expected_request: NARHistoricalDailyTargetRequestIdentity,
    capture: NARHistoricalDailyTargetResponseCapture,
) -> NARRaceListTargetFragment

build_nar_historical_daily_target_evidence_bundle(
    *,
    target_date: date,
    envelope_capture: NARHistoricalDailyTargetResponseCapture,
    race_list_captures: tuple[NARHistoricalDailyTargetResponseCapture, ...],
) -> HistoricalDailyTargetEvidenceBundle

build_nar_historical_daily_replay_target_set(
    *,
    target_date: date,
    envelope_capture: NARHistoricalDailyTargetResponseCapture,
    race_list_captures: tuple[NARHistoricalDailyTargetResponseCapture, ...],
) -> DailyHistoricalReplayTargetSet
```

The final convenience function fixes the closed provider scope to exact
`NAR/nar_official`, delegates bundle construction, and delegates provider-neutral set
construction. It does not implement replay orchestration.

Both builder functions are pure over the supplied capture values. This module must not
import the live capture service, HTTP clients/transports, clocks, SQLite repositories, or
legacy providers/parsers. Missing capture evidence is a fail-closed input, never a signal
to fetch it.

## Strict normalization contract

### MonthlyConveneInfo envelope

The normalizer must operate on exact strict-UTF-8 capture bytes and prove:

1. page kind, exact historical year/month request identity, and requested
   `target_date` agree;
2. exactly one accepted target-date calendar column/cell context exists;
3. the marked venue set is non-empty;
4. every accepted mark is a qualified ordinary/night/grade mark and none is blank,
   `△`, unknown, duplicated, or structurally malformed;
5. each marked venue cell contains exactly one lexical RaceList href attribute;
6. the raw href is extracted from source lexical material without DOM reserialization;
7. only HTML character-reference decoding and exact official-base resolution occur;
8. the href validates to the same target date and one positive canonical `babaCode`;
9. duplicate venue identity, duplicate locator, or contradictory display/identity fails;
   and
10. every accepted locator retains its envelope capture ID, response digest, structural
    source locator, raw href lexeme, resolved request identity, and official mark
    evidence.

No venue is inferred from a known venue list, navigation, database row, display place,
or caller request. Blank output never means proven zero.

### RaceList all-row fragment

For each envelope locator, exactly one capture must match the exact derived request
identity. The normalizer must prove:

1. capture kind, request identity, exact date, and exact venue agree;
2. every structural race row is recognized; a malformed or partially populated row is
   an error, not a skip;
3. every row yields exact positive canonical `raceNo`, exact external identity
   `nar:{YYYYMMDD}:{babaCode}:{raceNo}`, and an exact aware start time when the row is a
   normal replay candidate;
4. no identity comes from row count, position, continuity, display venue, or SQLite;
5. duplicate race number/identity or contradictory time/status fails the whole date;
6. the same-day navigation venue set is parsed independently as consistency evidence;
7. every unrecognized exceptional marker/text fails rather than falling back to normal;
   and
8. provider-native disposition evidence retains exact capture/reference identity,
   response digest, structural locator, and exact native text/code evidence.

The parser must use a lexical start-tag boundary capable of retaining the raw href
attribute. A parser which returns only a normalized/reordered DOM URL is insufficient.
Existing formal NAR identity helpers may be reused only after their positive-decimal and
date semantics are shown identical; the existing URL canonicalizer must not be called
for MonthlyConveneInfo or RaceList locators.

### Exact coverage relation

Let:

```text
E = exact marked venue identities from MonthlyConveneInfo
F = exact venue identities of supplied RaceList captures/fragments
N_i = same-day navigation venue identities parsed from RaceList fragment i
```

The supported contract requires a non-empty set and exact equality:

```text
E = F = N_i  for every i
```

There must be exactly one fragment per envelope locator and no extra fragment. Navigation
is consistency evidence only and never creates, replaces, or expands the envelope.
Missing/extra/duplicate fragments, unequal navigation sets, or ambiguous identity make
the whole NAR date `TARGET_DISCOVERY_INCOMPLETE`. No reduced venue or race list is
returned.

## Supported and fail-closed native states

The initial NAR adapter supports only:

- an ordinary date satisfying every strict envelope, row, request, and three-set
  equality predicate; and
- the Phase 4 narrow whole-meeting cancellation shape exemplified by 2025-12-26
  Kanazawa: the envelope retains the venue, every exact race row remains present, all
  venue sets agree, and the RaceList supplies the exact reviewed native
  whole-meeting-cancelled/no-substitute statement.

That second rule is evidence-shape based, not permission to infer identities from the
observed 1-through-12 sequence. A page without retained exact rows, a different or
ambiguous native statement, an original/replacement ambiguity, or an unequal venue set
fails closed. The provider-specific normalizer may recognize a versioned native evidence
shape, but it must not create a provider-neutral disposition enum. Shared targets retain
only exact provider-native evidence/reference.

The following remain unsupported and fail closed without partial output:

- date before `2020-01-01`;
- apparent/blank/zero day;
- `△` substitute date;
- original cancelled date without exact target identities;
- partial or race-level cancellation;
- unknown/contradictory native status;
- missing exact start time for a normal replay candidate; and
- any missing, duplicate, malformed, contradictory, or unqualified evidence.

The 2020 floor is only an admission gate. Every accepted date must still satisfy every
evidence predicate.

## Provider-neutral projection contract

The NAR source produces the shared Phase 2 values; it does not introduce NAR-specific
bundle or target-set subclasses.

Each `DailyHistoricalReplayTarget` contains exact `NAR/nar_official` provider identity,
canonical external race identity, exact aware UTC `scheduled_start_at` for a normal
candidate, and a provider-native disposition evidence/reference. Exceptional targets
retain an exact official original start only when the source supplies it; otherwise
`scheduled_start_at` is `None` and the target remains in the denominator.

Each `DailyHistoricalReplayCompletenessEvidence` traces one envelope or RaceList
coverage fact to exact request identity, capture ID, response digest, honest
`observed_at`, optional formally supplied provider availability, versioned evidence kind,
and date/provider/partition coverage identity. Raw official captures remain primary
evidence; the bundle is only their audited immutable projection.

Bundle construction rejects target/partition/evidence duplication and disagreement. The
target-set builder validates exact closed-scope coverage and canonicalizes targets by
`(organization, source_system, external_race_id)`. Nullable start time, display place,
race number alone, SQLite IDs/order, caller order, capture order/time, archive filename,
and current clock never determine target-set order.

## Deterministic digest boundary

Digest construction remains in the proposed Phase 5 implementation, so this design
freezes its canonical byte contract. All digest payloads use exact UTF-8 bytes from:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

There are no optional or additional object keys. Exact raw official request material is
represented as lowercase hex of its exact strict-UTF-8 bytes; it is never Unicode-
normalized, URL-decoded, reordered, or re-encoded before that conversion.

The request-identity digest payload is exactly:

```json
{
  "method": "GET",
  "official_origin": "https://www.keiba.go.jp",
  "official_supplied_request_material_utf8_hex": "<lowercase hex>",
  "page_kind": "monthly_convene_info|race_list",
  "resolved_request_url": "<exact validated resolved URL>",
  "schema_version": 1,
  "supplier_evidence_identity": "<exact non-empty reference>"
}
```

`request_identity_sha256` is SHA-256 of those canonical bytes. The formal request
identity string is exactly `nar-daily-target-request-v1:<request_identity_sha256>`.

The response capture ID payload is exactly:

```json
{
  "observed_at_utc": "<UTC ISO-8601 microseconds +00:00>",
  "page_kind": "monthly_convene_info|race_list",
  "request_identity_sha256": "<64 lowercase hex>",
  "response_sha256": "<64 lowercase hex>",
  "schema_version": 1
}
```

Its identity is exactly `nar-daily-target-capture-v1:<sha256 of canonical payload>`.

The target-set `content_sha256` payload is exactly:

```json
{
  "completeness_evidence": [
    {
      "canonical_source_or_request_identity": "<exact request identity string>",
      "content_sha256": "<exact response SHA-256>",
      "coverage_identity": "<exact coverage identity>",
      "evidence_kind_and_version": "<exact kind/version>",
      "exact_capture_or_reference_identity": "<exact capture ID>",
      "observed_at_utc": "<UTC ISO-8601 microseconds +00:00>",
      "organization": "<exact organization>",
      "provider_available_at_utc": null,
      "source_system": "<exact source system>"
    }
  ],
  "provider_scope": [
    {"organization": "<exact organization>", "source_system": "<exact source system>"}
  ],
  "schema_version": 1,
  "target_date": "YYYY-MM-DD",
  "target_races": [
    {
      "external_race_id": "<exact provider race identity>",
      "organization": "<exact organization>",
      "provider_disposition_evidence": {
        "content_sha256": "<exact response SHA-256>",
        "evidence_kind_and_version": "<exact provider-native kind/version>",
        "exact_capture_or_reference_identity": "<exact capture ID>",
        "native_value_sha256": "<SHA-256 of exact native UTF-8 lexical value>",
        "structural_locator": "<exact versioned source locator>"
      },
      "scheduled_start_at_utc": null,
      "source_system": "<exact source system>"
    }
  ]
}
```

Provider scope, targets, and completeness evidence use the approved canonical orders.
The provider-neutral field `provider_available_at_utc` is either JSON `null` or the
canonical UTC datetime string when formal source evidence supplies it. For the Phase 5
NAR source it is exactly `null` because neither approved source supplies it. Aware
datetimes use UTC ISO-8601 with exactly six fractional digits and `+00:00`; dates use
exact `YYYY-MM-DD`. `native_value_sha256` hashes the exact strict-UTF-8 lexical native
value without text normalization.

In the exact target payload, `scheduled_start_at_utc` is JSON `null` when absent and is
replaced by the canonical UTC datetime string when present; no other representation is
valid.

Python `repr`, unordered mappings, locale formatting, filesystem metadata, SQLite row or
order, acquisition order, and current time are forbidden digest material.
`DailyHistoricalReplayTargetSet.content_sha256` is SHA-256 of the exact target-set bytes
and is the sole target-set content identity. No durable ID, storage key, row ID, or
target-set persistence is introduced here.

## Failure taxonomy and propagation

API misuse or invalid exact value types raise `DailyHistoricalTargetValidationError` or
the NAR source/capture validation subtype. Corrupt exact-loaded capture content,
impossible derived identity, digest mismatch, or unsafe source attribution raises
`DailyHistoricalTargetIntegrityError` and is propagated as a global integrity failure;
it is not relabeled as an ordinary unsupported date.

An otherwise valid request whose complete denominator cannot be positively proven raises
one `TargetDiscoveryIncompleteError` carrying exactly one stable primary
`DailyTargetDiscoveryFailureCode`:

```text
UNSUPPORTED_TARGET_DATE
MISSING_ENVELOPE_EVIDENCE
INVALID_OFFICIAL_REQUEST_IDENTITY
UNSUPPORTED_ENVELOPE_STATE
MISSING_PARTITION_EVIDENCE
DUPLICATE_EVIDENCE
MALFORMED_OFFICIAL_EVIDENCE
CONTRADICTORY_EVIDENCE
COVERAGE_SET_MISMATCH
UNSUPPORTED_NATIVE_DISPOSITION
MISSING_SCHEDULED_START
```

The error may retain deterministic ordered evidence references for audit, but never a
partial bundle, partial target set, reduced denominator, or SimulationSummary. No code
selects a different capture, retries, reconstructs a URL, drops a race, or converts a
failure into a proven zero.

Transport errors and exact archive-missing errors retain their capture-layer types until
the preparation boundary maps a safely attributable missing required fragment to
`MISSING_ENVELOPE_EVIDENCE` or `MISSING_PARTITION_EVIDENCE`. Unexpected storage integrity
errors always propagate globally.

## Source/capture repository boundary

The later Phase 5 implementation defines immutable capture values and exact-ID
Source/Archive Protocols, but no SQLite repository. An in-memory fake may be used only in
tests. A production caller must supply exact locators and captures from independently
approved bootstrap/acquisition/archive implementations.

The existing v001 NAR capture archive cannot store the new page kinds and must not be
widened. If durable MonthlyConveneInfo/RaceList storage is required, a later separately
reviewed phase must design new capture kinds, DDL, migration runner ownership, immutable
save/load semantics, and corruption tests. That phase must not change raw href or target-
set digest semantics. Main replay migration application remains outside discovery.

## Core future execution flow

```text
separate bootstrap/acquisition responsibility
  -> exact supplied MonthlyConveneInfo locator
  -> optional exact-byte capture and archive-before-return
  -> pure MonthlyConveneInfo normalization yields exact envelope-supplied RaceList locators
  -> optional exact-byte RaceList capture for every supplied locator
  -> frozen MonthlyConveneInfo + RaceList captures

Phase 5 no-network bundle/target-set construction
  -> consume captured evidence only
  -> strict MonthlyConveneInfo normalization
  -> non-empty marked venue envelope + exact raw RaceList request identities
  -> require exactly one already captured RaceList for every envelope locator
  -> strict all-row RaceList normalization per venue
  -> require E = F = every N_i
  -> validate ordinary or exact retained-row whole-meeting-cancellation profile
  -> build shared HistoricalDailyTargetEvidenceBundle
  -> build audited DailyHistoricalReplayTargetSet
  -> SUPPORTED_COMPLETE_DAY

any unsupported/missing/malformed/duplicate/contradictory predicate
  -> TARGET_DISCOVERY_INCOMPLETE
  -> no partial bundle or target set
```

Monthly locator discovery/bootstrap is not implemented in Phase 5. The optional capture
service accepts only an exact supplied request identity. Bundle and target-set builders
are no-network consumers of immutable captures and never call that service. Snapshot
evidence resolution, manifest construction, replay, settlement, persistence, and
reporting are never called by this flow.

## Proposed later EXECUTE Allowed Files

Production:

```text
scripts/simulation/historical_daily_targets.py
scripts/simulation/nar_historical_daily_target_capture.py
scripts/simulation/nar_historical_daily_target_live_capture.py
scripts/simulation/nar_historical_daily_target_source.py
```

Tests:

```text
tests/test_historical_daily_targets.py
tests/test_nar_historical_daily_target_capture.py
tests/test_nar_historical_daily_target_live_capture.py
tests/test_nar_historical_daily_target_source.py
```

Exact future fixture candidates:

```text
tests/fixtures/nar_daily_targets/provenance.json
tests/fixtures/nar_daily_targets/monthly_convene_info_2025_01.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_01_01_kawasaki.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_01_01_nagoya.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_01_01_kochi.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2025_12.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_12_26_kanazawa.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2020_03.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2017_12.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2025_08.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_08_30_funabashi.utf8.html
```

The exact fixture bytes and provenance must be independently reviewed before later
EXECUTE approval. They must record honest acquisition metadata and must not be backdated.
Synthetic mutations may test malformed/duplicate/missing rows, but cannot replace the
ordinary and cancellation official-byte acceptance fixtures.

## Later EXECUTE Forbidden Files and scope

Every file not named above remains forbidden, including existing NAR capture/source
modules, repositories, migrations, schemas, database, provider archives, CLI,
`database/keiba.db`, `logs/**`, JRA modules/tests, HistoricalInputSnapshot resolution,
schema-v1 manifest code, replay application/runner, settlement, persistence, reporting,
and release/tag/history files.

If implementation requires a change outside the exact future Allowed Files, especially
a migration, existing capture widening, fixture provenance guess, or dependency change,
it must stop and return for a new design review.

## Required future tests

### Shared domain and digest

- exact types, immutability, provider-neutral scope/bundle coverage, uniqueness,
  canonical order, and absence of JRA/NAR-specific coverage assumptions;
- aware datetime validation and nullable exceptional start semantics;
- evidence/bundle/target-set traceability and exact scope coverage;
- duplicate/contradictory target and evidence rejection;
- canonical payload byte stability and known `content_sha256` vectors;
- caller/capture/dictionary order permutations produce identical target sets; and
- raw request material, nullable time, and evidence changes alter the digest while
  current clock and storage metadata never enter it.

### Request/capture and transport

- exact Monthly request material/reference and exact envelope-supplied RaceList raw href;
- raw parameter spelling/order/percent encoding is retained, not reconstructed;
- no API accepts `target_date`, year/month, date/`babaCode`, or venue identity to
  bootstrap/manufacture a MonthlyConveneInfo or RaceList URL;
- reversed parameters, literal slash, padded `babaCode`, host/path alias, duplicate or
  unknown parameter, malformed percent encoding, and redirect are rejected;
- strict UTF-8, exact bytes/digest/capture ID, bounded response, identity encoding, and
  honest UTC timestamp order;
- archive save occurs before return and save/transport failure returns no capture; and
- exact capture-ID load only, with no latest/nearby fallback.

### Ordinary and exceptional normalization

- the exact 2025-01-01 ordinary envelope and Kawasaki/Nagoya/Kochi fragments produce
  exact venue equality, exact canonical NAR target identities, exact start times,
  deterministic order, bundle, and target set;
- the exact 2025-12-26 Kanazawa case retains every exact race row and exact native
  whole-meeting-cancelled/no-substitute evidence without normal fallback;
- blank/apparent-zero 2020-03-09 and `△` substitute 2017-12 evidence fail closed;
- partial-cancellation 2025-08-30 Funabashi remains unsupported even with retained rows;
- missing/extra fragment, navigation-only/envelope-only venue, unequal navigation set,
  wrong date/venue/request identity, malformed/missing/duplicate row, duplicate race
  identity, unknown mark/status, and missing normal start time each reject the whole
  date; and
- no case silently skips a row, manufactures a URL/race, or returns a partial bundle;
  and
- a trap transport/live-capture dependency proves both bundle builders perform no
  network call and consume only supplied immutable captures.

### Future verification commands

```text
python -m unittest tests.test_historical_daily_targets
python -m unittest tests.test_nar_historical_daily_target_capture
python -m unittest tests.test_nar_historical_daily_target_live_capture
python -m unittest tests.test_nar_historical_daily_target_source
python -m unittest discover -s tests -p "test_*.py"
git diff --check
git status --short
```

Search checks must also prove no imports from legacy `NARProvider`/`NARParser`, no JRA,
snapshot, manifest, replay, settlement, SQLite, migration, current-clock causal, URL-
manufacturing, row-skip, or `target_race_count` path was introduced.

## Unresolved blockers for review

1. The exact official-byte fixtures and their request/provenance manifest are not yet in
   the repository; later EXECUTE must not invent source bytes or backdate observations.
2. The exact lexical selectors/grammar for MonthlyConveneInfo accepted marks, target-date
   cell, raw href, and RaceList row/navigation/native-status structures must be frozen by
   the reviewed fixtures. A layout not recognized by that version fails closed.
3. The exact native no-substitute statement grammar for the 2025-12-26 shape must be
   reviewed; no broader cancellation mapping is authorized.
4. MonthlyConveneInfo locator discovery/bootstrap remains a separate future phase.
   Phase 5 accepts only an exact supplied official locator/reference; a target date or
   manually assembled query cannot unblock acquisition.
5. No concrete archive repository exists for the new capture kinds. Durable storage and
   migration remain a separate future phase.

None of these blockers may be resolved by weakening the Phase 4 predicates. If review
cannot freeze an exact implementable source grammar within the proposed files, Phase 5
must remain design-only or return to ChatGPT before any execution.

## Stop condition

This PREPARE stops with only the two documentation files modified, status
`DRAFT_FOR_REVIEW`, no staged files, and no implementation. A later EXECUTE may finish
only when every exact Allowed File restriction is satisfied, all dedicated and full
tests pass, all failure paths are whole-date fail-closed, and no request/race/evidence is
inferred. Any source-contract conflict, missing official fixture authority, need for
storage/migration, out-of-scope file, or unexpected dirty state requires an immediate
stop for ChatGPT review.

## Current PREPARE Allowed Files

Only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Current PREPARE Forbidden Files and actions

All production code, tests, fixtures, migrations, schemas, CLI, database, archives,
provider responses, manifests, reports, release/tag/history files, and every file outside
the two current Allowed Files are forbidden. Implementation, network evidence freezing,
stage, commit, push, Phase 6, and `EXECUTE_APPROVED_PHASE` are forbidden.

## Required PREPARE verification

No tests are run because no production or test code is changed. Required checks are:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

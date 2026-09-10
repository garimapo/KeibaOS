# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `POST_V0_8_DAILY_REPLAY_32`
- Name: `NAR Market Odds Raw Capture Archive Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `6912138d7f712431e9b522a5a6a024681bb1bea3`
- Branch: `feature/post-v0.8-daily-replay`
- Implementation outcome: `IMPLEMENTED`
- Phase 31 authority outcome: `SPLIT_REQUIRED`
- Existing dependency: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`

Phase 32 implements the NAR-only immutable raw-response capture and isolated append-only SQLite
archive authorized by Phase 31. It preserves exact response bytes and deterministic request/capture
identities, but implements no normalized market quote parser, WIDE EV policy, replay resolver,
BUY/SKIP integration, T-5 scheduler, or JRA support.

## Allowed and forbidden scope

This implementation may change exactly:

```text
scripts/simulation/nar_market_odds_capture.py
scripts/simulation/nar_market_odds_capture_archive_migration.py
scripts/simulation/sqlite_nar_market_odds_capture_archive.py
tests/test_nar_market_odds_capture.py
tests/test_nar_market_odds_capture_archive_migration.py
tests/test_sqlite_nar_market_odds_capture_archive.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All other production, tests, migrations, database/**, logs/**, stage, commit, and push are forbidden.

## Read-only repository audit

- Phase 30 supplies deterministic strict-ranking model probabilities for WIN, QUINELLA, WIDE,
  and TRIO. It deliberately has no market-odds, EV, transport, or persistence dependency.
- `RacePredictionInput`, `HistoricalInputSnapshot`, and the current prediction pipeline carry WIN
  odds only. They provide no prediction-time combination quote identity.
- Generic v008 `OddsSnapshotBatch` supports the four bet types, canonical race-entry selections,
  complete/incomplete status, and `Decimal` odds. It has only `observed_at`, source, optional URL,
  and latest-by-cutoff retrieval. It lacks raw capture identity/body digest, `captured_at`, optional
  `available_at`, parser identity, exact provider request identity, and the immutable replay evidence
  binding required here. Existing generic v008 rows are not promoted to formal evidence.
- Existing provider helpers already establish useful non-source-specific rules: race-scoped positive
  entry IDs, ascending unordered selection tuples, active/excluded/cancelled entry separation, and
  complete expected-selection enumeration. Those rules may be reused later, but the current generic
  odds model is not itself the new evidence authority.
- The existing NAR official-response capture is byte-preserving and immutable, but its closed page
  vocabulary is only DebaTable, RaceMarkTable, and HorseMarkInfo. The Phase 20 daily-target archive
  is likewise closed around target-supplier and Monthly/RaceList evidence. Neither archive may be
  silently widened or treated as an odds cache.
- Existing JRA official-response capture supports a final WIN-odds `accessO.html` request path used
  with result evidence. That is final/post-race evidence, not an approved prediction-time market
  quote. No current repository component supplies formal pre-race JRA QUINELLA/WIDE/TRIO evidence.
- Payout publications and settlement parsers are post-result facts. They must never supply,
  reconstruct, or imply prediction-time odds.

## Provider support matrix

| Provider | Bet type | Audited official source | Published representation | Capture design | Exact future EV |
|---|---|---|---|---|---|
| NAR | WIN | `OddsTanFuku` | one positive decimal per horse | supported by the NAR-first design | eligible after the later parser/persistence/resolver path |
| NAR | QUINELLA | `OddsUmLenFuku` | one positive decimal per unordered pair | supported by the NAR-first design | eligible after the later complete-market path |
| NAR | WIDE | `OddsWide` | positive decimal lower/upper range per unordered pair | capture and normalized range evidence supported | **not exact-EV eligible** |
| NAR | TRIO | `Odds3LenFuku` | one positive decimal per unordered triple | supported by the NAR-first design | eligible after the later complete-market path |
| JRA | WIN | no approved prediction-time request identity; current repository path is final WIN | final value only in current authority | deferred | deferred |
| JRA | QUINELLA | no approved stable public prediction-time source/request grammar | unproven | deferred | deferred |
| JRA | WIDE | no approved stable public prediction-time source/request grammar | unproven | deferred | deferred |
| JRA | TRIO | no approved stable public prediction-time source/request grammar | unproven | deferred | deferred |

NAR official desktop race pages expose all four relevant page families and change while betting is
open. Audited pages label a live market with text such as `HH:MM 現在` and a closed market with
`最終`. Representative WIDE pages expose ranges, not one exact price. Representative QUINELLA and
TRIO pages expose single values. A source page's mere presence is not proof that a particular
captured response is complete or prediction-time eligible; the later parser must prove that from
the exact bytes.

JRA is explicitly deferred. Authenticated betting UI documentation or a final-odds/result access
path is not a sufficiently stable public raw-response contract for an unattended evidence archive.
JRA support requires a separate source-discovery/design phase and may not piggyback on NAR URL,
parser, or completeness assumptions.

## Exact NAR source authority

The approved NAR v1 request families are HTTPS GET responses from exactly
`https://www.keiba.go.jp` with these case-sensitive paths:

```text
WIN       /KeibaWeb/TodayRaceInfo/OddsTanFuku
QUINELLA  /KeibaWeb/TodayRaceInfo/OddsUmLenFuku
WIDE      /KeibaWeb/TodayRaceInfo/OddsWide
TRIO      /KeibaWeb/TodayRaceInfo/Odds3LenFuku
```

Each canonical request has exactly the three query keys `k_babaCode`, `k_raceDate`, and
`k_raceNo`. The race date is a real `YYYY/MM/DD` value serialized canonically with the slashes
percent-encoded as `%2F`; venue code and race number are positive canonical ASCII decimal tokens.
No fragment, credentials, alternate host, port, extra query key, duplicated key, blank value, or
ambiguous percent encoding is allowed. Optional display/sort controls such as `odds_flg` are not
part of the canonical evidence request. Mobile/SP pages and popularity-only views are not v1
authority or fallback.

One request identity binds organization `NAR`, source system `nar_official`, page kind, bet type,
external race identity, method `GET`, and the exact canonical URL. There is no caller-supplied URL
escape hatch and no alternate URL retry.

## Raw capture identity and archive ownership

The evidence pipeline is:

```text
canonical request identity
  -> one complete HTTP response body
  -> immutable byte-preserving raw capture
  -> versioned pure parser and eligibility evidence
  -> immutable normalized market batch
  -> causal resolver
  -> manifest/snapshot/prediction adapter
  -> later exact quote/EV adapter
```

Raw bodies remain exact bytes. `response_sha256` is lowercase SHA-256 of those bytes. A capture ID
is a versioned SHA-256 identity binding the request identity, page kind/bet type, response digest,
and exact `observed_at`; it is not merely a body hash. Therefore identical bytes have the same body
identity, while a fresh later observation of identical bytes is a distinct capture. Repeating the
same complete evidence tuple is idempotent.

Odds captures belong to a new explicit, caller-owned, append-only NAR market-odds capture SQLite
archive. It follows the existing trusted archive pattern but does not modify or overload the closed
NAR official-response or daily-target archives. It has an isolated explicit migration registry;
its repository constructor never migrates, creates a hidden database, uses a global connection, or
falls back to another archive. No UPDATE, DELETE, repair, latest, or cache API is introduced.

The later normalized quote batch belongs to immutable simulation evidence persistence, not the raw
archive and not a mutable current-price row. It must retain the raw capture ID, body digest, exact
request identity, parser/schema version, and normalized content/completeness identity. Phase 31
does not freeze a main-database migration number; that is audited only when the normalized
persistence phase is prepared.

## Market quote and batch model

The later normalized public domain is one immutable race-and-bet-type batch, not an independently
trusted quote row. It binds at least:

- schema/domain version;
- organization `NAR` and source system `nar_official`;
- exact external NAR race identity and canonical internal race ID;
- bet type and canonical page/request identity;
- exact raw capture ID and `response_sha256`;
- parser name/version;
- exact captured prediction-time race-entry-universe evidence identity;
- provider-listed eligible horse numbers and mapped active race-entry IDs in canonical order;
- expected, parsed, missing, unexpected, duplicate, suspended, and unavailable selection facts;
- batch/completeness status and deterministic completeness/content identity;
- requested, observed, captured, optional provider quote-as-of, and optional proven availability
  timestamps;
- every canonical quote entry in deterministic lexical selection order.

Canonical selection identity is race-scoped internal `race_entry_id`, never horse name. WIN uses a
one-item tuple; QUINELLA and WIDE use two distinct IDs sorted ascending; TRIO uses three distinct
IDs sorted ascending. The exact captured mapping from official horse number to internal entry ID is
evidence and must be one-to-one for every selected participant.

Quote values are a typed union:

```text
EXACT: exact_odds is one finite positive Decimal; range fields are absent
RANGE: lower_odds and upper_odds are finite positive Decimals with lower <= upper; exact is absent
```

WIN, QUINELLA, and TRIO require `EXACT`. WIDE requires `RANGE` even when the displayed endpoints
happen to be equal; it is not silently coerced to exact semantics. No float, NaN, Infinity, zero,
negative value, popularity rank, textual inference, midpoint, or payout-derived value is allowed.

Provider conditions are explicit. A numeric complete batch is `QUOTED`; recognizable betting
suspension or unavailable market state is diagnostic `SUSPENDED` or `UNAVAILABLE`; malformed,
ambiguous, partial, or contradictory content fails closed. Consumers never receive a successful
subset map from an incomplete batch.

## Complete-market and eligibility invariant

The expected field is the provider-listed betting-eligible field at capture time, reconciled
exactly with a causally valid captured pre-race `RaceEntryUniverse` for the same race. It is not the
original declared field and is never rewritten from later results. Active, scratched/excluded,
cancelled, and suspended states must be supported by exact captured content. If the odds response
and entry-universe evidence cannot prove one coherent eligible set, the batch is unsupported or
invalid; the parser must not guess.

For evidenced eligible count `n`, the complete quoted selection set is exactly:

```text
WIN       n
QUINELLA  C(n, 2)
WIDE      C(n, 2)
TRIO      C(n, 3)
```

The exact canonical identities, not only counts, must equal the expected set. A missing,
unexpected, duplicate, unmapped, nonnumeric, suspended, or unavailable expected selection prevents
a `QUOTED` complete batch. A wholly recognized suspended/unavailable response may yield only its
explicit diagnostic batch state. No numeric successful subset, venue filter, first-N cap, cached
fallback, or alternate source is returned.

Late scratches are accepted only when the captured odds participant set and captured entry-state
evidence agree before the cutoff. A later result page may not retroactively change membership.
Race cancellation or betting suspension produces no exact quote map and no EV eligibility.

## Timing and causal authority

The raw acquisition clock is one explicit injected UTC clock shared by the live capture service
and archive composition. The application adds no hidden/default/current clock.

- `requested_at`: sampled immediately before sending the exact request.
- `observed_at`: sampled only after the full response body and headers have been received.
- `captured_at`: the immutable archive's durable validation/publication time (`stored_at` in the
  existing archive vocabulary), sampled after response validation and no earlier than observed.
- `available_at`: optional and present only when an official field is proven to mean publication
  availability. It is not inferred from file time, cache headers, or current wall clock.
- `provider_quote_as_of_at`: optional audit fact parsed from an unambiguous official market-as-of
  label. `HH:MM 現在` is not automatically promoted to `available_at` without a separately tested
  semantic proof. `最終` is not prediction-time evidence.

Every quote used for replay/EV must satisfy exactly:

```text
available_at <= observed_at <= captured_at <= information_cutoff < scheduled_start_at
```

when `available_at` exists, otherwise:

```text
observed_at <= captured_at <= information_cutoff < scheduled_start_at
```

The later live service additionally requires `requested_at <= observed_at`. A request that begins
before cutoff but completes or is archived after cutoff is not prediction eligible. It may remain
as immutable audit capture, but it cannot produce a successful quote resolution. There is no
backdating, nearest-future selection, final-odds substitution, or wall-clock reconstruction.

For a future T-5 run the caller supplies both `scheduled_start_at` and the exact
`information_cutoff = scheduled_start_at - five minutes`. The service must be started early enough
for full response observation and archive publication to finish by that cutoff. Scheduling itself
is outside Phase 31 and every listed implementation phase.

## Multi-request atomicity

Each approved NAR bet-type page is treated as one full-market response for that one bet type. One
normalized bet-type batch must come from exactly one raw odds capture; pages or fragments from
multiple request times are never spliced into one batch.

A four-bet-type acquisition consists of four independently timestamped immutable captures. It is
not described as an atomic simultaneous market snapshot. A downstream decision may bind all four
capture identities only after each required batch separately passes the same explicit cutoff and
race-universe checks. Failure of any required batch means no partial four-type decision input.

The separate race-entry-universe evidence is permitted only as eligibility evidence. Its exact
race identity and pre-cutoff capture identity are bound into the normalized batch, and its active
set must reconcile with the participants proven by the odds response. It does not authorize
combining odds values from multiple odds responses.

## Historical replay selection

Replay never reparses arbitrary raw HTML as a fallback once a normalized batch exists. The parser
version and raw evidence identities are immutable members of the normalized batch, and replay
loads that exact validated batch through its repository.

The frozen resolver policy is `latest-observed-before-cutoff-fail-on-tie-v1`:

1. match exact organization/source, external and internal race identity, bet type, parser/domain
   version, and required completeness/quote representation;
2. retain only batches satisfying the causal chain and scheduled-start boundary;
3. select the greatest `observed_at` not after the cutoff;
4. collapse only an exact duplicate immutable content identity;
5. if two different content identities share the greatest `observed_at`, fail closed as ambiguous.

`available_at` is a causal gate, not an implicit freshness override. Database row ID, insertion
order, current time, file timestamp, lexical content preference, date fallback, and “latest current”
are forbidden. The replay resolution and manifest must eventually bind the selected normalized
batch content SHA, raw capture ID/SHA, request identity, parser version, and exact policy.

## EV boundary and WIDE decision

The later exact market ratio may be calculated only when all of the following are exact and valid:

- Phase 30 probability/model identity;
- provider, race, bet type, and canonical selection identity;
- a causally valid, complete `QUOTED` market batch;
- one positive exact Decimal quote for that selection.

Only then:

```text
model_expected_value_ratio = model_probability * market_decimal_odds
```

WIN, QUINELLA, and TRIO can meet this representation gate after the later NAR path is implemented.
NAR WIDE remains excluded from exact market EV because the official source publishes a range. No
lower endpoint, upper endpoint, or midpoint is called exact EV. A separately named conservative or
interval metric would require a later design review proving its semantics. JRA remains fully
deferred. Accordingly `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` is design-resolved only for the
future NAR QUINELLA/TRIO capture path; it is not yet implementation-resolved and remains open for
WIDE exact EV and JRA.

## Approved phase decomposition

The work is split because raw evidence integrity, live acquisition, parser/completeness semantics,
normalized persistence/resolution, replay integration, and EV integration have independent failure
and audit boundaries:

1. **Phase 32 — NAR Market Odds Raw Capture Archive Implementation**: closed request identity,
   byte-preserving raw capture, isolated explicit archive migration, immutable exact-ID archive.
   No HTTP, HTML parser, normalized quote, cutoff resolver, or EV.
2. **Phase 33 — NAR Market Odds Live Acquisition Implementation**: one fixed GET per requested bet
   type, injected transport/clock, immediate archive, conservative request/observation/storage
   timing, no parser and no cross-type partial success.
3. **Phase 34 — NAR Market Odds Parser and Complete Quote Batch Implementation**: pure parsing,
   exact/range quote union, entry-universe reconciliation, provider status, completeness, content
   identity. No network or database writes.
4. **Phase 35 — NAR Normalized Market Odds Persistence and Causal Resolution**: immutable main-DB
   normalized batch storage, exact load, causal policy, ambiguity failure. Migration version is
   audited then, not guessed now.
5. **Phase 36 — NAR Replay Manifest/Input Quote Evidence Integration**: bind selected quote evidence
   to resolver, manifest, snapshot, and prediction input without changing model or strategy.
6. **Phase 37 or later — Exact NAR WIN/QUINELLA/TRIO EV and versioned decision integration**:
   probability/quote adapter first, then separately reviewed strategy and immutable decision audit.

WIDE range analytics and JRA prediction-time source discovery remain separate later designs.

## Exact Phase 32 public domain API

`POST_V0_8_DAILY_REPLAY_32` — `NAR Market Odds Raw Capture Archive Implementation` — is the
only next implementation proposed. The public domain API is frozen exactly as follows.

```python
class NARMarketOddsPageKind(StrEnum):
    ODDS_TAN_FUKU = "odds_tan_fuku"
    ODDS_UM_LEN_FUKU = "odds_um_len_fuku"
    ODDS_WIDE = "odds_wide"
    ODDS_3_LEN_FUKU = "odds_3_len_fuku"

@dataclass(frozen=True, slots=True)
class NARMarketOddsRaceIdentity:
    baba_code: str
    race_date: date
    race_no: int

@dataclass(frozen=True, slots=True)
class NARMarketOddsRequestIdentity:
    page_kind: NARMarketOddsPageKind
    race_identity: NARMarketOddsRaceIdentity
    schema_version: int = field(init=False, default=1)
    organization: str = field(init=False, default="NAR")
    source_system: str = field(init=False, default="keiba.go.jp")
    method: str = field(init=False, default="GET")
    official_origin: str = field(init=False, default="https://www.keiba.go.jp")
    canonical_request_url: str = field(init=False)
    request_identity_sha256: str = field(init=False)
    request_identity: str = field(init=False)

def build_nar_market_odds_request_identity(
    *,
    page_kind: NARMarketOddsPageKind,
    baba_code: str,
    race_date: date,
    race_no: int,
) -> NARMarketOddsRequestIdentity: ...

@dataclass(frozen=True, slots=True)
class NARMarketOddsResponseCapture:
    request_identity: NARMarketOddsRequestIdentity
    effective_url: str
    response_body: bytes
    charset: str
    requested_at: datetime
    observed_at: datetime
    captured_at: datetime
    http_status: int
    content_type: str | None = None
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    schema_version: int = field(init=False, default=1)
    response_sha256: str = field(init=False)
    byte_length: int = field(init=False)
    capture_id: str = field(init=False)
```

`NARMarketOddsRaceIdentity` accepts only an exact built-in `str` `baba_code` matching
`[1-9][0-9]*`, an exact `datetime.date` that is not `datetime.datetime`, and an exact built-in
positive `int` `race_no` that is not bool. It contains provider identity only; Phase 32 adds no
internal/main-database race ID and never uses a horse name.

The page/path relation is exact:

```text
ODDS_TAN_FUKU    /KeibaWeb/TodayRaceInfo/OddsTanFuku
ODDS_UM_LEN_FUKU /KeibaWeb/TodayRaceInfo/OddsUmLenFuku
ODDS_WIDE        /KeibaWeb/TodayRaceInfo/OddsWide
ODDS_3_LEN_FUKU  /KeibaWeb/TodayRaceInfo/Odds3LenFuku
```

The future normalized mapping is respectively WIN, QUINELLA, WIDE, and TRIO, but Phase 32 does not
parse that content. `OddsTanFuku` is preserved in full even though only its WIN portion is expected
to become a later normalized value.

## Canonical request and identity

The request builder alone creates the URL. Query order is exactly `k_babaCode`, `k_raceDate`, then
`k_raceNo`; date slashes are uppercase `%2F`:

```text
https://www.keiba.go.jp<PATH>?k_babaCode=<BABA>&k_raceDate=YYYY%2FMM%2FDD&k_raceNo=<RACE_NO>
```

No arbitrary input URL, reordered or extra query, alternate host, credentials, fragment, HTTP, or
port spelling is accepted as identity. The one private canonical JSON authority used by both
request and capture identities is exactly:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

The request payload is exactly:

```json
{
  "baba_code": "<canonical token>",
  "canonical_request_url": "<exact canonical URL>",
  "method": "GET",
  "official_origin": "https://www.keiba.go.jp",
  "organization": "NAR",
  "page_kind": "<enum value>",
  "race_date": "YYYY-MM-DD",
  "race_no": 1,
  "schema_version": 1,
  "source_system": "keiba.go.jp"
}
```

`race_no` is the actual integer. `request_identity_sha256` is SHA-256 of those canonical bytes and
`request_identity` is exactly:

```text
nar-market-odds-request-v1:<64 lowercase hex>
```

## Exact response capture contract

`request_identity` must be the exact public request type. `effective_url` must be an exact nonempty
built-in string that passes the same official canonical URL validation and equals
`request_identity.canonical_request_url` exactly; redirects and cross-origin responses are outside
Phase 32. The body is exact nonempty built-in `bytes`. It is decoded once only to prove strict UTF-8
support, but decoded text is never identity material and bytes are never normalized or re-encoded.

`charset` is exactly `utf-8`; `http_status` is exact int 200 and rejects bool. `content_encoding` is
only `None` or exact `identity`. Optional HTTP metadata is exact `str | None` with no control
characters. `content_length`, when present, is an exact nonnegative int, rejects bool, and equals
the exact response byte length.

Malformed types, URL/status/length contradictions, and timestamp contradictions raise validation
errors. A syntactically valid but unsupported charset, content-encoding profile, or body that is not
strict UTF-8 raises the unsupported error.

`requested_at`, `observed_at`, and `captured_at` are exact aware `datetime.datetime` values,
canonicalized to UTC and persisted with microseconds as `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`. Their
exact relation is:

```text
requested_at <= observed_at <= captured_at
```

They are supplied by the future transport/caller; the domain calls no current clock. Phase 32 owns
no `available_at`, `information_cutoff`, or `scheduled_start_at` field and does not infer
availability from HTTP Date. A capture can be valid raw evidence even when a later resolver rejects
it for a prediction cutoff. The later resolver retains the Phase 31 causal chain and
`latest-observed-before-cutoff-fail-on-tie-v1` policy.

`response_sha256 = sha256(response_body).hexdigest()` over the exact persisted bytes and
`byte_length = len(response_body)`. The capture payload binds every immutable response fact:

```json
{
  "captured_at_utc": "<microsecond UTC text>",
  "charset": "utf-8",
  "content_encoding": null,
  "content_length": null,
  "content_type": null,
  "effective_url": "<exact canonical request URL>",
  "etag": null,
  "http_date": null,
  "http_status": 200,
  "last_modified": null,
  "observed_at_utc": "<microsecond UTC text>",
  "request_identity_sha256": "<64 lowercase hex>",
  "requested_at_utc": "<microsecond UTC text>",
  "response_sha256": "<64 lowercase hex>",
  "schema_version": 1
}
```

Optional members use their exact actual string/int value instead of null. The capture digest is
SHA-256 of the same canonical JSON bytes; `capture_id` is exactly:

```text
nar-market-odds-capture-v1:<64 lowercase hex>
```

Thus the same full semantic capture is deterministic/idempotent; changed bytes, request, header, or
owned timestamp changes the capture identity. Identical bytes observed later retain the same body
SHA but receive a distinct capture ID.

## Exact domain and Protocol errors

```python
class NARMarketOddsCaptureError(Exception): ...

class NARMarketOddsCaptureValidationError(NARMarketOddsCaptureError): ...

class NARMarketOddsCaptureUnsupportedError(NARMarketOddsCaptureError): ...

class NARMarketOddsCaptureSource(Protocol):
    def load_capture(
        self,
        *,
        capture_id: str,
    ) -> NARMarketOddsResponseCapture | None: ...

class NARMarketOddsCaptureArchive(NARMarketOddsCaptureSource, Protocol):
    def save_capture(
        self,
        *,
        capture: NARMarketOddsResponseCapture,
    ) -> None: ...
```

Exact missing lookup returns `None`; there is no domain missing exception. There is no latest,
closest, date, cutoff, page search, update, delete, repair, or fallback method.

## Exact isolated migration authority

The migration module freezes:

```python
VERSION = 1
NAME = "v001_nar_market_odds_capture_archive_schema"

def apply(connection: sqlite3.Connection) -> None: ...

def get_applied_nar_market_odds_capture_archive_schema_versions(
    connection: sqlite3.Connection,
) -> dict[int, str]: ...

def get_pending_nar_market_odds_capture_archive_migrations(
    connection: sqlite3.Connection,
) -> tuple[object, ...]: ...

def apply_nar_market_odds_capture_archive_migrations(
    connection: sqlite3.Connection,
) -> None: ...

def require_nar_market_odds_capture_archive_schema(
    connection: sqlite3.Connection,
) -> None: ...
```

Every entrypoint requires exact `sqlite3.Connection`. `apply` creates only v1 domain objects and
does not begin, commit, or roll back; its caller owns that transaction. The explicit migration
runner rejects an active caller transaction, enables/verifies foreign keys, owns one atomic
`BEGIN IMMEDIATE`, and rolls back on failure. Read/schema-gate entrypoints never create or migrate
schema. Unknown future versions, name mismatches, malformed registry, and unregistered objects fail
closed. No hidden path, current clock, main simulation migration registry, seed, or backfill exists.

The exact schema object set is:

```text
nar_market_odds_capture_archive_schema_migrations
nar_market_odds_response_bodies
nar_market_odds_response_captures
ux_nar_market_odds_response_captures_evidence
```

The registry is the standard `version INTEGER PRIMARY KEY` / unique nonempty `name TEXT` table,
`WITHOUT ROWID`. The bodies table, also `WITHOUT ROWID`, has exactly
`response_sha256`, `response_body`, and `byte_length`; it enforces lowercase 64-hex identity,
nonempty BLOB, positive integer length, and `byte_length = length(response_body)`.

The capture table is `WITHOUT ROWID` with these columns in exact order:

```text
capture_id
schema_version
request_schema_version
request_identity
request_identity_sha256
page_kind
organization
source_system
request_method
request_official_origin
request_baba_code
request_race_date
request_race_no
canonical_request_url
effective_url
response_sha256
charset
requested_at_utc
observed_at_utc
captured_at_utc
http_status
content_type
content_encoding
http_date
etag
last_modified
content_length
```

It enforces both version values equal one; exact identity prefixes/lowercase SHA shape; the four
page kinds; constant organization/source/method/origin; positive canonical baba/race values; real
canonical date text and exact request/canonical/effective URL reconstruction through repository
validation; strict UTF-8/status/encoding; microsecond UTC timestamp shape and order; and optional
metadata types/length. `capture_id` is the primary key. `response_sha256` references
`nar_market_odds_response_bodies(response_sha256)` with `ON UPDATE RESTRICT ON DELETE RESTRICT`.

The only evidence index is named `ux_nar_market_odds_response_captures_evidence`, is UNIQUE, and
has this exact column order:

```text
request_identity_sha256,response_sha256,requested_at_utc,observed_at_utc,captured_at_utc
```

There is no `CURRENT_TIMESTAMP`, generated semantic time, mutable timestamp, trigger, aggregate, or
main-simulation table. The migration DDL is the single schema authority. Its public schema gate
checks the exact object set and normalized SQL plus column order/type/nullability/PK, CHECK clauses,
`WITHOUT ROWID`, unique index definition/order, FK target/actions, and `foreign_key_check`; a
lookalike schema is rejected and never repaired.

## Exact SQLite repository API and behavior

```python
class SQLiteNARMarketOddsCaptureArchive:
    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
    ) -> None: ...

    def save_capture(
        self,
        *,
        capture: NARMarketOddsResponseCapture,
    ) -> None: ...

    def load_capture(
        self,
        *,
        capture_id: str,
    ) -> NARMarketOddsResponseCapture | None: ...
```

Construction requires exact `sqlite3.Connection`, rejects an active transaction, enables/verifies
foreign keys, and requires the already-applied exact v1 schema. It does not migrate, repair, open,
or close a connection. Caller owns connection lifetime.

The repository reuses exactly `RepositoryValidationError`, `RepositoryConflictError`, and
`RepositoryDataIntegrityError` from `scripts.simulation.repositories.errors`. Invalid caller or
lookup values use validation; the same immutable identity with different valid supplied content
uses conflict; malformed/corrupt/incompatible stored data or SQLite integrity failures use data
integrity.

Save requires exact capture type and no active caller transaction, owns one atomic
`BEGIN IMMEDIATE`, and commits or rolls back its own work. Same capture ID and exact reconstructed
capture is an idempotent success. Any semantic difference is a conflict. Bodies are deduplicated by
response SHA; multiple capture rows may reference one body. Same supplied SHA with different valid
bytes is a conflict, while a corrupt preexisting body or missing referenced body is data-integrity
failure and is never repaired. Publication is INSERT-only: no `INSERT OR REPLACE`, `REPLACE`,
UPDATE, DELETE, refresh, or overwrite.

Load validates canonical capture-ID syntax, reads one exact capture and one exact body, validates
BLOB type/length/SHA, reconstructs race/request/capture domain values, recomputes both identities,
compares every stored scalar to the reconstructed tuple, and verifies evidence-index coherence.
Any mismatch raises data integrity; only an absent exact key returns `None`. The repository exposes
no latest, closest, date, cutoff, fuzzy URL, mutable, or resolver API.

## Phase 32 raw-only boundaries

Phase 32 performs no HTTP request. A future transport supplies the exact request identity, effective
URL, raw bytes, response metadata, and timestamps. The three approved production files contain no
`requests`, `urllib.request`, aiohttp, browser, global session, hidden clock, random, UUID, JRA,
Phase 30 probability, ValueEngine, BetGenerator, strategy, settlement, payout, main migration
runner, or replay dependency.

Phase 32 does not parse horse numbers, selections, odds, popularity, completeness, suspension, or
WIDE bounds; imports no Decimal odds model; computes no model probability or EV; and leaves
`COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` open. The later normalized WIDE representation remains
a lower/upper range with no exact EV policy. JRA, causal resolver, replay manifest, BUY/SKIP, and T-5
scheduler remain deferred.

## Exact Phase 32 Allowed Files

Phase 32 may change exactly these eight files:

```text
scripts/simulation/nar_market_odds_capture.py
scripts/simulation/nar_market_odds_capture_archive_migration.py
scripts/simulation/sqlite_nar_market_odds_capture_archive.py
tests/test_nar_market_odds_capture.py
tests/test_nar_market_odds_capture_archive_migration.py
tests/test_sqlite_nar_market_odds_capture_archive.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No ninth file is permitted. Existing NAR/JRA capture production, global migrations, prediction,
settlement, payout, database/**, and logs/** remain read-only.

## Frozen Phase 32 test contract

Phase 32 tests must cover at least:

- all four exact enum members/values, endpoint paths, query order, uppercase `%2F`, future wager
  association without parsing, and deterministic request identity;
- identity changes for page/baba/date/race; malformed/leading-zero baba, datetime-as-date, bool or
  nonpositive race number, arbitrary/wrong-origin/effective URL rejection;
- deterministic capture ID; exact Japanese UTF-8 and CRLF/LF byte preservation; exact body SHA and
  length; one-byte/header/requested/observed/captured changes alter the required identity;
- exact bytes/type, strict UTF-8, HTTP 200, charset/encoding, metadata/control, content-length, aware
  datetime, UTC canonicalization, and owned timestamp-order validation; no ambient clock;
- migration `VERSION`/`NAME`, empty apply, applied/pending queries, repeat idempotence, unknown future
  version, malformed registry, unexpected object, malformed body/capture/index/FK/CHECK/SQL,
  foreign-key integrity, and repository no-auto-migration;
- exact connection and transaction gates; atomic save/load round trip; byte-for-byte body reload;
  idempotent duplicate; immutable conflict; shared body hash; missing exact ID; invalid ID; corrupt
  body/SHA/length/metadata/FK/evidence tuple; rollback; clean transaction; caller connection remains
  open; no repair;
- absence of latest/fallback/update/delete/replace APIs and static absence of network/current-clock,
  random/UUID, JRA, main migration runner, market parser, normalized odds/Decimal, EV, probability,
  strategy, settlement, and payout dependencies;
- existing NAR official-response and daily-target archive/migration regressions, Phase 30,
  Phase 25/27/28, relevant migration regressions, full unittest discovery, focused compilation,
  ResourceWarning-as-error where practical, static boundary searches, and database/log Git gates.

Cutoff crossing/no-partial transport behavior remains Phase 33; canonical pair/triple parsing,
Decimal odds validation, expected combination counts, scratches, suspension, and complete/no-partial
normalized maps remain Phase 34; cutoff selection and manifest identity remain Phases 35–36.

## Stop condition

Phase 32 stops at `READY_FOR_REVIEW`. The implementation and tests remain unstaged for independent
review. No stage, commit, push, Phase 33 preparation, normalized market parsing, EV integration,
resolver, scheduling, or JRA work is authorized. Blockers are none.

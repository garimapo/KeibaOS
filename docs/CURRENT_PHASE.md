# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1 — Historical input source policy and snapshot construction preparation

## Base Commit

`038130c9d84a082107e351e545c167a9019e7b3a feat: load historical input snapshots from sqlite`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective and Frozen Boundaries

Prepare the smallest fail-closed V3c boundary that converts already-observed official historical source records
into one committed V3a `HistoricalInputSnapshot`. This phase does not implement a provider, raw store, builder,
migration, or repository change. The nine V3a domain values and protocols, the V3b SQLite schema, and the V3d
SQLite repository save/load behavior are frozen.

## Current Source Trust Classification

| Current material | Classification | V3c use |
| --- | --- | --- |
| `races.id`, `horses.id`, `horses.race_id`, `horses.horse_no` | linkage-only | May bind a separately trusted external record to exact internal IDs. Never evidence. |
| Legacy race descriptive values and `deba_table_url` | linkage-only | May locate a supplied official URL after validation; never supplies snapshot/provenance facts. |
| Legacy jockey/weight/popularity/horse URL | untrusted | No immutable official record identity or causal observation time. |
| `horses.odds` | forbidden | Never an official historical odds source. |
| Legacy `past_races` / `get_past_races()` | forbidden | Parsed data has no official identity, raw payload, or source-time proof; row ID ordering is forbidden. |
| v008 odds batches | untrusted | Not automatically official historical-source provenance. |
| results, payouts, settlements | forbidden | Post-race evidence never enters a prediction-time snapshot. |
| Current NAR response supplied to a future capture boundary with immutable official URL and timestamp | conditionally trusted | Only after source-record validation and causal policy pass. Current code does not retain it. |
| Current JRA material | unavailable | `JRAFetcher` is a static placeholder, not an official adapter. |

`NARProvider` fetches live HTML and writes log files named with Python `hash(url)`; neither raw payload nor
timestamp is a persisted canonical record. `NARParser` retains a `k_raceDate`-derived date and `HorseParser`
retains a numeric horse number, but they drop `k_babaCode`, `k_raceNo`, canonical raw identity, and timing.
`PastRaceFetcher` / `PastRaceParser` save legacy rows only. Thus no existing persisted database row or log file is
trusted source material for retrospective V3c construction.

## Constructibility Matrix

| Family | track | entry | jockey | odds_win | past_race | past_race_absence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `nar_official` / `NAR` | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | UNSUPPORTED | Live parser inputs can expose page values but lack retained immutable raw records, complete official keys, and causal timestamps. No scoped absence search exists. |
| `jra_official` / `JRA` | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | No real official JRA provider/parser, URL/identity, or capture boundary exists. |

JRA is **UNSUPPORTED / DEFERRED**. No JRA external identity format is invented here.

## NAR External Identity

Future supplied official NAR records construct only:

```text
nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}
nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:entry:{horseNum}
```

`YYYYMMDD` is a real calendar date parsed from `k_raceDate`, then rendered without separators. `k_babaCode` and
`k_raceNo` are non-empty ASCII decimal official query tokens, with no whitespace or colon; their official source
spelling is preserved, with no guessed integer conversion or zero-padding. `horseNum` is a positive official
horse-number token rendered in canonical base-10 without zero-padding only after parsing the official numeric
field. Missing, repeated, ambiguous, or non-decimal source keys fail source validation. Place names and displayed
race numbers are never substitutes. Legacy DB rows alone are insufficient because they do not preserve the two
official race keys and are linkage-only.

## Canonical Source Record and Digest Policy

### Exact common source-record envelope

This section supersedes every earlier abbreviated c1 description of source payloads, provenance linkage, or
digest input. The c1a source domain accepts exactly these six `record_kind` values:

```text
track
entry
jockey
odds_win
past_race
past_race_absence
```

The public record field is named `schema_version`, not `version`: its exact Python type is `int`, its value is
exactly `1`, and it is required in the digest envelope. `his-v1` is the source-ID family prefix, not a second
record field. Every c1a source record has the following exact fields. All `str` values are NFC-normalized; values
are never trimmed or case-folded. A required text field rejects the empty string after normalization.

| Field | Python type / nullability | Exact normalization and semantic source | In source-ID digest |
| --- | --- | --- | --- |
| `schema_version` | exact `int`, required, value `1` (`bool` rejected) | Fixed schema discriminator supplied by c1a. | yes |
| `record_kind` | `Literal["track", "entry", "jockey", "odds_win", "past_race", "past_race_absence"]`, required | Exact lower-ASCII member; identifies the matching `record_values` schema below. | yes |
| `organization` | `str`, required | Non-empty NFC official organization label, e.g. `NAR`; supplied by the future source normalizer. | yes |
| `source_system` | `str`, required | Non-empty NFC source-family label, e.g. `nar_official`; supplied by the future source normalizer. | yes |
| `external_race_id` | `str`, required | Non-empty NFC official **target** race identity. For NAR it is exactly `nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}` under the already-approved NAR rule. | yes |
| `external_entry_id` | `str | None` | NFC non-empty official target-entry identity when the kind is entry-scoped; JSON `null` only for `track`. NAR is exactly `{external_race_id}:entry:{horseNum}`. | yes |
| `canonical_source_url` | `str | None` | Already-canonical official primary response/record URL supplied by c1b/c1d, or `null` only where the record-kind URL policy below permits it. c1a validates it but does not canonicalize it. There is no separate `source_url` or `response_url` alias. | yes |
| `provider_record_id` | `str | None` | NFC non-empty opaque official provider record identity when supplied. It is never a local row ID, path, inferred URL fragment, or generated value. | yes |
| `available_at` | `datetime | None` | Official provider publication/availability time only; an aware instant normalized to UTC with exactly six fractional digits when rendered. Receipt time, mtime, insertion time, race start, and page date are forbidden substitutes. | no |
| `observed_at` | `datetime`, required | Immutable capture-boundary timestamp recorded immediately after successful official response-byte receipt and before parsing; aware and normalized to UTC with exactly six fractional digits when rendered. | no |
| `record_values` | immutable `Mapping[str, object]`, required | Defensively frozen exact per-kind mapping below. It contains no internal SQLite identifier and no unspecified key. | yes, as the final envelope member |

`race_id` and `race_entry_id` are deliberately absent from c1a source records and from their digest. They are
local V3a assembly/linkage values allocated after source normalization. The future builder receives a separate
official-entry-to-local-entry mapping; the same official record must therefore retain the same source ID even if
it is later linked to a different SQLite row. `entry_order` and `past_race_index` are likewise derived builder
values and are not source content.

### Exact per-kind `record_values` schemas

All mapping keys listed below are mandatory and are the complete key set for that kind. A JSON date is the
canonical `YYYY-MM-DD` string. A JSON datetime is the canonical aware UTC `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`
string. A JSON Decimal is NFC-independent canonical `format(value.normalize(), "f")` text with zero rendered
as `"0"`; input must be `Decimal`, finite, and never `float`. Exact `int` excludes `bool`.

| Kind | Exact `record_values` keys and validated source-domain types |
| --- | --- |
| `track` | `target_race_date: date`; `scheduled_start_at: datetime` (aware); `place: str`; `distance_m: int` (> 0); `track: str`; `track_condition: str`; `race_name: str | None`; `race_class: str | None`; `weather: str | None`. The three nullable historical metadata fields render as explicit JSON `null`; all other text is non-empty NFC. |
| `entry` | `external_entry_id: str` (must equal the common envelope field); `external_horse_id: str | None` (explicit `null` is permitted; current NAR horse-detail URL is not a stable provider horse ID); `horse_no: int` (> 0). `entry_order` is not a key: the future builder derives it from the complete official `horse_no` set in ascending order. `race_entry_id` is not a key. |
| `jockey` | `external_entry_id: str` (must equal the common envelope field); `jockey: str` (non-empty NFC). No external jockey identity is added because the committed V3 contract does not require one. |
| `odds_win` | `external_entry_id: str` (must equal the common envelope field); `horse_no: int` (> 0); `win_odds: Decimal` (finite and strictly > 0, serialized as canonical Decimal text). Zero is invalid, so zero normalization does not make an odds value valid. |
| `past_race` | `race_date: date`; `place: str`; `race_name: str`; `race_class: str`; `distance_m: int` (> 0); `track: str`; `weather: str`; `track_condition: str`; `finish: int` (> 0); `margin: Decimal` (finite, signed permitted); `race_time: str`; `weight: Decimal` (finite and >= 0); `weight_diff: Decimal` (finite, signed permitted); `jockey: str`; `popularity: int` (>= 0); `odds: Decimal` (finite and >= 0); `passing_order: str` (NFC; the empty string is valid and remains `""`); `fourth_corner_position: int` (>= 0). Every text field except `passing_order` is non-empty. The common `external_entry_id` is the target official entry. The common `provider_record_id` is required and non-empty for this kind and is the opaque official past-race record identity; no local row ID is used. |
| `past_race_absence` | `external_entry_id: str` (must equal the common envelope field); `query_scope: Mapping[str, object]` with exactly `external_entry_id: str` (equal to the common field), `target_race_date: date`, and `strictly_before_target_race: bool` (exactly `True`); `result_count: int` (exactly `0`, with `bool` rejected). The common `canonical_source_url` is the successful official search response URL. It is one complete official zero-result search proof, never parser emptiness and never an open-ended endpoint parameter bag. |

### Exact canonical-source-URL ownership and validation

c1b/c1d source normalizers own provider-family URL normalization. They canonicalize a provider URL under that
source family's separately approved policy and supply the resulting `canonical_source_url`. c1a never sorts or
drops query parameters, infers a default port, changes percent encoding, removes a trailing slash, adds/removes
`www`, lowercases a path or query, resolves a relative URL, strips tracking parameters, or otherwise transforms a
URL. Host-case canonical spelling is also c1b/c1d responsibility; c1a retains the supplied host spelling exactly.

When non-null, `canonical_source_url` must be an exact `str`, non-empty, already NFC-normalized, and have neither
leading nor trailing whitespace. c1a rejects (rather than trims) a value needing NFC or whitespace normalization.
It parses only to validate that it is an absolute URL with scheme exactly `https`, a non-empty host, no username,
no password, no fragment, and no control character. It performs no further canonicalization and puts the validated
string byte-for-byte into the digest envelope.

| Record kind | `canonical_source_url` policy | Evidence rule |
| --- | --- | --- |
| `track` | OPTIONAL | A future normalizer may establish this record by official provider record ID without one primary URL. |
| `entry` | OPTIONAL | A future normalizer may establish this record by official provider record ID without one primary URL. |
| `jockey` | OPTIONAL | A future normalizer may establish this record by official provider record ID without one primary URL. |
| `odds_win` | OPTIONAL | A future normalizer may establish this record by official provider record ID without one primary URL. |
| `past_race` | OPTIONAL | Its non-null `provider_record_id` remains the required official past-race identity; c1a never synthesizes a URL from it. |
| `past_race_absence` | REQUIRED | The non-null URL is the auditable anchor for one successful complete official zero-result search scope. |

`canonical_source_url` and `provider_record_id` are independent evidence/identity fields. c1a never derives,
synthesizes, or cross-fills either value from the other. `past_race` retains its non-null `provider_record_id`
requirement. `past_race_absence` does not require `provider_record_id`; its required complete scoped response URL
is the proof anchor.

For `past_race`, the future set validator uses
`(source_system, external_race_id, external_entry_id, provider_record_id)` as the official conflict primitive.
Two records with that primitive and different canonical payloads are a conflict; two identical canonical payloads
have the same source ID and are a duplicate. For every kind, same-source duplicate identity is exact `source_id`.
Neither check uses a database row ID.

### Exact digest envelope and serialization

For every kind, source ID is the SHA-256 of the UTF-8 bytes of exactly this object; no time, local ID, extra key,
or absent nullable key is permitted:

```json
{
  "schema_version": 1,
  "source_system": "<NFC non-empty str>",
  "record_kind": "<one of the six exact kinds>",
  "organization": "<NFC non-empty str>",
  "external_race_id": "<NFC non-empty str>",
  "external_entry_id": "<NFC non-empty str or null>",
  "canonical_source_url": "<validated upstream HTTPS str or null by kind policy>",
  "provider_record_id": "<NFC non-empty str or null>",
  "record_values": { "<the complete exact kind-specific key set above>" }
}
```

`available_at` and `observed_at` are immutable source-record evidence fields but are intentionally excluded from
the source-ID digest: the ID identifies normalized official record content, not the collector/capture event.
They remain mandatory downstream causal evidence. The JSON projection converts dates, datetimes, and Decimals as
specified above, validates but never changes `canonical_source_url`, NFC-normalizes every other allowed string,
uses explicit `null`, then calls exactly
`json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")`.
SHA-256 is computed over those encoded bytes; only its 64-character hexadecimal result is lowercase. The complete
ID is exactly `his-v1:{record_kind}:{lowercase_sha256_hex}`. `repr()`, mapping insertion order, HTML order,
raw response bytes, local IDs, file paths, filenames, timestamps, UUIDs, and Python `hash()` are forbidden.

## Record-to-Provenance Mapping

| Record kind | Provenance input type | Audit key |
| --- | --- | --- |
| `track` | `track` | `track` |
| `entry` | `entry` | `entry/{race_entry_id}` |
| `jockey` | `jockey` | `jockey/{race_entry_id}` |
| `odds_win` | `odds` | `odds/{race_entry_id}` |
| `past_race` | `past_race` | `past_race/{race_entry_id}/{past_race_index}` |
| `past_race_absence` | `past_race` | `past_race/{race_entry_id}/none` |

`odds_win` and `past_race_absence` are record kinds, never new provenance input types. `source` is the source
system and `source_id` is the deterministic record ID; timestamps copy exactly from the source record.

## Past-Race, Absence, and Temporal Policy

Eligible `past_race` records require a `race_date` strictly before the track record's `target_race_date`. The
future builder orders valid records exactly by `(race_date DESC, source_id ASC)`, then assigns
`past_race_index = 0, 1, ...`; equal dates use source ID and no database row ID. Missing, same-day, future,
malformed, duplicate-source, or same-official-identity/different-payload records fail closed.

An entry may receive the provenance audit key `past_race/{race_entry_id}/none` only from exactly one
`past_race_absence` record having the complete `query_scope` fixed above, `strictly_before_target_race is True`,
and `result_count == 0` as an exact non-`bool` integer. The source record's common `external_race_id`,
`external_entry_id`, `canonical_source_url`, `available_at`, and `observed_at` give the official response scope
and temporal evidence. A parser returning an empty list is never absence proof.

`available_at` is `datetime | None`: when present, it is only an official source-provided publication time.
`observed_at` is required and is only the immutable capture-boundary receipt instant defined above. Both must be
aware; if `available_at` is present it must be `<= observed_at`. Downstream construction additionally requires
`available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at`, omitting only the
first comparison when `available_at is None`. Thus a record with no official `available_at` but a valid immutable
`observed_at` is usable for a prospective capture whose observed/captured time meets the downstream cutoff; it is
not retrospectively manufactured from legacy data. Existing NAR data records no such capture-boundary observation,
so NAR remains partial until c1b supplies it. HTTP receipt substituted after the fact, database insertion,
filesystem mtime, race start, page date, derived/result/post-race time, and settlement data are forbidden.

## Exact c1a Public API and Error Boundary

The proposed module is exactly `scripts/simulation/historical_input_source_records.py`. Its public names are:

```python
SourceRecordKind = Literal[
    "track", "entry", "jockey", "odds_win", "past_race", "past_race_absence"
]

class HistoricalInputSourceError(ValueError): ...
class HistoricalInputSourceValidationError(HistoricalInputSourceError): ...
class HistoricalInputSourceConflictError(HistoricalInputSourceError): ...

@dataclass(frozen=True, slots=True)
class HistoricalInputSourceRecord:
    schema_version: int = field(default=1, init=False)
    record_kind: SourceRecordKind
    organization: str
    source_system: str
    external_race_id: str
    external_entry_id: str | None
    canonical_source_url: str | None
    provider_record_id: str | None
    record_values: Mapping[str, object]
    available_at: datetime | None
    observed_at: datetime
    source_id: str = field(init=False)

def canonical_historical_input_source_payload(
    *, record: HistoricalInputSourceRecord
) -> dict[str, object]: ...

def build_historical_input_source_id(
    *, record: HistoricalInputSourceRecord
) -> str: ...

def validate_historical_input_source_record_set(
    *, records: Sequence[HistoricalInputSourceRecord]
) -> tuple[HistoricalInputSourceRecord, ...]: ...
```

`HistoricalInputSourceRecord` validates and defensively freezes the exact schema, yielding
`HistoricalInputSourceValidationError` for type, kind, URL, identity, scalar, nullability, and temporal-order
violations. The payload/ID functions are pure and raise that same validation error only for an invalid record.
The set validator returns the caller order unchanged when valid; duplicate source IDs and same-past-race conflict
primitive with a different payload raise `HistoricalInputSourceConflictError`. The base error exists solely for
callers that need one source-domain boundary. JRA unsupported behavior belongs to c1d/JRA normalization, not c1a;
c1a performs no network, parser, DB, or filesystem work. There is no package-root export.

## Future Builder Boundary

```text
already-observed official source records
-> policy normalization / validation
-> immutable canonical source bundle
-> build_historical_input_snapshot(...)
-> HistoricalInputSnapshot
-> SQLiteHistoricalInputSnapshotRepository.save_snapshot(...)
```

The pure builder receives records plus exact dataset/internal-race/cutoff/captured facts and returns one V3a
snapshot or fails closed. It never fetches, opens/writes a DB, reads results, guesses provenance, repairs records,
or calls repository save/load.

The later c1c builder will translate only its own caller/assembly failures from these validated source records;
it does not alter c1a exception identity. Repository exceptions are not used by c1a.

## Recommended Split and Candidate Future Files

1. **4C-2d3b1i6c1a — Source-record domain and deterministic IDs:** likely new
   `scripts/simulation/historical_input_source_records.py` and
   `tests/test_historical_input_source_records.py`.
2. **4C-2d3b1i6c1b — NAR supplied-raw normalization:** likely new
   `scripts/simulation/nar_historical_input_source.py` and a dedicated test. Existing provider/parser changes are
   not pre-authorized.
3. **4C-2d3b1i6c1c — Pure snapshot builder:** likely new
   `scripts/simulation/historical_input_snapshot_builder.py` and dedicated test; repository round trip is focused
   integration only.
4. **4C-2d3b1i6c1d — JRA normalization:** deferred pending a real official JRA adapter and identity contract.

## Exact Future c1a Allowed Files and Test Matrix

The exact future c1a implementation scope is only:

```text
scripts/simulation/historical_input_source_records.py
tests/test_historical_input_source_records.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

It does not authorize c1b NAR normalization, c1c snapshot builder, JRA work, provider/parser edits, database,
migration, package-root exports, or repository work. Deterministic, no-network c1a tests must cover: exact public
API; frozen/slotted fields and annotations/defaults; the exact six kinds and unknown-kind rejection; exact payload
key sets for every kind; retained JSON nulls; NFC; canonical UTC microseconds; canonical dates and Decimal text;
float rejection; bool-versus-int rejection; deterministic IDs; ID independence from local row IDs; identical
construction producing the same ID; one canonical-content change producing a different ID; external identity
validation; positive odds; `passing_order == ""`; duplicate and official-conflict primitives; the exact absence
`query_scope`; exact zero result count; malformed absence rejection; temporal ordering; no DB/network/filesystem
access; and no package-root export. URL tests additionally cover non-`str`, empty, non-NFC, `http`, relative,
missing-host, credential-bearing, fragment-bearing, and control-character URLs; a valid HTTPS URL is retained
byte-for-byte without query/path/host transformation; `past_race_absence` rejects `None`; and every per-kind
required/optional URL policy is enforced. NAR-key and JRA-normalizer behavior are c1b/c1d tests, not c1a behavior.

## Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files

Production, tests, migrations/schema, provider/parser/fetch code, README, package exports, database/logs, the
original workspace, and all Git writes are forbidden during preparation.

## Required Future Verification

Every approved implementation subphase must run deterministic dedicated tests, relevant V3a/V3b/V3d regressions,
the full suite, source-boundary searches, `git diff --check`, and an allowed-files status check.

## Explicit Gap / Blocker

No persisted official raw corpus currently has immutable source identity plus causal availability evidence. This
blocks trusted retrospective construction today but not the source-record-domain phase with supplied deterministic
records. JRA remains unsupported/deferred.

## Stop Condition

This documentation-only phase remains `DRAFT_FOR_REVIEW` awaiting ChatGPT design review. Do not implement, stage,
commit, push, or begin a recommended subphase without a separate explicit instruction.

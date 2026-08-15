# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d4b1` — JRA final-odds capture domain and dedicated archive v002 implementation.

Formal base: `906628c5eb5f1639387b3625d494cf133bb27729`.

Approved PREPARE: `acf0a28d84f6ce7961175cb807ec602f868fef56`.

Review branch: `review/4c-2d3b1i6d1d4b1-final-odds-capture-implementation`.

## Implemented Contract

`JRAOfficialFinalWinOddsRequestLocator` is a frozen/slotted provider-owned POST locator with exactly
`endpoint_url`, `cname`, `external_race_identity`, and `request_identity_sha256`. It accepts only the literal
accessO endpoint `https://www.jra.go.jp/JRADB/accessO.html` and a raw, canonical CNAME matching:

```text
pw151ou10<VV><YYYY><MM><DD><RR><YYYYMMDD>Z/<HH>
```

The locator derives and cross-checks the existing `JRAExternalRaceIdentity`; it never synthesizes CNAME from race
identity. Percent/plus encoding, whitespace, controls, invalid dates, noncanonical fields, lower-case opaque tail,
and caller-supplied contradictory fingerprints are rejected. The fingerprint is SHA-256 over exact UTF-8 canonical
ASCII JSON with sorted keys and compact separators:

```json
{"endpoint_url":"https://www.jra.go.jp/JRADB/accessO.html","form":{"cname":"<raw canonical cname>"},"method":"POST","schema_version":1}
```

`JRAOfficialPageKind.FINAL_WIN_ODDS` is the sole new page kind. Existing accessS/accessU GET URL canonicalization
and their public APIs remain unchanged; FINAL_WIN_ODDS cannot be passed through the GET URL canonicalizer.

`JRAFinalWinOddsSuppliedOfficialResponse` and `JRAFinalWinOddsResponseCapture` are separate frozen/slotted POST
values. They retain exact strict-CP932 raw bytes and aware timestamps without a text round trip. The v2 capture uses
`schema_version=2`, `page_kind=final_win_odds`, `request_method=POST`, the validated locator, and deterministic
`jra-capture-v2:<sha256>` identity over the approved endpoint/request fingerprint/body SHA/observed-at preimage.
All `JRAOfficialResponseCapture` v1 GET constructors and `jra-capture-v1` IDs remain literal-compatible.

## Dedicated JRA Archive v002

Dedicated migration v002 is exactly `v002_jra_official_response_capture_request_identity_schema`. It is
transaction-neutral: the existing migration runner alone owns `BEGIN IMMEDIATE`, commit, rollback, and registry
registration. The runner sequence is exactly `(1, 2)`; global migrations remain `(8, 9, 10, 11, 12, 13, 14)`.

v002 proves the complete registered v001 trust boundary before any mutation: both table column/type/PK/NOT-NULL and
`WITHOUT ROWID` shapes, the exact response-body foreign key, and the unique non-partial three-column evidence index
are verified with SQLite PRAGMAs. Rollback-only SAVEPOINT probes then prove actual v001 body and capture CHECK/FK
behavior, including malformed body identity/length, page family, charset, HTTP, content encoding/length, URL, and
timestamp-order rejection. Existing rows continue to reconstruct through the legacy capture domain. Any weakened or
corrupt v001 shape fails before `ALTER TABLE`; the runner rollback leaves its tables, index, data, and version-1
registry entry intact. v002 then rebuilds only `jra_official_response_captures`; `jra_official_response_bodies` is never rebuilt. All v001 values are copied exactly
with `GET`, NULL request fingerprint, and NULL CNAME. The replacement table has disjoint enforced families:

```text
v001: race_result|horse_profile_history / GET / NULL fingerprint / NULL CNAME
v002: final_win_odds / POST / lowercase SHA-256 fingerprint / raw canonical CNAME
```

It maintains separate partial exact-evidence indexes for legacy URL/body/observed identity and request-aware
endpoint/request-fingerprint/body/observed identity. A malformed v001 schema, row, digest/body relationship, or
unregistered store fails closed; any rebuild failure rolls back through the runner with no repair, adoption, update,
delete, pruning, or fallback.

`JRAOfficialResponseCaptureArchive` is one six-method family-specific protocol. The existing three legacy methods
remain source- and type-compatible and operate only on v001 GET values. The new separate methods are
`save_final_win_odds_capture`, `load_final_win_odds_capture`, and
`load_final_win_odds_supplied_response_for_evidence`. Final lookup requires exact endpoint, request fingerprint,
raw SHA, and observed-at; it has no URL-only POST, latest, nearest, or fallback mode. Legacy load of a v2 capture ID
and final load of a v1 capture ID return `None`; an existing contradictory stored row raises
`RepositoryDataIntegrityError`.

## Frozen Boundaries

```text
EXISTING_ACCESS_S_CAPTURE_IDS_PRESERVED = PASS
EXISTING_ACCESS_U_CAPTURE_IDS_PRESERVED = PASS
LEGACY_ARCHIVE_API_PRESERVED = PASS
LEGACY_GET_EVIDENCE_LOOKUP = PASS
GLOBAL_MIGRATION_FINAL_VERSION = 14
NAR_CAPTURE_UNCHANGED = PASS
NEUTRAL_REQUEST_EVIDENCE_UNCHANGED = PASS
LIVE_CAPTURE_PRODUCTION_UNCHANGED = PASS
```

Live POST transport, real accessO capture, JRA historical odds/result normalization, acquisition, NAR/JRA bridge,
pagination, pacing, historical backdating, and package-root exports remain out of scope.

## Allowed Files

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/jra_official_response_capture_migration_v002.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_identity.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent implementation review. Do not integrate formal or begin d1d4b2 live POST transport.

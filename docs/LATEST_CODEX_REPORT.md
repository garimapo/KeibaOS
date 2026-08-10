# Latest Codex Report

## Status

PHASE_4C_2D3B1I6C1D3B2B_PREPARE

## Formal Context

Phase 4C-2d3b1i6c1d3b2a is formally complete at
`4af5a7ba4f18769f365ac2c934bcfd0ffcf38818` on `feature/ver0.8-simulator`.

This docs-only preparation is on `review/4c-2d3b1i6c1d3b2b-prepare`, created directly from that formal commit.
No production code, test, fixture, migration, database, log, or original-workspace file was changed.

## Preparation Result

The proposed next work is intentionally split in two. d3b2b1 owns an append-only, content-addressed SQLite archive
in the existing KeibaOS database: exact response BLOBs are deduplicated by SHA-256 and immutable capture observations
are uniquely recoverable by existing evidence `(canonical_source_url, response_sha256, observed_at)`. It introduces
additive `v013_nar_official_response_capture_schema` and reconstructs the existing
`NarSuppliedOfficialResponse` without a fetch, text re-encoding, or synthesized timestamp.

d3b2b2 then owns the dedicated NAR HTTPS acquisition service. It does not reuse the legacy `NARProvider`, whose
`response.text`, apparent-encoding, and logs path cannot preserve trusted parser bytes. The service will validate the
closed NAR URL vocabulary before network use, take `requested_at` before request start and `observed_at` only after
the complete raw parser-input entity bytes arrive, archive before normalizing, use HTTPS certificate verification,
disable redirects and retries, and accept HTTP 200/strict UTF-8 only. A real aware UTC clock is production-owned;
tests inject a deterministic clock. HTTP Date remains metadata, never observed or available time.

The operational trust claim is deliberately limited. KeibaOS can audit its own local capture history, but a local
clock and SQLite do not provide cryptographic third-party timestamp proof. Current NAR pages, provider logs, fixture
timestamps, race dates, file/Git/database times, or third-party archives cannot be backdated into valid historical
evidence. Before trusted collection begins, live-site-only historical replay is expected no-data. Capture should begin
as soon as the primitive is implemented so future replay coverage grows.

## Official Investigation

Read-only direct official requests on 2026-08-10 found these representative direct `www.keiba.go.jp` endpoints return
HTTP 200 without redirect, `Content-Type: text/html; charset=UTF-8`, no Content-Encoding, and approximate body sizes:

- DebaTable, Funabashi 2026-07-04 11R: 297,718 bytes.
- HorseMarkInfo lineage `30074407776`: 83,949 bytes.
- RaceMarkTable, Kochi 2026-05-03 1R: 96,614 bytes.

`www2.keiba.go.jp` HorseMarkInfo returned HTTP 301 to `www.keiba.go.jp`. The capture contract therefore preserves
the existing supplied-response host vocabulary but fails closed for this live redirect while redirects are disabled;
it performs no silent host rewrite.

## Future Migration Scope

v013 changes the migration registry and requires exact expectation updates in these existing tests:

```text
tests/test_historical_input_snapshot_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_simulation_migrations.py
tests/test_sqlite_persisted_simulation_application.py
```

No historical snapshot table is changed. Existing v008-v012 records continue to load; older evidence lacking an
archived body returns the explicit missing-capture result rather than a fabricated body.

## Status and Blockers

`CURRENT_PHASE_STATUS = DRAFT_FOR_REVIEW`.

No implementation has started. The preparation is ready for independent architecture review. Intentional limitations
remain: no external timestamp authority, no trusted retroactive live-page backfill, no production capture during
PREPARE, no pagination/acquisition orchestration, and no `past_race_absence` support.

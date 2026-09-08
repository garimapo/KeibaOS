# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_23`
- Name: `NAR Daily Target Live Acquisition Application Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `ecb962dcfd6639b9c44c64376db4d611222bcc58`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `IMPLEMENTABLE`
- Production/tests implementation during PREPARE: `NOT_AUTHORIZED`
- Stage/commit/push: `NOT_AUTHORIZED`

AGENTS.md and the committed Phase 2-22 contracts are authority. This phase is only the
thin live acquisition/composition application which closes an exact `target_date` into
one audited NAR `DailyHistoricalReplayTargetSet`. It does not change any existing domain,
parser, transport, archive, normalizer or target-set contract.

## Existing implementation audit and reuse

The required flow is implementable without changing an existing production file:

- Phase 22 `NARMonthlyConveneInfoBootstrapLiveCaptureService` owns fresh homepage,
  Monthly-root and pinned-script acquisition and archives each exact supplier capture.
- Phase 22 staged resolvers own the homepage/root/script relations and exact source-owned
  Monthly request material. The Phase 18 final resolver and bootstrap evidence value
  remain the final Monthly identity authority.
- Phase 6 `NARHistoricalDailyTargetLiveCaptureService` captures and archives one already
  validated Monthly or RaceList request identity. It owns the closed daily-target HTTP
  boundary and requires no change.
- `normalize_nar_monthly_convene_info` returns an immutable envelope whose
  `venue_locators` tuple is already deterministic and retains each exact raw-href-derived
  `request_identity`.
- `build_nar_historical_daily_replay_target_set` already revalidates the Monthly envelope,
  requires exact envelope/RaceList coverage and navigation equality, normalizes every
  RaceList fragment, and delegates provider-neutral set construction/digest authority.
- The Phase 20 `SQLiteNARDailyTargetEvidenceArchive` structurally satisfies both required
  save APIs. Migration remains explicit caller/setup responsibility.

No missing production capability or contract conflict requires scope expansion.

## Public API

The new `scripts/simulation/nar_daily_target_live_acquisition.py` exposes exactly two
public values.

```python
@dataclass(frozen=True, slots=True)
class NARDailyTargetLiveAcquisitionResult:
    target_date: date
    homepage_supplier_capture_id: str
    monthly_root_supplier_capture_id: str
    locator_script_supplier_capture_id: str
    supplier_evidence_identity: str
    monthly_capture_id: str
    race_list_capture_ids: tuple[str, ...]
    target_set: DailyHistoricalReplayTargetSet


class NARDailyTargetLiveAcquisitionApplication:
    def __init__(
        self,
        *,
        archive: _NARDailyTargetLiveAcquisitionArchive,
        supplier_transport: NARMonthlyConveneInfoBootstrapHTTPTransport,
        daily_target_transport: NARHistoricalDailyTargetHTTPTransport,
        utc_clock: Callable[[], datetime],
    ) -> None: ...

    def acquire(
        self,
        *,
        target_date: date,
    ) -> NARDailyTargetLiveAcquisitionResult: ...
```

The result has no independent acquisition timestamp, persistence identity, session,
transport, connection or database state. It stores only exact audit IDs plus the exact
builder-returned target set. Its frozen/slots constructor requires an exact `date`, exact
non-empty string IDs, a tuple of non-empty unique RaceList capture IDs in acquisition
order, an exact `DailyHistoricalReplayTargetSet`, and exact target-date agreement. It
does not compute another target-set digest or infer completeness.

A private `_NARDailyTargetLiveAcquisitionArchive(Protocol)` declares only the existing
`save_supplier_capture(...)` and `save_capture(...)` methods needed by the two services.
It adds no public repository API. The constructor stores one archive and internally
constructs exactly one supplier service and one daily-target service with that same
archive and the same injected clock. It does not call migration, SQL, load APIs or the
clock directly.

Invalid non-exact `target_date` raises the existing
`NARHistoricalDailyTargetSourceValidationError` before any capture. All other existing
bootstrap, transport, capture, source, target-set and repository errors propagate without
generic wrapping. No Phase 23-specific error type is needed.

## Exact acquisition sequence

`acquire` performs only this order:

```text
require type(target_date) is date
-> supplier_service.capture_official_home()
-> resolve_nar_monthly_convene_info_root_locator(homepage_capture=...)
-> supplier_service.capture_monthly_root(homepage_capture=..., root_locator=...)
-> resolve_nar_monthly_convene_info_locator_script(
       target_date=..., root_locator=..., monthly_root_capture=...)
-> supplier_service.capture_locator_script(
       monthly_root_capture=..., locator_script_resolution=...)
-> NARMonthlyConveneInfoBootstrapEvidence(exact three supplier captures)
-> resolve_nar_monthly_convene_info_request_identity(
       target_date=..., supplier_evidence=...)
-> daily_service.capture_supplied_response(exact Monthly request identity)
-> normalize_nar_monthly_convene_info(target_date=..., capture=Monthly capture)
-> for every envelope.venue_locators item in exact tuple order:
       daily_service.capture_supplied_response(
           request_identity=locator.request_identity)
-> build_nar_historical_daily_replay_target_set(
       target_date=...,
       envelope_capture=Monthly capture,
       race_list_captures=exact ordered tuple)
-> construct and return NARDailyTargetLiveAcquisitionResult
```

Every RaceList locator is consumed. There is no count limit, first-N behavior, venue
filter, skip, reorder, reconstructed request identity or catch-and-continue path. In
particular five or more discovered locators remain five or more acquisitions. The exact
existing `locator.request_identity` object is passed unchanged to the Phase 6 service.

The existing builder is called exactly once and only after all required capture calls
have returned successfully. The returned target set is stored by object identity in the
result. The application does not parse HTML/JavaScript, inspect raw hrefs, create URLs,
normalize fragments, compare navigation sets or calculate any digest.

## No-partial and fresh-live semantics

Any exception before final result construction means no
`NARDailyTargetLiveAcquisitionResult` and no partial target set is returned. This applies
to supplier acquisition, staged relation, archive save, pinned-script, final bootstrap,
Monthly acquisition/normalization, every RaceList acquisition/archive save, builder and
repository integrity/conflict failures. Existing exceptions and causes are preserved.

Captures saved by an existing service before a later failure remain honest immutable
Phase 20 audit records. Their presence never constitutes a successful day, never causes
the builder to run early and never permits a partial return.

Every `acquire` invocation is a fresh live chain. The application exposes no capture-ID,
offline or resume input, calls no `load_*`, and has no cache/network fallback. A repeated
date performs the supplier, Monthly and every RaceList request again. It adds no retry;
the two existing transport policies remain authority.

## Clock, archive and causal boundary

The application passes the same caller-supplied `utc_clock` object to both existing live
services. It never invokes that clock itself and contains no current-clock API or
application timestamp synthesis. Service timestamps remain honest acquisition audit
metadata and are never mapped to prediction, snapshot, availability, scheduled-start or
settlement fields.

The caller supplies one already-migrated Phase 20 archive. The application neither
migrates nor checks schema independently, owns no database path/connection/transaction,
and performs no SQL, repair, latest lookup or cache load. Existing service save-before-
return behavior guarantees each network response is archived before it becomes an
application-stage success.

## Allowed Files

Only these exact files may change in a later approved execution:

```text
scripts/simulation/nar_daily_target_live_acquisition.py
tests/test_nar_daily_target_live_acquisition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The production and test files are new. Every existing file is read-only.

## Forbidden Files and non-goals

Do not change Phase 22/20/18/6 production or tests, shared daily-target domains,
fixtures, `.gitattributes`, repositories/errors, migrations/schemas, main or settlement
databases/archives, CLI, JRA, evidence resolver, manifest, replay, result persistence,
reporting, strategy or metrics. Never modify/stage `database/keiba.db` or `logs/`.

This phase stops at `target_date -> DailyHistoricalReplayTargetSet`. It does not call
Phase 14 resolution, Phase 16 manifest projection, replay runner, prediction pipeline or
settlement logic and does not implement the later Daily Orchestrator.

## Required Tests

A later approved execution must implement all of these behavior groups in
`tests/test_nar_daily_target_live_acquisition.py`:

1. constructor accepts one explicit archive, supplier transport, daily transport and clock;
2. constructor composes both existing services with the same archive and clock;
3. constructor/acquire never migrates and constructor performs no capture;
4. exact `date` is required before any side effect;
5. homepage is the first acquisition;
6. root locator is produced only by Stage A;
7. root capture receives the exact homepage capture and Stage A locator;
8. script resolution is produced only by Stage B with exact target date/root chain;
9. script capture receives the exact root capture and Stage B resolution;
10. exact three captures construct existing bootstrap evidence;
11. final Monthly identity comes from the existing Phase 18 final resolver;
12. Monthly capture uses the existing Phase 6 service and exact identity unchanged;
13. Monthly capture is archived before normalization or later acquisition;
14. existing Monthly normalizer is called once and its envelope is used unchanged;
15. every envelope venue locator is iterated;
16. exact `locator.request_identity` object is passed unchanged;
17. envelope tuple order is preserved in RaceList capture order;
18. every RaceList capture is archived before the next stage;
19. five discovered locators are all captured without a cap;
20. existing builder is called once only after every RaceList succeeds;
21. builder receives exact Monthly capture and exact ordered RaceList tuple;
22. result retains the exact builder target-set object and ordered audit capture IDs;
23. result is frozen/slotted and validates exact field/type/date invariants;
24. supplier failure returns no result;
25. root/staged parser failure returns no result;
26. script/pin failure returns no result;
27. Monthly transport/archive failure returns no result;
28. Monthly normalization failure returns no result and no builder call;
29. first, middle and final RaceList failures each return no result;
30. RaceList archive failure returns no result;
31. builder failure returns no result or target set;
32. earlier successful archived captures remain after a later failure but imply no success;
33. no partial target set/result or catch-and-continue exists;
34. no archive lookup/cache fallback exists;
35. repeated acquisition performs a fresh complete request chain;
36. application introduces no retry or arbitrary URL/request reconstruction;
37. no HTML/JavaScript/parser/normalizer/completeness/digest duplication exists;
38. no SQL, migration or direct current-clock call exists;
39. no prediction, evidence resolver, settlement, manifest or replay call exists;
40. Phase 22 staged/bootstrap and supplier-live regressions pass;
41. Phase 20 migration/archive regressions pass;
42. Phase 6 capture/live/source regressions pass;
43. deterministic target-set semantics hold with the reviewed existing fixtures;
44. database paths and settlement archive remain untouched.

Tests use injected fake transports and clocks and temporary/in-memory explicitly migrated
Phase 20 archives. They perform no real network. Failure tests must not be skipped or
relaxed.

Execution must run:

```text
python -W error::ResourceWarning -m unittest tests.test_nar_daily_target_live_acquisition
python -m unittest tests.test_nar_historical_daily_target_bootstrap tests.test_nar_historical_daily_target_bootstrap_live_capture tests.test_nar_historical_daily_target_bootstrap_capture
python -m unittest tests.test_nar_daily_target_evidence_archive_migration tests.test_sqlite_nar_daily_target_evidence_archive
python -m unittest tests.test_nar_historical_daily_target_capture tests.test_nar_historical_daily_target_live_capture tests.test_nar_historical_daily_target_source
python -m unittest discover -s tests -p "test_*.py"
```

New dedicated ResourceWarnings are failures. Existing unrelated full-suite warnings must
be reported separately.

Static inspection must prove the new application has no direct `requests`, `httpx`,
`urllib`, `sqlite3`, SQL, `HTMLParser`, provider URL regex/literal, browser, eval/exec,
`datetime.now`, `datetime.utcnow`, `time.time`, migration invocation, archive load,
retry, replay runner, prediction, settlement or manifest boundary. Git comparison must
prove all Phase 22/20/18/6 production files remain unchanged.

## Stop Condition

During PREPARE stop at `DRAFT_FOR_REVIEW`, with only the two docs changed and cached state
empty. No implementation, test change, stage, commit, push or Phase 24 work is authorized.

During a later approved execution, stop without guessing if an existing API cannot be
composed exactly; the exact request identity/order would change; parser, URL, normalizer,
coverage or digest logic would need duplication; an existing production file or fifth
file must change; partial result semantics would be required; or any dedicated, related,
full-suite, static or Git scope check fails.

Successful execution requires all 44 groups and regressions to pass, only the four
Allowed Files to change, `git diff --check` to pass, cached state to remain empty, no
database/log change, docs to record exact results, and Status to become
`READY_FOR_REVIEW`. Stage, commit and push remain separately gated.

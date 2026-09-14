# Current Phase

## Phase

POST_V0_8_DAILY_REPLAY_50

## Name / type / state

NAR Reacquisition Observability Support and Phase44 GET-Boundary Instrumentation

- Type: IMPLEMENTATION
- Status: INTEGRATED_PENDING_REMOTE_VERIFICATION
- Outcome: IMPLEMENTED_NO_NETWORK_OBSERVABILITY_SUPPORT
- Branch: feature/post-v0.8-daily-replay
- Base: 8b5e6a04a42f8259f06f089f1cf932a1efbbd0e5

Design review: PHASE50_DESIGN_REVIEW_PASS

Integration review: PASS_FOR_INTEGRATION

Next permitted action: REMOTE_VERIFICATION_REQUIRED

Phase50 is implemented within its exact six-path manifest. It performs no HTTP, live Phase44 acquisition, fixture work, staging, commit, or push.

## Preserved state

Phase48 is final:

~~~text
SOURCE_PROFILE_FIXTURE_BLOCKED
PHASE48_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED
PHASE48_REACQUISITION_NOT_AUTHORIZED
LIVE_FAILURE_ROOT_CAUSE_UNRESOLVED
~~~

Its first attempt made zero requests and did not enter Phase44. The reauthorized attempt passed compile/preflight and started a live child, but the parent discarded return code/stdout/stderr after collapsing nonzero exit and/or stderr. Phase44 entry, GET count, closed bundle, safety, Profiles A/B, and transient publication remain UNKNOWN. No formal source evidence persisted.

Phase41 remains DESIGN_BLOCKED. Dependencies remain OPEN:

~~~text
COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE
NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE
~~~

No Phase50 work changes target 21 / 2025-01-01 / 6, Phase44 sole authority, at-most-two requests, no retry/fallback/discovery, raw-byte authority, safety, Profiles A/B, fixture contract, manifest identities, or rollback. Listing plus no withdrawal never implies MARKET_ELIGIBLE. WHOLE_MEETING_CANCELLATION and positive_market_eligibility remain UNSUPPORTED.

## Inspected Phase44 and selected option

Inspected scripts/simulation/nar_race_entry_status_raw_capture.py:

| Location | Current fact |
| --- | --- |
| 620-625 | injected transport protocol fetch(*, request_identity) |
| 632-770 | concrete requests transport owns a fresh session per document |
| 644-648 | session/retry/header/TLS/timeout setup |
| 648-655 | exact existing session.get call site |
| 808-837 | transport result validation and capture construction |
| 840-883 | public Deba -> RaceList -> closed bundle acquisition |
| 886-903 | frozen public __all__ surface |

Also inspected tests/test_nar_race_entry_status_raw_capture.py: public-surface, concrete request option/raw-byte, error/clock-count, and two-fetch-order tests.

Option A is selected. Phase50 implementation will add a private context-local observer scope inside Phase44. It is not exported in __all__; public function signatures, transport protocol, concrete constructor, public types, exception hierarchy, and identity payloads do not change. The default unbound observer is a no-op and has no I/O. The exact private integration names are `_RawCaptureObservationEvent`, `_RawCaptureObservationObserver`, `_raw_capture_observer_scope(observer)`, and `_emit_raw_capture_observation(event)`. The private event value contains only `kind`, `page_kind`, `request_identity`, `response_sha256`, `response_byte_length`, and `bundle_id`, with irrelevant fields set to None. The support module alone binds the scope for controlled execution.

Private dispatches occur at acquisition-function entry; immediately before transport.fetch; immediately before existing session.get; immediately after that call returns; after complete raw response construction; and immediately before bundle return.

~~~text
ACQUISITION_FUNCTION_ENTERED
TRANSPORT_FETCH_ABOUT_TO_START
HTTP_GET_ATTEMPT_ABOUT_TO_START
HTTP_RESPONSE_RETURNED
RAW_RESPONSE_CONSTRUCTED
CLOSED_BUNDLE_CONSTRUCTED
~~~

HTTP_GET_ATTEMPT_ABOUT_TO_START means the immediate next Phase44 instruction is existing requests.Session.get. It proves a program-side pre-call boundary, not wire-level send/provider receipt. A crash after it leaves wire state UNKNOWN.

Events carry only page role, request identity, and when already available response SHA-256/byte length or bundle ID. They never carry raw body, headers, cookies, authentication/session/token/user values, exception repr, or observer timestamp. Journal time is external operational metadata and never calls the Phase44 clock.

Observer failure is fail closed. A failure before session.get prevents that call. Any observer failure after durable PHASE44_CALL_ABOUT_TO_ENTER maps to existing NARRaceEntryStatusRawCaptureTransportError, without retry. No-observer behavior retains exact URL, headers, retries, redirects, TLS, timeout, session ownership, raw bytes, response profile, exception taxonomy, ordering, six clock calls, and all identities.

A private hook is narrower than a public argument; an external decorator alone cannot reach the exact session.get boundary. No public API change is proposed.

## Support journal contract

Proposed support module:

~~~text
scripts/simulation/nar_race_entry_status_reacquisition_observability.py
~~~

It owns no HTTP client, parser, fixture, database, or repository persistence. It owns only a worktree-external OS-temp operational journal.

Every UTF-8 JSON Lines record is canonical JSON plus exactly one LF byte:

~~~json
{"journal_schema":"nar-race-entry-status-reacquisition-observability-journal","schema_version":1,"run_id":"32-lowercase-hex","sequence":1,"milestone":"PARENT_EXECUTION_PREPARED","occurred_at":"YYYY-MM-DDTHH:MM:SS.ffffffZ","details":{}}
~~~

Canonical bytes are exactly:

~~~python
json.dumps(payload, ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")
~~~

All seven top-level keys are required. Operational identity is (run_id, sequence); it is not a deterministic fixture identity. Parent can report SHA-256 of exact validated JSONL as an operational checksum only. PID, temp path, random run ID, and event time never enter fixture/manifest identity.

Sequence is a positive exact int, starts at one, and increments by one. Times are real aware UTC with six digits and Z. Details is an allowlist-only object. Strings are single-line UTF-8 <=512 bytes; a record <=4096 bytes; a journal <=131072 bytes; bool is never an int; URLs are not retained.

Forbidden anywhere: raw bodies/HTML, cookies/Set-Cookie, Authorization/proxy credentials, authentication/session/CSRF/token data, account/user/personalization data, arbitrary header/environment data, raw exception repr, and uncontrolled stdout/stderr. Unknown event/key, invalid UTF-8/type, malformed/noncanonical JSON, newline/control injection, oversized value, duplicate/decreasing/skipped sequence, or truncated final record invalidates the journal fail-closed.

Journal creation is exclusive and binary. Each append writes, flushes, and os.fsyncs before the named boundary. Serialization, write, flush, fsync, validation, or callback failure is never ignored. Parent validates before cleanup; child never deletes the journal.

## Milestone semantics

| Milestone | Timing | Allowed details |
| --- | --- | --- |
| PARENT_EXECUTION_PREPARED | parent, after journal creation before child launch | run_id |
| LIVE_PROCESS_START | child, after start | pid |
| TARGET_CONSTRUCTED | after target construction | baba_code, race_date, race_no |
| PHASE44_CALL_ABOUT_TO_ENTER | before function call; fsync required | target fields |
| PHASE44_FUNCTION_ENTERED | after private entry dispatch | none |
| DEBA_TRANSPORT_FETCH_ENTERED / RACELIST_TRANSPORT_FETCH_ENTERED | before corresponding transport call | request_identity |
| DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START / RACELIST_HTTP_GET_ATTEMPT_ABOUT_TO_START | immediately before existing session.get | request_identity |
| DEBA_HTTP_RESPONSE_RETURNED / RACELIST_HTTP_RESPONSE_RETURNED | after session.get returns | request_identity |
| DEBA_RAW_RESPONSE_CONSTRUCTED / RACELIST_RAW_RESPONSE_CONSTRUCTED | after complete raw response object | request_identity, response_sha256, response_byte_length |
| CLOSED_BUNDLE_RETURNED | after Phase44 returns bundle | bundle_id |
| IDENTITY_VERIFICATION_PASS | after independent check | bundle_id |
| SAFETY_PASS / PROFILE_A_QUALIFIED / PROFILE_B_QUALIFIED | after gate passes | none |
| PUBLICATION_BEGIN | before repository mutation | planned_path_count |
| RAW_FIXTURES_WRITTEN | after both reread/verified | document_count |
| MANIFEST_WRITTEN | after write/readback | fixture_set_identity, qualification_identity |
| DEDICATED_TEST_WRITTEN | after write/readback | test_path |
| REGRESSIONS_PASS | after frozen command set | command_count |
| ROLLBACK_BEGIN / ROLLBACK_COMPLETE | before / after rollback | none |
| LIVE_PROCESS_COMPLETE | after child outcome fixed | outcome, authorization_state |
| PARENT_EVIDENCE_VALIDATION_PASS | parent after validation | journal_sha256 |
| PARENT_CLEANUP_COMPLETE | after child artifacts gone, before journal deletion | none |

Each event is once-only; Deba and RaceList names are distinct. Missing later events never prove a side effect did not occur.

## Accounting, output, and failure protocol

| Durable state | Authorization report |
| --- | --- |
| failure before PHASE44_CALL_ABOUT_TO_ENTER | UNCONSUMED |
| durable about-to-enter only | CONSUMED_FAIL_CLOSED; later state UNKNOWN |
| PHASE44_FUNCTION_ENTERED | CONSUMED_CONFIRMED |
| GET-about-to-start | CONSUMED_CONFIRMED; wire state UNKNOWN |
| valid terminal protocol | CONSUMED_CONFIRMED |

The parent always retains return code plus safe stdout/stderr metadata regardless of exit, stderr, journal validity, or crash. Each stream is capped at 16384 bytes; retained fields are presence, byte length, SHA-256, and safe classification. Invalid UTF-8 is INVALID_UTF8 without retained bytes. Arbitrary text is UNCONTROLLED_OUTPUT_REDACTED. A controlled stdout report is retained only if it is exactly:

~~~text
PHASE50_FINAL_REPORT:<canonical-json>
~~~

The JSON has exactly schema_version, outcome, authorization_state, last_sequence, and last_milestone. Text with body/HTML/header/token/session/authentication indicators is REDACTED_UNSAFE_OUTPUT. Nonempty stderr alone is not semantic failure.

Parent retains output, validates journal/report and sequence/allowlists, derives only recorded facts, appends PARENT_EVIDENCE_VALIDATION_PASS, then cleans artifacts. Success requires zero exit, valid journal/report, LIVE_PROCESS_COMPLETE, and cleanup success.

## Future source/preflight and cleanup

Future executor source remains line-built and compiled before temp file, child launch, preflight, or HTTP:

~~~python
generated_source = "\n".join(EXECUTOR_SOURCE_LINES) + "\n"
compile(generated_source, "<nar_reacquisition_observability_executor.py>", "exec")
~~~

Child delivery remains code-only UTF-8 source outside worktree, direct CPython 3.14.5 with -B and PYTHONDONTWRITEBYTECODE=1, stdin=subprocess.DEVNULL, shell=False, and no input, handshake, shell source interpolation, eval, external exec, or base64 transport.

Reserved future no-network token:

~~~text
NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS
~~~

Only a future approved preflight emits it after synthetic proof of child launch, journal create/append/flush/fsync/readback, parent capture/reconstruction, failure-boundary observability, cleanup, no .pyc/__pycache__, zero HTTP, and zero repository mutation.

Cleanup follows parent validation. It verifies/removes run source, journal, __pycache__, every .pyc under the exact run directory, and empty run directory. Residue blocks success. The historic Phase48 pyc is untouched.

## Phase50 implementation manifest and tests

Allowed later implementation paths exactly:

~~~text
scripts/simulation/nar_race_entry_status_reacquisition_observability.py
scripts/simulation/nar_race_entry_status_raw_capture.py
tests/test_nar_race_entry_status_reacquisition_observability.py
tests/test_nar_race_entry_status_raw_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
~~~

No fixture, parser, reconciliation, database, dependency, manifest, or .gitattributes path is allowed.

Tests must be synthetic and no-network: success; zero/nonzero exit with/without stderr; failure before/after journal and at every milestone; simulated function/transport/GET/response/bundle/publication boundaries; missing/malformed/noncanonical/truncated/invalid-UTF-8 journal; unknown event; unsafe/oversized key/value; duplicate/decreasing/skipped sequence; write/flush/fsync/observer failure; parent validation; cleanup success/failure; no cache/pyc; deterministic safe reporting; and no-observer Phase44 compatibility.

Executed verification commands:

~~~text
python -m pytest -q tests/test_nar_race_entry_status_reacquisition_observability.py
python -W error::ResourceWarning -m pytest -q tests/test_nar_race_entry_status_reacquisition_observability.py
python -m pytest -q tests/test_nar_race_entry_status_raw_capture.py
python -m compileall -q scripts/simulation/nar_race_entry_status_reacquisition_observability.py tests/test_nar_race_entry_status_reacquisition_observability.py
git diff --check
~~~

## Approved implementation constraints

Option A is approved. Implementation may add only the already-designed minimal private, context-local Phase44 observer hook. It must remain outside `__all__`, and the existing public Phase44 API and public symbol surface must remain unchanged.

The dependency direction is frozen: the minimal private binding/emission primitive belongs in `nar_race_entry_status_raw_capture.py`; `nar_race_entry_status_reacquisition_observability.py` may bind and consume it. The foundational raw-capture module must not import, depend on, or otherwise point upward to the higher-level observability/orchestration layer. No circular import or additional abstraction module is authorized without a later approved design correction.

Observer binding must be context-local and token-reset in `finally`. It must not leak across acquisitions, threads, tasks, tests, or later calls. A callback failure must not leave a binding active. A global mutable callback slot is prohibited.

`HTTP_GET_ATTEMPT_ABOUT_TO_START` means the Phase44 source-level execution point immediately before invoking the existing `requests.Session.get()` operation. It is not proof that bytes reached the network, a TCP/TLS exchange began, or the provider received or processed the request. A crash after this marker leaves wire/provider state UNKNOWN.

With an observer bound, every BEFORE event is emitted before its boundary. If emission, journal serialization, write, flush, or fsync fails, execution fails closed and Phase44 must not intentionally invoke the corresponding boundary operation. In particular, failure of the immediate pre-GET event prevents `Session.get()`; no observer error may be silent or trigger an automatic retry.

With no observer bound, Phase44 behavior remains equivalent to the current implementation: request/capture/bundle identities, raw bytes, SHA-256, length, URL, headers, timeout, redirects, retry behavior, ordering, session lifecycle, semantic clock-call count, and error behavior do not change. The existing injected Phase44 clock must not be consumed for observer timestamping; operational timestamps remain outside capture-time semantics.

The approved journal remains worktree-external OS-temp UTF-8 canonical JSONL, one LF-terminated allowlisted safe record at a time, append-only with flush and `os.fsync()` after every boundary record, and parent validation before cleanup. It excludes bodies, headers, cookies, credentials, session or token material, account/user identifiers, arbitrary environment data, and uncontrolled exception/stdout/stderr payloads.

`PHASE44_CALL_ABOUT_TO_ENTER` must be written, flushed, and fsynced before Phase44 invocation. Before that durable record, acquisition authorization is UNCONSUMED; once it exists, later controlled-run accounting is CONSUMED_FAIL_CLOSED. Missing later records never prove a later external effect did not occur, and no automatic reacquisition retry follows an incomplete journal.

The parent must retain child return code, sanitized stdout, sanitized stderr, journal syntactic validity, journal semantic validity, reconstructed milestones, authorization state, and semantic outcome as separate dimensions. Nonempty stderr alone is not failure; return code zero alone is not success.

The reserved token `NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS` remains unavailable until a future approved synthetic no-network preflight proves the complete lifecycle. Phase50 approval does not emit it or authorize HTTP, Phase44 entry, fixture publication, Phase51 preparation/execution, or a retry of Phase48.

The eventual Phase50 EXECUTE must first report focused synthetic tests, then the relevant NAR regression suite, and run the full repository suite only once implementation is otherwise ready for review. Required coverage includes context binding/reset, observer-exception cleanup, no-observer compatibility, exact pre-GET boundary, observer failure preventing GET invocation, journal durability and malformed/unsafe-record cases, child return/stdout/stderr combinations, parent reconstruction, cleanup, no `.pyc`/`__pycache__`, and existing Phase44 regressions. No real HTTP is permitted in those tests.

## Implementation result

The private observer uses `ContextVar` token binding with unconditional reset in `finally`. Phase44 emits only the six approved private events and remains the foundational dependency. The support module imports and binds the private hook; Phase44 does not import the support module. Its formal `__all__`, public function signatures, request/capture/bundle identities, semantic clock usage, request behavior, error hierarchy, and no-observer results remain unchanged.

The immediate pre-GET event is emitted immediately before the existing `requests.Session.get()` expression. Tests prove that callback or durable journal failure at this event prevents `Session.get()` from being invoked. They do not interpret this event as wire transmission, TCP/TLS activity, or provider receipt.

The support module implements the approved external canonical JSONL writer and validator, exact milestone/detail allowlists, sequence and semantic validation, durable write/flush/fsync behavior, Phase44 bridge, authorization reconstruction, sanitized child stdout/stderr/return-code evidence, generated-source compile gate, and preflight result gate. It contains no HTTP client, database, parser, fixture writer, raw-body/header journal field, live acquisition, or Phase51 orchestration.

Verification evidence:

~~~text
focused Phase50 + Phase44: 160 passed
Phase50 dedicated: 65 passed
Phase50 dedicated, ResourceWarning as error: 65 passed
Phase44 raw-capture regression: 95 passed
relevant NAR regression (32 paths): 592 passed, 584 subtests passed
full repository: 3,666 passed, 2,841 subtests passed
static compile: PASS
no-observer public-surface/identity/clock regressions: PASS
pre-GET observer/journal failure prevents Session.get(): PASS
context binding restoration after normal and exceptional exits: PASS
synthetic child leaves no .pyc/__pycache__: PASS
HTTP performed: no
live Phase44 acquisition entered: no
~~~

The only matching repository bytecode artifacts predate Phase50 (2026-09-12); no artifact for the new support module or test was created. Phase50 neither deletes nor modifies those pre-existing ignored cache files.

## Git gate and stop

The changed/untracked set is exactly the approved six paths. Branch, local HEAD, and remote remain feature/post-v0.8-daily-replay / 8b5e6a04a42f8259f06f089f1cf932a1efbbd0e5 / same SHA. Index/cached is empty; database/logs, .gitattributes, fixture paths, manifest, dependencies, and Phase51 remain unchanged/absent. HTTP and live Phase44 acquisition entry are zero.

Stop at INTEGRATED_PENDING_REMOTE_VERIFICATION. Do not mark FORMALLY_COMPLETE, start Phase51, perform HTTP, or make further repository changes before independent remote verification.

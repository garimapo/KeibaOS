# Latest Codex Report

## POST_V0_8_DAILY_REPLAY_50 — NAR Reacquisition Observability Support and Phase44 GET-Boundary Instrumentation

Status: INTEGRATED_PENDING_REMOTE_VERIFICATION

Outcome: IMPLEMENTED_NO_NETWORK_OBSERVABILITY_SUPPORT

Design review: PHASE50_DESIGN_REVIEW_PASS

Integration review: PASS_FOR_INTEGRATION

Next permitted action: REMOTE_VERIFICATION_REQUIRED

Base: 8b5e6a04a42f8259f06f089f1cf932a1efbbd0e5

Branch: feature/post-v0.8-daily-replay

### Design decision

Option A is selected. A private, context-local Phase44 observer will dispatch safe events at function entry, transport-fetch boundary, immediate pre-session.get boundary, response return, raw-response construction, and closed-bundle construction. It is not exported in __all__; no public signature change is proposed. Unbound behavior is no-op and preserves Phase44 request, raw-byte, identity, clock, and lifecycle contracts.

HTTP_GET_ATTEMPT_ABOUT_TO_START means only that the immediate next instruction is existing requests.Session.get. It is a truthful program-side boundary, not proof of wire-level send. Observer failure before that line prevents the request; later failure is fail-closed without retry.

The support module will provide an OS-temp external UTF-8 canonical JSONL journal with strict sequence/key/value allowlists, append/flush/fsync durability, sanitized return-code/stdout/stderr retention, parent reconstruction, and verified cleanup. It owns no HTTP client or repository evidence persistence.

PHASE44_CALL_ABOUT_TO_ENTER is fsynced before function invocation; its durable presence consumes authorization fail-closed. PHASE44_FUNCTION_ENTERED confirms entry. Return status, stderr presence, journal validity, and semantic outcome remain separate report dimensions.

Reserved future no-network preflight token:

~~~text
NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS
~~~

It is not emitted in PREPARE. Future tests are synthetic/no-network and cover exit/stderr variants, every milestone failure, journal corruption/canonicality/UTF-8/sequence/key/value/size cases, observer/durability/parent-validation/cleanup failures, no cache/pyc, deterministic safe reporting, and no-observer compatibility.

### Implemented paths

~~~text
scripts/simulation/nar_race_entry_status_reacquisition_observability.py
scripts/simulation/nar_race_entry_status_raw_capture.py
tests/test_nar_race_entry_status_reacquisition_observability.py
tests/test_nar_race_entry_status_raw_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
~~~

No fixture, parser, reconciliation, database, dependency, manifest, or .gitattributes change is part of Phase50.

Phase48 remains consumed fail-closed and non-retryable. Phase41 remains DESIGN_BLOCKED. Dependencies remain OPEN:

~~~text
COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE
NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE
~~~

### Approval constraints

Option A is approved. The eventual implementation may add only the prepared private, context-local Phase44 observer. It remains outside `__all__`; all existing public Phase44 symbols and public APIs remain unchanged.

Dependency direction is frozen: private binding/emission lives in `nar_race_entry_status_raw_capture.py`; the higher-level `nar_race_entry_status_reacquisition_observability.py` binds and uses it. No upward dependency from raw capture, circular import, global mutable callback slot, or additional abstraction module is authorized.

Context-local binding must use token-based restoration in `finally`; observer failure cannot leak a binding. `HTTP_GET_ATTEMPT_ABOUT_TO_START` is only the source-level point immediately before the existing `requests.Session.get()` call. It is not proof of network-wire, TCP/TLS, or provider receipt/processing; a crash after it leaves wire/provider state UNKNOWN.

Bound observer failure is fail closed: a failed BEFORE event, including journal serialization/write/flush/fsync failure, prevents the corresponding boundary operation; immediate pre-GET failure prevents `Session.get()` and never retries. With no observer bound, Phase44 behavior is equivalent to current behavior, including identities, bytes, request behavior, lifecycle, error behavior, and semantic clock-call count. Observer timestamps do not consume the Phase44 clock.

The approved journal remains external OS-temp canonical UTF-8 JSONL with one LF-terminated allowlisted safe record per line, append/flush/fsync durability, and parent validation before cleanup. `PHASE44_CALL_ABOUT_TO_ENTER` is durable before invocation: before it authorization is UNCONSUMED; after it authorization is CONSUMED_FAIL_CLOSED. Return code, sanitized stdout/stderr, journal syntactic and semantic validity, reconstructed milestones, authorization state, and outcome remain separate dimensions.

`NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS` remains reserved for a future approved synthetic no-network preflight. Phase50 does not authorize HTTP, enter a live Phase44 acquisition, prepare Phase51, retry Phase48, publish fixtures, stage, commit, or push.

### Implementation and verification

Phase44 now has the approved private `ContextVar` observer with token reset in `finally`. Events cover acquisition-function entry, transport-fetch entry, the source-level point immediately before `requests.Session.get()`, response return, raw-response construction, and closed-bundle construction. The support layer binds the private hook; Phase44 has no upward dependency and its public `__all__` and signatures remain unchanged.

Bound callback or durable journal failure is fail closed. Tests prove immediate pre-GET failure prevents `Session.get()` and observer binding is restored after normal completion and exceptions. The marker remains a program-side pre-call fact only, never evidence of wire activity or provider receipt. Existing no-observer identities, raw bytes, clock counts, request behavior, session lifecycle, and errors remain covered by the Phase44 regression.

The new support module implements worktree-external canonical UTF-8 JSONL records, exact LF termination, milestone/detail allowlists, sequence and semantic validation, write/flush/fsync durability, authorization reconstruction, safe process-stream classification, separate return-code/stdout/stderr dimensions, mandatory generated-source compile validation, and the synthetic preflight result gate. It journals no bodies, arbitrary headers, credentials, session/token/user data, environment data, or uncontrolled output.

Verification results:

~~~text
focused Phase50 + Phase44: 160 passed
Phase50 dedicated: 65 passed
Phase50 dedicated, ResourceWarning as error: 65 passed
Phase44 raw-capture: 95 passed
relevant NAR regression (32 paths): 592 passed, 584 subtests passed
full repository: 3,666 passed, 2,841 subtests passed
static compile: PASS
synthetic child .pyc/__pycache__ residue: none
HTTP performed: no
live Phase44 acquisition entered: no
~~~

Only older matching ignored bytecode artifacts dated 2026-09-12 exist in the repository. Phase50 generated no support-module/test bytecode and did not alter those pre-existing files.

The integration commit is restricted to the approved six paths. Phase50 is not FORMALLY_COMPLETE: independent remote verification is required before any later phase. Phase41, Phase48 historical state, fixtures, dependencies, and Phase51 remain unchanged. No HTTP or live Phase44 acquisition occurred.

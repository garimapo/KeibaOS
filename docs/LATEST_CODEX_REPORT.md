# Latest Codex Report

## Phase71 implementation report

Phase: `POST_V0_8_DAILY_REPLAY_71`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Support Repair: `PHASE50_PROFILE_A_V3_TARGET_CONTRACT_REPAIRED`

Starting tracking HEAD: `4c18597eac7ec8b180650c89acddbe88f0294047`

Previous executable support HEAD: `79d6faaa30a54840232c0b73cd0e4ce1451a088e`

Phase50 now preserves the historical schema-2 targetless blocked Profile-A payload contract while requiring the real canonical `target` object for schema 3. Schema 3 accepts no missing or extra target keys and validates canonical `baba_code`, exact valid `YYYY-MM-DD` `race_date`, and an exact positive `race_no` bounded to `1..12`, without coercion or normalization.

Phase50 journal semantics additionally require a schema-3 blocked Profile-A target to equal the journal's `TARGET_CONSTRUCTED` record exactly. Mismatch in baba code, race date, or race number fails closed. Unsupported versions remain rejected. The top-level journal schema, ordering, limits, acquisition behavior, and all other qualification/recovery authorities are unchanged.

Changed paths are exactly:

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `docs/CURRENT_PHASE.md`
4. `docs/LATEST_CODEX_REPORT.md`

Verification completed:

- `python -m pytest tests/test_nar_race_entry_status_reacquisition_observability.py -q`: `355 passed in 3.05s`.
- `python -m pytest tests/test_nar_race_entry_status_source_profile_profile_a.py tests/test_nar_race_entry_status_source_profile_recovery_diagnostics.py tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py -q`: `249 passed in 0.71s`.
- `python -m pytest -q`: `4309 passed, 2841 subtests passed in 28.82s`.

The representative schema-3 blocked Profile-A record is `923` bytes excluding LF (`924` including LF), below `MAX_RECORD_BYTES = 4096`. The representative seven-record journal is `2695` bytes, below `MAX_JOURNAL_BYTES = 131072`.

No provider request occurred: Provider HTTP `0`, Phase44 `0`, GET `0`. No acquisition authorization was issued. No fixture, manifest, publication artifact, raw provider content, database, or log was created.

Phase70 authorization remains formally unconsumed:

`PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`

Because the executable support HEAD changes with this repair, its execution eligibility is `INVALIDATED_BY_EXECUTABLE_SUPPORT_HEAD_CHANGE`. It is unusable and must not be reused or rebound; it was not marked consumed.

Next permitted action: `CHATGPT_REVIEW_PHASE71_IMPLEMENTATION`.

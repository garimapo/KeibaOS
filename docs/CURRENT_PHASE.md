# Current Phase

## Phase

POST_V0_8_DAILY_REPLAY_56

## Name / state

Tracked NAR Source-Profile Publication Contract v2 Support

- Type: NO_NETWORK_TRACKED_CONTRACT_SUPPORT
- Status: INTEGRATED_PENDING_REMOTE_VERIFICATION
- Outcome: IMPLEMENTED_PUBLICATION_CONTRACT_V2_SUPPORT
- Review: PASS_FOR_INTEGRATION
- Branch: feature/post-v0.8-daily-replay
- Base: c9f704261cc37f95e12eb2fafa54f83b3055d944
- Predecessor: POST_V0_8_DAILY_REPLAY_55 — APPROVED_FOR_CODEX
- Design authority: PHASE55_DESIGN_REVIEW_PASS
- v1: V1_PUBLICATION_CONTRACT_NOT_EXACTLY_RECOVERABLE
- v2: VERSIONED_PUBLICATION_CONTRACT_REDESIGN_REQUIRED
- Design Review: PHASE56_DESIGN_REVIEW_PASS
- Implementation Manifest: exact approved six paths
- Phase44 Changes: NOT_AUTHORIZED
- Phase50 Changes: NOT_AUTHORIZED
- Provider HTTP: NOT_AUTHORIZED
- Phase57 Authorization: AUTHORIZATION_NOT_YET_ISSUED
- Next permitted action: INDEPENDENT_REMOTE_VERIFICATION

Phase54 remains factually PHASE54_ACQUISITION_AUTHORIZATION_UNCONSUMED and contractually PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2. Phase57 authorization is NOT_YET_ISSUED. No Phase54 authority is used or consumed here.

## Exact Phase56 implementation manifest

1. scripts/simulation/nar_race_entry_status_source_profile_profile_a.py — new pure Profile-A diagnostics.
2. tests/test_nar_race_entry_status_source_profile_profile_a.py — new synthetic Profile-A tests.
3. scripts/simulation/nar_race_entry_status_source_profile_publication_contract.py — new pure v2 identity, manifest, and safety support.
4. tests/test_nar_race_entry_status_source_profile_publication_contract.py — new synthetic safety, identity, and manifest tests.
5. docs/CURRENT_PHASE.md
6. docs/LATEST_CODEX_REPORT.md

No seventh path is authorized. Phase44, Phase50, Phase53, fixtures, .gitattributes, database, and logs are forbidden.

## Ownership and boundaries

The Profile-A module owns only the deterministic ENTRY_LISTING_PRESENT grammar. The publication-contract module owns only publication-safety evaluation plus v2 fixture-set, qualification, and manifest build/validate semantics. Phase53 remains the sole Profile-B authority through ProfileBDiagnostics and diagnose_nar_race_entry_status_profile_b. Phase44 remains the sole acquisition/capture authority. Phase50 remains operational evidence only.

Distinct authorities remain separate: formal raw/capture evidence; fixture-set identity; qualification identity; Profile-A diagnostics; Profile-B diagnostics; safety result; and Phase50 journal evidence. Neither a v2 artifact nor either Profile result proves MARKET_ELIGIBLE.

## Common v2 canonical form

Every canonical payload/manifest is exactly:

~~~
json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
~~~

SHA-256 is applied to those exact bytes. All identity digest text is lowercase hexadecimal. Exact type checks, exact closed key sets, canonical UTC text, canonical Phase44 identifiers, ordered documents, and canonical bytes are mandatory; any failure is fail-closed. run_id, journal sequence, PID, temp/repository path, machine/launcher state, raw body, headers/cookies, and arbitrary URL/query text are excluded.

## Fixture-set v2

Prefix: nar-race-entry-status-source-profile-fixture-set-v2:.

The payload is frozen as schema, schema_version, provider, target, documents, and closed_bundle_identity. schema is nar-race-entry-status-source-profile-fixture-set; schema_version is exact int 2; provider is NAR; target is exact formal NARRaceEntryStatusRaceIdentity represented as baba_code canonical decimal text, race_date canonical ISO text, and positive race_no.

documents is an exact two-element ordered list:

| Field | Type / required | Provenance | Identity treatment |
| --- | --- | --- | --- |
| role | exact str; required | fixed deba_table, then race_list | included |
| fixture_relative_path | exact str; required | fixed v2 path for matching role | included |
| request_identity | exact canonical request id; required | CaptureMetadataSummary document | included |
| capture_identity | exact canonical capture id; required | CaptureMetadataSummary document | included |
| response_sha256 | 64 lowercase hex; required | CaptureMetadataSummary document | included |
| response_byte_length | exact positive int; required | CaptureMetadataSummary document | included |
| requested_at / observed_at / captured_at | canonical UTC text; each required | CaptureMetadataSummary document | included |
| effective_url_matches_canonical | exact bool; required | CaptureMetadataSummary document | included |

closed_bundle_identity is required canonical formal bundle id from CaptureMetadataSummary. Fixed paths are tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/deba_table.html and race_list.html. No body is included.

## Qualification v2

Prefix: nar-race-entry-status-source-profile-qualification-v2:.

The payload has exactly schema, schema_version, provider, target, fixture_set_identity, profile_a, profile_b, and market_eligibility. schema is nar-race-entry-status-source-profile-qualification; schema_version is exact int 2; provider/target are the same canonical formal values; fixture_set_identity is the recomputed v2 identity; profile_a is ProfileADiagnostics.to_canonical_dict(); profile_b is the existing Phase53 ProfileBDiagnostics.to_canonical_dict(); market_eligibility is exact UNSUPPORTED.

Profile-A therefore contributes its overall result, terminal semantic, all three ordered predicate results, and safe fields. Profile-B contributes its existing overall result, EXPLICIT_WITHDRAWAL_PRESENT terminal semantic where qualified, ordered six predicate diagnostics, and safe fields. Raw HTML and operational state are absent. A qualification semantic change changes this identity.

## Manifest v2

The manifest root is a closed schema. Every field is required:

| Field path | Type | Source/provenance | Validation |
| --- | --- | --- | --- |
| manifest_schema | str | fixed nar-race-entry-status-source-profile-fixture-manifest | exact |
| manifest_schema_version | int | fixed 2 | exact |
| acquisition_semantics | str | fixed CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET | exact |
| provider | str | formal Phase44 target | exact NAR |
| target.baba_code / race_date / race_no | str / str / int | formal Phase44 target | canonical target |
| documents | two-item list | fixture-set v2 document payload | exact order and equality |
| closed_bundle_identity | str | CaptureMetadataSummary | canonical/recomputed equality |
| fixture_set_identity | str | fixture-set v2 builder | exact recomputation |
| qualification_identity | str | qualification-v2 builder | exact recomputation |
| publication_safety | object | safety evaluator canonical dict | closed schema / safe only |
| profile_a | object | Profile-A canonical dict | closed schema / safe only |
| profile_b | object | Phase53 canonical dict | exact existing Phase53 representation |
| market_eligibility | str | fixed contract disclaimer | exact UNSUPPORTED |

The manifest bytes use the common canonical form. Builder and validator both reconstruct expected objects from deterministic inputs; a noncanonical serialized input, wrong schema/version, missing/extra key, mismatched capture field, wrong identity, or wrong disclaimer raises a manifest validation error. No manifest field can claim MARKET_ELIGIBLE, historical availability, or a historical capture time.

## Profile-A grammar and API

Public symbols:

| Symbol | Input / output | Responsibility |
| --- | --- | --- |
| ProfileAOutcome | stable PASS, FAIL, AMBIGUOUS, UNSUPPORTED enum | predicate vocabulary |
| ProfileAPredicateIdentifier | ENTRY_TABLE_SCOPE, ORDINARY_HORSE_ROW_SHAPE, SELECTED_NON14_LISTING | frozen ordering |
| ProfileADiagnostics | frozen canonical result; to_canonical_dict() and canonical_bytes() | safe qualification result |
| diagnose_nar_race_entry_status_profile_a | exact bytes and exact NARRaceEntryStatusRaceIdentity -> ProfileADiagnostics | Phase57 qualification authority |

Input authority is exact DebaTable raw bytes plus exact formal Phase44 target identity. The target scope is that formal identity bound to the formal DebaTable capture; no launcher-local inference or alternate page is allowed. The source strictly UTF-8 decodes, passes an html.parser tag-balance validation, then uses BeautifulSoup html.parser. Invalid UTF-8 or unmatched/unclosed non-void markup returns ordered UNSUPPORTED predicate results, never repaired markup.

The frozen order and semantics are:

1. ENTRY_TABLE_SCOPE: among article.raceCard descendant section.cardTable table elements, count tables containing a tr with exactly one direct td.horseNum. One PASS; zero FAIL; more than one AMBIGUOUS.
2. ORDINARY_HORSE_ROW_SHAPE: every candidate selected-table row must have exactly one direct td.horseNum with an ASCII positive decimal and exactly one nonempty a.horseName[href]. No row FAIL; duplicate required node AMBIGUOUS; malformed element/number UNSUPPORTED.
3. SELECTED_NON14_LISTING: eligible rows must have a horse number other than 14 and one row per number. Select the lowest numeric eligible horse. Zero FAIL; duplicate candidate number AMBIGUOUS; malformed input UNSUPPORTED.

Safe fields are exactly entry_table_scope_count; ordinary_row_count; and selected_non14_candidate_count plus selected_provider_horse_no (null unless PASS). The first non-PASS is the first non-PASS in this order. All PASS gives QUALIFIED and terminal semantic ENTRY_LISTING_PRESENT; otherwise BLOCKED and null terminal semantic. No raw source, name, link, URL, DOM, or MARKET_ELIGIBLE field is retained.

## Publication safety grammar and API

Public symbols:

| Symbol | Input / output | Responsibility |
| --- | --- | --- |
| PublicationSafetyOutcome | SAFE, UNSAFE, AMBIGUOUS, UNSUPPORTED enum | aggregate/category vocabulary |
| PublicationSafetyCategory | five frozen categories in fixed order | stable result ordering |
| RawFixturePublicationSafety | frozen result; to_canonical_dict() and canonical_bytes() | safe publication decision |
| assess_nar_race_entry_status_raw_fixture_publication_safety | exact DebaTable bytes and exact RaceList bytes -> RawFixturePublicationSafety | in-memory publication gate |
| SourceProfilePublicationContractError | explicit validation/identity/manifest errors | programmer and structural contract failures |
| build_nar_race_entry_status_fixture_set_v2 / validate_nar_race_entry_status_fixture_set_v2 | exact target + CaptureMetadataSummary -> identity/value / independent validation | source-evidence identity |
| build_nar_race_entry_status_qualification_v2 / validate_nar_race_entry_status_qualification_v2 | target + fixture-set + Profile-A + Phase53 Profile-B -> identity/value / independent validation | semantic identity |
| build_nar_race_entry_status_manifest_v2 / validate_nar_race_entry_status_manifest_v2 | deterministic value objects -> canonical bytes/value; canonical bytes + deterministic inputs -> value | local manifest build/revalidation |

Both document bodies are strictly UTF-8 decoded and tag-balance checked. The evaluator inspects both roles and only attribute names/presence on meta, input, form, a, link, script, img, iframe; query parameter names/values in href, src, action; and header-style lines beginning authorization:, cookie:, set-cookie:. Attribute/query names are ASCII-lowercased with hyphen replaced by underscore.

| Category | Exact tokens |
| --- | --- |
| NO_AUTHENTICATION_MATERIAL | authorization, authentication, password, credential, api_key, access_token, refresh_token, bearer |
| NO_COOKIE_OR_SESSION_SECRET | cookie, set_cookie, session, session_id, sessionid, sid |
| NO_CSRF_OR_SECRET_TOKEN | csrf, xsrf, token, secret, nonce |
| NO_USER_ACCOUNT_IDENTIFIER | user, username, user_id, account, account_id, member, member_id, login_id, email |
| NO_PERSONALIZATION_IDENTIFIER | personalization, personalised, my_page, mypage, preference, favorite, history |

A matched sensitive key with nonempty value is UNSAFE. Empty sensitive fields, malformed sensitive query encoding, and structurally indeterminate matching are AMBIGUOUS. No match is SAFE. Decode/structural failure is UNSUPPORTED. The aggregate is SAFE and raw_fixture_publication_safe true only if all five categories are SAFE; every other aggregate fails closed. Results contain only schema_version, result, raw_fixture_publication_safe, five ordered identifier/outcome/finding_count records. They never retain raw HTML, visible text, URL/query/value, secret, or exception repr.

## Error strategy

Malformed/unsupported raw source returns a deterministic ordered diagnostic result. Exact-type violations, illegal value objects, malformed manifest structure, noncanonical serialization, and identity/provenance mismatch raise SourceProfilePublicationContractError. There is no coercion, partial qualification, fallback, or silently repaired object.

## Future synthetic tests and execution economy

Profile-A tests: valid listing; missing/duplicate target scope; missing/duplicate selected ordinary horse; nonnumeric horse; wrong scope; malformed DOM; invalid UTF-8; repeatability; canonical bytes; no raw/URL/MARKET_ELIGIBLE output.

Safety tests: minimal safe Deba/RaceList; each category independently; multiple categories; ambiguous token-like field/query; malformed DOM; invalid UTF-8; repeatability; no raw source/value echo; aggregate fail-closed result.

Identity/manifest tests: canonical byte/identity repeatability; input mapping order immaterial; changed SHA, length, or capture id changes fixture identity; run_id/temp/repository paths cannot affect identities; Profile-A/Profile-B semantic changes change qualification identity; raw HTML absent; builder/validator round-trip; wrong schema, missing/extra key, wrong provenance/id/SHA/length, noncanonical bytes, operational field, and disclaimer mismatch fail closed; local reread validation has no network.

Future EXECUTE order: focused v2 tests; Phase53 interoperability only if affected; relevant NAR regression once; full suite once when otherwise ready. No broad test run occurs in PREPARE.

## Future success and authorization

Future Phase56 success is READY_FOR_REVIEW / IMPLEMENTED_PUBLICATION_CONTRACT_V2_SUPPORT. It requires all six-path support, focused and relevant/full tests, no network, clean index, and diff check PASS.

Phase57 remains unauthorized until Phase56 is reviewed, integrated, independently remote-verified, and formally complete; then it needs PREPARE, review, APPROVE, and a new explicit one-shot authorization. Phase54 is never reused.

Phase41 remains DESIGN_BLOCKED. COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE and NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE remain OPEN. Positive market eligibility and WHOLE_MEETING_CANCELLATION remain UNSUPPORTED.

## Phase56 execution result

The exact six-path implementation is integrated pending independent remote verification. The tracked Profile-A module implements the frozen three-predicate grammar and canonical safe result. The publication-contract module implements the five-category fail-closed safety gate, fixture-set-v2 and qualification-v2 canonical payload/identity build-validation symmetry, and closed canonical manifest-v2 build-validation symmetry. Phase53 remains the sole Profile-B authority; Phase44 and Phase50 are unchanged.

Verification passed entirely without provider HTTP: focused Phase56 tests 46 passed (14 Profile-A and 32 publication-contract); Phase53 interoperability 23 passed; relevant NAR regression 690 passed plus 596 subtests; full repository suite 3,753 passed plus 2,841 subtests. Static no-network/source-safety checks, deterministic canonicalization checks, raw/secret exclusion checks, operational-metadata exclusion checks, MARKET_ELIGIBLE non-inference checks, and `git diff --check` passed.

The repository delta is exactly the approved six paths. The index remains empty. No Phase44, Phase50, Phase53, fixture, `.gitattributes`, database, log, or generated-cache path changed. No provider data was acquired, Phase44 live acquisition was not entered, Phase54 authority remains factually unconsumed but unusable for v2, and Phase57 authorization remains not issued.

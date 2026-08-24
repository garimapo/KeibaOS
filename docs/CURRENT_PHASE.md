# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4d0` — JRA race replay seed identity.

Formal base: `1394a6042da1938511798fbbbdf31b09b1a196f6`.

Approved prepare: `a3d09e8f80888a970c3fd90a67507cd35caaa2fe`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4d0-jra-race-replay-seed`.

## Implemented Contract

The phase adds a durable, immutable provider-specific JRA replay seed. It binds exact v4
navigation provenance, exact v3 target-card provenance, canonical JRA race and entry
identities, the normalized target-source collection, the dataset, and the caller's replay
information cutoff. Seed IDs and content digests are deterministic canonical JSON SHA-256
values.

Materialization is one `BEGIN IMMEDIATE` transaction. It uses only the fixed
`JRA`/`jra_official` source identity; atomically revalidates or creates exact JRA
external-to-internal race and entry mappings; rejects legacy collisions rather than
adopting them; and writes immutable seed headers and ordered entries. Exact-ID loads
rebuild and revalidate the seed and its mappings.

Migration v015 adds only the two replay-seed tables and the one full external-entry
mapping unique index. No capture family, HTTP, archive query, snapshot construction,
prediction, or live acquisition behavior is added.

The review correction requires every reused race and entry mapping to have valid prior
d0 seed proof. Unreferenced pre-existing mappings and legacy natural-key/horse-number
collisions fail as repository integrity errors. Prior proven race reuse checks only stable
race identity fields, so later exact target revisions may differ in weather, condition,
or runner count without rebinding the race.

Every target source record must carry the exact v3 response URL, digest, observation,
record-kind evidence role, and null provider/request availability fields. This validation
occurs before the transaction. Every failure after `BEGIN IMMEDIATE`, including an
unexpected Python exception, rolls back; unexpected exceptions are re-raised unchanged.
Exact loads validate repeated child organization, source, race, and internal-race columns.
V015 now rejects registered-v014 lookalikes missing request identity, malformed v010
mapping keys/FKs, and unregistered partial v015 objects before mutation.

## Verification

Seed domain tests: **29 passed**. Seed repository tests: **33 passed**. V015 migration
tests: **13 passed**. Related JRA and snapshot stack: **92 passed**. Migration regression
suite: **66 passed**. Full pytest suite: **2808 passed**. `git diff --check`
passed. No live HTTP or trusted real capture was performed.

## Stop Condition

Stop after this review branch is committed and pushed for independent review. Do not
integrate the formal branch or begin c4d.

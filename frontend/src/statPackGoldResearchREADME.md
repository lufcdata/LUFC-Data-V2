# Gold research rollout

The modules exported by `statPackGoldResearchIndex.ts` are intentionally isolated from `StatPack.tsx` and the signed-off fixture research path.

This is a safety boundary, not unfinished provenance. It allows each new research family to be validated against real LUFC database populations before production consumption.

Activation rule for each family:

1. Verify required authoritative database fields exist.
2. Verify population semantics on multiple fixtures/seasons.
3. Add regression coverage for scope and historical comparator selection.
4. Inspect generated wording against Gold editorial benchmarks.
5. Only then wire the family into the production Stat Pack.

Never fill a missing database dimension by web lookup, opponent-name inference, stadium-name inference or a fixture-specific correction.

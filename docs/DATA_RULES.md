# LUFC Data V2 — Data Rules

1. **Match identity:** `Match ID` is authoritative. A date is never a match key; multiple matches may occur on the same date.
2. **Player identity:** source `PLAYER ID` is preserved as a unique legacy ID. Names are display/alias data, not foreign keys.
3. **Appearances:** `Player 1`–`Player 11` are starts. `Sub 1`–`Sub 6` are substitutes used and therefore appearances.
4. **Goals:** V2 generates its own `goal_id`. Source `#` is retained only as a legacy reference because it is not unique.
5. **Managers:** manager people and managerial spells are separate entities.
6. **Corrections:** never silently mutate source exports. Every confirmed correction belongs in the migration correction log and must be testable.
7. **Competition naming:** preserve historically correct display names by era while grouping renamed competitions under a stable lineage.
8. **Derived facts:** appearances, goals, W-D-L totals and similar aggregates are calculated from atomic records.
9. **Source preservation:** original CSVs are immutable snapshots and are not edited in place.
10. **No fixture-specific application hacks:** historical anomalies are resolved in documented migration data, not hidden conditional code.

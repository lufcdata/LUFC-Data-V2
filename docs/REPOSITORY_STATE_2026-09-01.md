# LUFC Data V2 Repository State — 2026-09-01

## Canonical repository baseline

`main` is the canonical code/repository source of truth.

On 1 September 2026 the completed `database-load-v1` history and the Gold-locked `opposition-managers-gold-v1` history were consolidated into `main` with merge commit:

`c070632b4cbb027b8f0015f6aa7b70debc6d1c95`

The merge commit has both completed branch heads as parents, so neither workstream was squashed, copied over destructively, or abandoned.

Completed parent heads:

- `database-load-v1`: `37a96e6e40da26af51ece66afac2e9c53b045c40`
- `opposition-managers-gold-v1`: `889bd6496edd47dff8f80def4be4e02b7977a6d1`

Both historical branches are now ancestors of `main` and should be treated as completed reference branches rather than active development branches.

## Protected Gold layers currently represented in main

- Match core
- Match substitutions / substitution relationships
- Opposition Managers

The Opposition Managers Gold sign-off is documented in `docs/OPPOSITION_MANAGERS_GOLD_AUDIT_2026-09-01.md`.

## Live Supabase reconciliation at consolidation

Project: `nztiaxnrwojraiwipwjj`

- matches: 4,856
- seasons: 101
- clubs: 190
- players: 902
- player_matches: 58,528
- goals: 7,282
- match_substitutions: 5,112
- opposition managerial assignments: 4,856
- explicitly forensically validated opposition-manager assignments: 130
- opposition-manager raw/canonical/authority reconciliation mismatches: 0

## Migration-history note

The live Supabase migration ledger contains the structural Opposition Managers migration `20260901144957_create_relational_opposition_manager_assignments` plus the earlier enrichment/substitution migrations.

Some later Opposition Managers SQL files in the repository deliberately mirror corrections that were first applied live as audited DML during the forensic investigation. Therefore the repository migration directory is a reproducible record of the Gold corrections, while `supabase_migrations.schema_migrations` is not expected to list every later mirror-only correction file as an applied migration on the already-correct production database.

Do not blindly replay those mirror migrations against production merely to make migration-history numbers match. Validate semantic state instead.

## Branch discipline from this point

1. Start each new Gold-layer workstream from current `main`.
2. Keep one dedicated active branch per workstream.
3. Do not develop new layers directly on completed Gold branches.
4. Reconcile live Supabase and repository state before Gold sign-off.
5. After Gold approval, integrate the completed branch back into `main` before beginning the next major layer.
6. Never rewrite a protected Gold definition silently.

## Next workstream

Leeds Managers is the next proposed Gold-layer audit. Its working branch should be created from the consolidated `main`, not from either completed historical branch.

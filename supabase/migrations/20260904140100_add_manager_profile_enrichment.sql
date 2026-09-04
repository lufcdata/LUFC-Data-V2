create table if not exists public.manager_spell_profile_enrichment (
  manager_spell_id bigint primary key references public.manager_spells(manager_spell_id) on delete cascade,
  coaching_staff text,
  source_seasons integer,
  club_honours integer,
  promotions integer,
  achievements text,
  source_name text not null default 'MANAGERS.csv',
  updated_at timestamptz not null default now()
);

grant select on public.manager_spell_profile_enrichment to anon, authenticated;

comment on table public.manager_spell_profile_enrichment is
  'Spell-specific manager profile enrichment sourced from the researched MANAGERS.csv baseline. Live rows are resolved by manager_spells.legacy_manager_order to preserve canonical manager/spell identity.';

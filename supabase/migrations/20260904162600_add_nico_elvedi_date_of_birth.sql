update public.players
set date_of_birth = date '1996-09-30',
    birth_date_precision = 'exact',
    updated_at = now()
where player_id = 901
  and display_name = 'Nico Elvedi';

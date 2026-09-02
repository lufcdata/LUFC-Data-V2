update public.manager_spells ms
set profile_image_url_override = '/managers/Eddie Gray 2003.png'
from public.managers m
where ms.manager_id = m.manager_id
  and m.canonical_name = 'Eddie Gray'
  and ms.date_joined = date '2003-11-10'
  and ms.date_left = date '2004-05-10';

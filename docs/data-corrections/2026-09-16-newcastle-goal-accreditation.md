# Newcastle 4–1 Leeds? No: Leeds 4–1 Newcastle — goal accreditation correction

Date of match: 2026-09-14. Match ID: 4859. Correction confirmed: 2026-09-16.

Official Leeds United announcement: https://www.leedsunited.com/en/news/dominic-calvert-lewin-given-goal-against-newcastle-united

The expert panel reassigned Leeds' 34th-minute goal from Jayden Bogle to Dominic Calvert-Lewin. DCL scored at 34' and 45+1', two goals in the 4–1 win; his 2026/27 total is four goals in six competitive appearances at the time of the announcement.

Production database correction (Supabase project nztiaxnrwojraiwipwjj):
- public.goals goal_id 7288: leeds_player_id 877 -> 894; scorer_name_raw Jayden Bogle -> Dominic Calvert-Lewin; assist_player_id 894 -> NULL and assisted_by_raw Dominic Calvert-Lewin -> NULL. A scorer cannot assist his own goal. Do not infer a replacement assist without a source.
- goal_id 7289: goal_number_for_player_match 1 -> 2; existing scorer DCL, minute 45+1', and Tarik Muharemović assist preserved.
- Goal IDs 7287 (Lewis Miley own goal, 32') and 7290 (Noah Okafor, 59') unchanged. Score and goal-state chronology unchanged.
- Pre-change rows 7288 and 7289 backed up in preimport_backup_newcastle_20260914.goals_before_20260916_recredit.
- Audit entries public.migration_corrections correction_id 4 and 5.
- public.match_centre_goals and public.match_centre_players are database views that derive from public.goals; verification showed DCL 2, Bogle 0 for this match and DCL 4 goals for season 2026/27.

Editorial consequence: any earlier claim that Calvert-Lewin both scored and assisted against Newcastle on 2026-09-14 is now invalid; the former assist was removed following official goal recredit. Recompute opponent-specific score-and-assist streaks rather than reusing cached copy. No application code was changed as part of this data correction.

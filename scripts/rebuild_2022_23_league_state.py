#!/usr/bin/env python3
import csv, io, urllib.request
from collections import defaultdict
from datetime import datetime

RESULTS_URL='https://raw.githubusercontent.com/seanelvidge/England-football-results/main/EnglandLeagueResults.csv'
DEDUCTIONS_URL='https://raw.githubusercontent.com/seanelvidge/England-football-results/main/EnglishTeamPointDeductions.csv'
LEEDS='Leeds United'


def download_csv(url):
    raw=urllib.request.urlopen(url, timeout=120).read().decode('utf-8-sig')
    return list(csv.DictReader(io.StringIO(raw)))

rows=download_csv(RESULTS_URL)
deductions=download_csv(DEDUCTIONS_URL)

for r in rows:
    r['_date']=datetime.strptime(r['Date'],'%Y-%m-%d').date()
    r['_hg']=int(r['hGoal']); r['_ag']=int(r['aGoal'])
for r in deductions:
    r['_date']=datetime.strptime(r['Date'],'%Y-%m-%d').date()
    r['_pts']=int(r['Pts_deducted'])

# Group by season. Only reconstruct the exact division/tier occupied by Leeds.
by_season=defaultdict(list)
for r in rows:
    if r['Season'] and r['Season'] <= '2025/2026':
        by_season[r['Season']].append(r)

ded_by_season=defaultdict(list)
for r in deductions:
    ded_by_season[r['Season']].append(r)

out=[]
season_audit=[]
for season in sorted(by_season):
    season_rows=by_season[season]
    leeds_rows=[r for r in season_rows if LEEDS in (r['HomeTeam'],r['AwayTeam'])]
    if not leeds_rows:
        continue
    # Leeds United entered the Football League in 1920/21.
    if season < '1920/1921':
        continue
    divisions={(r['Division'],r['Tier']) for r in leeds_rows}
    if len(divisions)!=1:
        raise AssertionError((season,'multiple Leeds divisions',divisions))
    division,tier=next(iter(divisions))
    league=[r for r in season_rows if r['Division']==division and r['Tier']==tier]

    # Historical expungements used by the source's own league-table implementation.
    if season=='1931/1932':
        league=[r for r in league if 'Wigan Borough' not in (r['HomeTeam'],r['AwayTeam'])]
    if season=='1961/1962':
        league=[r for r in league if 'Accrington Stanley' not in (r['HomeTeam'],r['AwayTeam'])]

    teams=sorted({r['HomeTeam'] for r in league}|{r['AwayTeam'] for r in league})
    if LEEDS not in teams:
        raise AssertionError((season,'Leeds missing after filters'))
    state={t:{'p':0,'gf':0,'ga':0,'pts':0} for t in teams}
    adjustments={t:0 for t in teams}
    season_deds=sorted([r for r in ded_by_season.get(season,[]) if r['Team'] in state],key=lambda r:r['_date'])
    ded_i=0
    start_year=int(season[:4])
    win_points=2 if start_year<1981 else 3
    goal_average=start_year<1976

    def positions():
        def key(t):
            s=state[t]
            pts=s['pts']+adjustments[t]
            gd=s['gf']-s['ga']
            gr=(s['gf']/s['ga']) if s['ga'] else (float('inf') if s['gf'] else 0.0)
            return (-pts, -(gr if goal_average else gd), -s['gf'], t)
        ranked=sorted(teams,key=key)
        return {t:i+1 for i,t in enumerate(ranked)}

    def apply_match(r):
        h,a=r['HomeTeam'],r['AwayTeam']; hg,ag=r['_hg'],r['_ag']
        state[h]['p']+=1; state[a]['p']+=1
        state[h]['gf']+=hg; state[h]['ga']+=ag
        state[a]['gf']+=ag; state[a]['ga']+=hg
        if hg>ag: state[h]['pts']+=win_points
        elif ag>hg: state[a]['pts']+=win_points
        else: state[h]['pts']+=1; state[a]['pts']+=1

    bydate=defaultdict(list)
    for r in league: bydate[r['_date']].append(r)
    first=True; season_count=0
    for d in sorted(bydate):
        # Apply deductions whose effective date is this date before the day's fixtures.
        while ded_i<len(season_deds) and season_deds[ded_i]['_date']<=d:
            dr=season_deds[ded_i]
            adjustments[dr['Team']]-=dr['_pts']
            ded_i+=1
        before=positions()
        day=bydate[d]
        leeds_today=[r for r in day if LEEDS in (r['HomeTeam'],r['AwayTeam'])]
        for r in day: apply_match(r)
        after=positions()
        if leeds_today:
            if len(leeds_today)!=1: raise AssertionError((season,d,'multiple Leeds fixtures'))
            r=leeds_today[0]
            lg=r['_hg'] if r['HomeTeam']==LEEDS else r['_ag']
            og=r['_ag'] if r['HomeTeam']==LEEDS else r['_hg']
            opp=r['AwayTeam'] if r['HomeTeam']==LEEDS else r['HomeTeam']
            pb=None if first else before[LEEDS]
            pa=after[LEEDS]
            change=None if pb is None else pb-pa
            points=state[LEEDS]['pts']+adjustments[LEEDS]
            out.append({
                'season':season,'date':d.isoformat(),'division':division,'tier':tier,
                'opponent':opp,'venue':'H' if r['HomeTeam']==LEEDS else 'A',
                'leeds_score':lg,'opponent_score':og,
                'position_before':pb,'position_after_calc':pa,
                'position_change':change,'points_after_calc':points,
            })
            season_count+=1; first=False
    season_audit.append((season,season_count,division,tier))

# Regression guard: the already-Gold 2022/23 reconstruction must still reproduce its key checkpoints.
checks={'2022-10-29':15,'2022-11-05':12,'2023-02-25':17,'2023-03-18':14,'2023-05-28':19}
for d,p in checks.items():
    got=next(x['position_after_calc'] for x in out if x['season']=='2022/2023' and x['date']==d)
    assert got==p,(d,got,p)
assert next(x for x in out if x['season']=='2022/2023' and x['date']=='2023-05-28')['points_after_calc']==31

fields=['season','date','division','tier','opponent','venue','leeds_score','opponent_score','position_before','position_after_calc','position_change','points_after_calc']
with open('leeds_before_change_candidates.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
with open('leeds_before_change_season_audit.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['season','leeds_rows','division','tier']); w.writerows(season_audit)

print(f'GENERATED candidates={len(out)} seasons={len(season_audit)}')
print('2022_23_GOLD_CHECKPOINTS_OK')

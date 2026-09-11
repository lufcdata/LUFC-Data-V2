#!/usr/bin/env python3
import csv, io, urllib.request
from collections import defaultdict
from datetime import datetime

URL='https://raw.githubusercontent.com/datasets/football-datasets/main/datasets/premier-league/season-2223.csv'
raw=urllib.request.urlopen(URL, timeout=30).read().decode('utf-8')
rows=list(csv.DictReader(io.StringIO(raw)))
assert len(rows)==380, len(rows)
for r in rows:
    r['Date']=datetime.strptime(r['Date'],'%Y-%m-%d').date()
    r['FTHG']=int(r['FTHG']); r['FTAG']=int(r['FTAG'])

teams=sorted({r['HomeTeam'] for r in rows}|{r['AwayTeam'] for r in rows})
state={t:{'p':0,'gf':0,'ga':0,'pts':0} for t in teams}

def table():
    ranked=sorted(teams,key=lambda t:(-state[t]['pts'],-(state[t]['gf']-state[t]['ga']),-state[t]['gf'],t))
    return {t:i+1 for i,t in enumerate(ranked)}

def apply(r):
    h,a=r['HomeTeam'],r['AwayTeam']; hg,ag=r['FTHG'],r['FTAG']
    state[h]['p']+=1; state[a]['p']+=1
    state[h]['gf']+=hg; state[h]['ga']+=ag; state[a]['gf']+=ag; state[a]['ga']+=hg
    if hg>ag: state[h]['pts']+=3
    elif ag>hg: state[a]['pts']+=3
    else: state[h]['pts']+=1; state[a]['pts']+=1

bydate=defaultdict(list)
for r in rows: bydate[r['Date']].append(r)
first=True
out=[]
for d in sorted(bydate):
    before=table()
    day=bydate[d]
    leeds=[r for r in day if r['HomeTeam']=='Leeds' or r['AwayTeam']=='Leeds']
    for r in day: apply(r)
    after=table()
    if leeds:
        r=leeds[0]
        leeds_goals=r['FTHG'] if r['HomeTeam']=='Leeds' else r['FTAG']
        opp_goals=r['FTAG'] if r['HomeTeam']=='Leeds' else r['FTHG']
        opp=r['AwayTeam'] if r['HomeTeam']=='Leeds' else r['HomeTeam']
        pos_before=None if first else before['Leeds']
        pos_after=after['Leeds']
        change=None if pos_before is None else pos_before-pos_after
        out.append((d.isoformat(),opp,leeds_goals,opp_goals,pos_before,pos_after,change,state['Leeds']['pts']))
        first=False

assert len(out)==38, len(out)
checks={
'2022-10-29':15,
'2022-11-05':12,
'2023-02-25':17,
'2023-03-18':14,
'2023-05-28':19,
}
for d,p in checks.items():
    got=next(x[5] for x in out if x[0]==d)
    assert got==p,(d,got,p)
assert out[-1][7]==31,out[-1]
print('date,opponent,leeds_score,opponent_score,position_before,position_after,position_change,points_after')
for x in out:
    print(','.join('' if v is None else str(v) for v in x))
print('VALIDATION_OK rows=38 final_points=31 final_position=19')

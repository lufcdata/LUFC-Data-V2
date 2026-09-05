import React, { Component, Fragment, useState, type ErrorInfo, type ReactNode } from 'react';
import { Moon, Sun } from 'lucide-react';
import Leaderboard from './Leaderboard';
import Managers from './Managers';
import ManagerPage from './ManagerPage';
import Players from './Players';
import Matches from './Matches';
import Goals from './Goals';
import MatchCentre from './MatchCentre';
import PlayerPage from './PlayerPage';
import PlayerMatchLog from './PlayerMatchLog';
import TestA1 from './TestA1';
import PlayerAdmin from './PlayerAdmin';
import './PlayerMatchLog.css';
import './PlayerPageChart.css';
import './MobilePolish.css';
import './LightTheme.css';

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('LUFC Data runtime error', error, info); }
  render() { if (this.state.error) return <main className="leaderboard-isolate"><div className="card lb-runtime-error"><strong>LUFC Data could not render.</strong><span>{this.state.error.message}</span></div></main>; return this.props.children; }
}

type Page='matches'|'match-centre'|'goals'|'players'|'player-profile'|'managers'|'manager-profile'|'opponents'|'test-a1'|'player-admin';
function App() {
 const [theme,setTheme]=useState<'light'|'dark'>('dark');
 const [page,setPage]=useState<Page>(()=>{const params=new URLSearchParams(window.location.search);return window.location.pathname==='/admin/players'||params.get('admin')==='players'?'player-admin':'matches'});
 const [selectedMatchId,setSelectedMatchId]=useState(4846);
 const [selectedPlayerId,setSelectedPlayerId]=useState(276);
 const [selectedPlayerName,setSelectedPlayerName]=useState('Billy Bremner');
 const [selectedManagerId,setSelectedManagerId]=useState(49);
 const isDark=theme==='dark';
 const openMatch=(matchId:number)=>{setSelectedMatchId(matchId);setPage('match-centre')};
 const openPlayer=(playerId:number,playerName:string)=>{setSelectedPlayerId(playerId);setSelectedPlayerName(playerName);setPage('player-profile')};
 const openManager=(managerId:number)=>{setSelectedManagerId(managerId);setPage('manager-profile')};
 const content=page==='matches'?<Matches onSelectMatch={openMatch}/>:page==='match-centre'?<MatchCentre matchId={selectedMatchId} onBack={()=>setPage('matches')}/>:page==='goals'?<Goals/>:page==='players'?<Players onSelectPlayer={openPlayer}/>:page==='player-profile'?<Fragment key={selectedPlayerId}><PlayerPage playerId={selectedPlayerId} onBack={()=>setPage('players')}/><PlayerMatchLog playerId={selectedPlayerId} playerName={selectedPlayerName}/></Fragment>:page==='managers'?<Managers onSelectManager={openManager}/>:page==='manager-profile'?<ManagerPage managerId={selectedManagerId} onBack={()=>setPage('managers')}/>:page==='test-a1'?<TestA1/>:page==='player-admin'?<PlayerAdmin/>:<Leaderboard/>;
 return <ErrorBoundary><main className={`leaderboard-isolate ${isDark?'theme-dark':'theme-light'}`}>
  {page!=='player-admin'&&<nav className="page-nav" aria-label="Database sections">
   <button className={page==='matches'||page==='match-centre'?'active':''} onClick={()=>setPage('matches')}>Matches</button>
   <button className={page==='goals'?'active':''} onClick={()=>setPage('goals')}>Goals</button>
   <button className={page==='players'||page==='player-profile'?'active':''} onClick={()=>setPage('players')}>Players</button>
   <button className={page==='managers'||page==='manager-profile'?'active':''} onClick={()=>setPage('managers')}>Managers</button>
   <button className={page==='opponents'?'active':''} onClick={()=>setPage('opponents')}>Opponents</button>
   <button className={page==='test-a1'?'active':''} onClick={()=>setPage('test-a1')}>Test A1</button>
  </nav>}
  <button type="button" className="theme-toggle" onClick={()=>setTheme(c=>c==='light'?'dark':'light')} aria-label={isDark?'Switch to light mode':'Switch to dark mode'} aria-pressed={isDark} title={isDark?'Switch to light mode':'Switch to dark mode'}><Sun size={15} strokeWidth={1.6} className={`theme-icon ${!isDark?'active':''}`}/><Moon size={15} strokeWidth={1.25} className={`theme-icon ${isDark?'active':''}`}/></button>
  {content}
 </main></ErrorBoundary>;
}
export default App;
import React, { Component, Fragment, useState, type ErrorInfo, type ReactNode } from 'react';
import { Moon, Sun } from 'lucide-react';
import Leaderboard from './Leaderboard';
import Managers from './Managers';
import ManagerPage from './ManagerPage';
import Players from './Players';
import Matches from './Matches';
import MatchCentre from './MatchCentre';
import PlayerPage from './PlayerPage';
import PlayerMatchLog from './PlayerMatchLog';
import TestPage from './TestPage';
import TestPage2 from './TestPage2';
import TestPage3 from './TestPage3';
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

type Page='matches'|'match-centre'|'players'|'player-profile'|'managers'|'manager-profile'|'opponents'|'test'|'test2'|'test3';
function App() {
 const [theme,setTheme]=useState<'light'|'dark'>('dark');
 const [page,setPage]=useState<Page>('matches');
 const [selectedMatchId,setSelectedMatchId]=useState(4846);
 const [selectedPlayerId,setSelectedPlayerId]=useState(276);
 const [selectedPlayerName,setSelectedPlayerName]=useState('Billy Bremner');
 const [selectedManagerId,setSelectedManagerId]=useState(49);
 const isDark=theme==='dark';
 const openMatch=(matchId:number)=>{setSelectedMatchId(matchId);setPage('match-centre')};
 const openPlayer=(playerId:number,playerName:string)=>{setSelectedPlayerId(playerId);setSelectedPlayerName(playerName);setPage('player-profile')};
 const openManager=(managerId:number)=>{setSelectedManagerId(managerId);setPage('manager-profile')};
 const content=page==='matches'?<Matches onSelectMatch={openMatch}/>:page==='match-centre'?<MatchCentre matchId={selectedMatchId} onBack={()=>setPage('matches')}/>:page==='players'?<Players onSelectPlayer={openPlayer}/>:page==='player-profile'?<Fragment key={selectedPlayerId}><PlayerPage playerId={selectedPlayerId} onBack={()=>setPage('players')}/><PlayerMatchLog playerId={selectedPlayerId} playerName={selectedPlayerName}/></Fragment>:page==='managers'?<Managers onSelectManager={openManager}/>:page==='manager-profile'?<ManagerPage managerId={selectedManagerId} onBack={()=>setPage('managers')}/>:page==='test'?<TestPage/>:page==='test2'?<TestPage2/>:page==='test3'?<TestPage3/>:<Leaderboard/>;
 return <ErrorBoundary><main className={`leaderboard-isolate ${isDark?'theme-dark':'theme-light'}`}>
  <nav className="page-nav" aria-label="Database sections">
   <button className={page==='matches'||page==='match-centre'?'active':''} onClick={()=>setPage('matches')}>Matches</button>
   <button className={page==='players'||page==='player-profile'?'active':''} onClick={()=>setPage('players')}>Players</button>
   <button className={page==='managers'||page==='manager-profile'?'active':''} onClick={()=>setPage('managers')}>Managers</button>
   <button className={page==='opponents'?'active':''} onClick={()=>setPage('opponents')}>Opponents</button>
   <button className={page==='test'?'active':''} onClick={()=>setPage('test')}>Test</button>
   <button className={page==='test2'?'active':''} onClick={()=>setPage('test2')}>Test 2</button>
   <button className={page==='test3'?'active':''} onClick={()=>setPage('test3')}>Test 3</button>
  </nav>
  <button type="button" className="theme-toggle" onClick={()=>setTheme(c=>c==='light'?'dark':'light')} aria-label={isDark?'Switch to light mode':'Switch to dark mode'} aria-pressed={isDark} title={isDark?'Switch to light mode':'Switch to dark mode'}><Sun size={15} strokeWidth={1.6} className={`theme-icon ${!isDark?'active':''}`}/><Moon size={15} strokeWidth={1.25} className={`theme-icon ${isDark?'active':''}`}/></button>
  {content}
 </main></ErrorBoundary>;
}
export default App;
import React, { Component, Fragment, useState, type ErrorInfo, type ReactNode } from 'react';
import { Moon, Sun } from 'lucide-react';
import Leaderboard from './Leaderboard';
import OpponentPage from './OpponentPage';
import Managers from './Managers';
import ManagerPage from './ManagerPage';
import Players from './Players';
import Matches from './Matches';
import Seasons from './Seasons';
import Debutants from './Debutants';
import Goals from './Goals';
import RedCards from './RedCards';
import Penalties from './Penalties';
import HatTricks from './HatTricks';
import OwnGoals from './OwnGoals';
import FirstTo from './FirstTo';
import Streaks from './Streaks';
import StatPack from './StatPack';
import MatchCentre from './MatchCentre';
import PlayerPage from './PlayerPage';
import PlayerMatchLog from './PlayerMatchLog';
import TestA1 from './TestA1';
import PlayerAdmin from './PlayerAdmin';
import './PlayerMatchLog.css';
import './PlayerPageChart.css';
import './MobilePolish.css';
import './LightTheme.css';
import './StatPack.css';
import './RedCards.css';
import './Penalties.css';
import './OwnGoals.css';
import './FirstTo.css';
import './MobileNavigation.css';

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('LUFC Data runtime error', error, info); }
  render() { if (this.state.error) return <main className="leaderboard-isolate"><div className="card lb-runtime-error"><strong>LUFC Data could not render.</strong><span>{this.state.error.message}</span></div></main>; return this.props.children; }
}

type Page='matches'|'match-centre'|'seasons'|'debutants'|'goals'|'red-cards'|'penalties'|'hat-tricks'|'own-goals'|'first-to'|'streaks'|'stat-pack'|'players'|'player-profile'|'managers'|'manager-profile'|'opponents'|'opponent-profile'|'test-a1'|'player-admin';
const navItems: {page:Page;label:string}[] = [
 {page:'matches',label:'Matches'}, {page:'seasons',label:'Seasons'}, {page:'players',label:'Players'},
 {page:'goals',label:'Goals'}, {page:'managers',label:'Managers'}, {page:'first-to',label:'First To'},
 {page:'streaks',label:'Streaks'}, {page:'opponents',label:'Opponents'}, {page:'red-cards',label:'Red Cards'},
 {page:'penalties',label:'Penalties'}, {page:'hat-tricks',label:'Hat-Tricks'}, {page:'debutants',label:'Debutants'},
 {page:'own-goals',label:'Own Goals'}, {page:'stat-pack',label:'Stat Pack'}, {page:'test-a1',label:'Test A1'}
];
function App() {
 const [theme,setTheme]=useState<'light'|'dark'>('dark');
 const [page,setPage]=useState<Page>(()=>{const params=new URLSearchParams(window.location.search);return window.location.pathname==='/admin/players'||params.get('admin')==='players'?'player-admin':'matches'});
 const [selectedMatchId,setSelectedMatchId]=useState(4846);
 const [selectedPlayerId,setSelectedPlayerId]=useState(276);
 const [selectedPlayerName,setSelectedPlayerName]=useState('Billy Bremner');
 const [selectedManagerId,setSelectedManagerId]=useState(49);
 const [selectedOpponentId,setSelectedOpponentId]=useState(48);
 const isDark=theme==='dark';
 const openMatch=(matchId:number)=>{setSelectedMatchId(matchId);setPage('match-centre')};
 const openPlayer=(playerId:number,playerName:string)=>{setSelectedPlayerId(playerId);setSelectedPlayerName(playerName);setPage('player-profile')};
 const openManager=(managerId:number)=>{setSelectedManagerId(managerId);setPage('manager-profile')};
 const openOpponent=(clubId:number)=>{setSelectedOpponentId(clubId);setPage('opponent-profile')};
 const content=page==='matches'?<Matches onSelectMatch={openMatch}/>:page==='match-centre'?<MatchCentre matchId={selectedMatchId} onBack={()=>setPage('matches')} onSelectPlayer={openPlayer} onSelectManager={openManager} onSelectOpponent={openOpponent}/>:page==='seasons'?<Seasons/>:page==='debutants'?<Debutants onSelectMatch={openMatch} onSelectPlayer={openPlayer}/>:page==='goals'?<Goals onSelectPlayer={openPlayer}/>:page==='red-cards'?<RedCards onSelectMatch={openMatch} onSelectPlayer={openPlayer} onSelectManager={openManager}/>:page==='penalties'?<Penalties onSelectMatch={openMatch} onSelectPlayer={openPlayer}/>:page==='hat-tricks'?<HatTricks onSelectMatch={openMatch} onSelectPlayer={openPlayer}/>:page==='own-goals'?<OwnGoals onSelectMatch={openMatch}/>:page==='first-to'?<FirstTo/>:page==='streaks'?<Streaks onSelectMatch={openMatch}/>:page==='stat-pack'?<StatPack/>:page==='players'?<Players onSelectPlayer={openPlayer}/>:page==='player-profile'?<Fragment key={selectedPlayerId}><PlayerPage playerId={selectedPlayerId} onBack={()=>setPage('players')}/><PlayerMatchLog playerId={selectedPlayerId} playerName={selectedPlayerName}/></Fragment>:page==='managers'?<Managers onSelectManager={openManager}/>:page==='manager-profile'?<ManagerPage managerId={selectedManagerId} onBack={()=>setPage('managers')}/>:page==='opponents'?<Leaderboard onSelectOpponent={openOpponent}/>:page==='opponent-profile'?<OpponentPage clubId={selectedOpponentId} onBack={()=>setPage('opponents')}/>:page==='test-a1'?<TestA1/>:page==='player-admin'?<PlayerAdmin/>:<Leaderboard onSelectOpponent={openOpponent}/>;
 const navPage:Page=page==='match-centre'?'matches':page==='player-profile'?'players':page==='manager-profile'?'managers':page==='opponent-profile'?'opponents':page;
 return <ErrorBoundary><main className={`leaderboard-isolate ${isDark?'theme-dark':'theme-light'}`}>
  {page!=='player-admin'&&<>
   <nav className="page-nav" aria-label="Database sections">
    {navItems.map(item=><button key={item.page} type="button" className={navPage===item.page?'active':''} onClick={()=>setPage(item.page)}>{item.label}</button>)}
   </nav>
   <div className="mobile-page-navigation">
    <label htmlFor="mobile-page-select">Section</label>
    <select id="mobile-page-select" aria-label="Choose database section" value={navPage} onChange={e=>setPage(e.target.value as Page)}>
     {navItems.map(item=><option key={item.page} value={item.page}>{item.label}</option>)}
    </select>
   </div>
  </>}
  <button type="button" className="theme-toggle" onClick={()=>setTheme(c=>c==='light'?'dark':'light')} aria-label={isDark?'Switch to light mode':'Switch to dark mode'} aria-pressed={isDark} title={isDark?'Switch to light mode':'Switch to dark mode'}><Sun size={15} strokeWidth={1.6} className={`theme-icon ${!isDark?'active':''}`}/><Moon size={15} strokeWidth={1.25} className={`theme-icon ${isDark?'active':''}`}/></button>
  {content}
 </main></ErrorBoundary>;
}
export default App;

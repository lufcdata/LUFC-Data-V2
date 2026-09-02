import React, { Component, useState, type ErrorInfo, type ReactNode } from 'react';
import { Moon, Sun } from 'lucide-react';
import Leaderboard from './Leaderboard';
import Managers from './Managers';
import Players from './Players';
import Matches from './Matches';
import PlayerPage from './PlayerPage';
import PlayerManagerWidget from './PlayerManagerWidget';

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('LUFC Data runtime error', error, info); }
  render() { if (this.state.error) return <main className="leaderboard-isolate"><div className="card lb-runtime-error"><strong>LUFC Data could not render.</strong><span>{this.state.error.message}</span></div></main>; return this.props.children; }
}

type Page='matches'|'players'|'player-profile'|'managers'|'opponents';
function App() {
 const [theme,setTheme]=useState<'light'|'dark'>('dark');
 const [page,setPage]=useState<Page>('player-profile');
 const isDark=theme==='dark';
 const content=page==='matches'?<Matches/>:page==='players'?<Players/>:page==='player-profile'?<><PlayerPage onBack={()=>setPage('players')}/><PlayerManagerWidget/></>:page==='managers'?<Managers/>:<Leaderboard/>;
 return <ErrorBoundary><main className={`leaderboard-isolate ${isDark?'theme-dark':'theme-light'}`}>
  <nav className="page-nav" aria-label="Database sections">
   <button className={page==='matches'?'active':''} onClick={()=>setPage('matches')}>Matches</button>
   <button className={page==='players'||page==='player-profile'?'active':''} onClick={()=>setPage('players')}>Players</button>
   <button className={page==='managers'?'active':''} onClick={()=>setPage('managers')}>Managers</button>
   <button className={page==='opponents'?'active':''} onClick={()=>setPage('opponents')}>Opponents</button>
  </nav>
  <button type="button" className="theme-toggle" onClick={()=>setTheme(c=>c==='light'?'dark':'light')} aria-label={isDark?'Switch to light mode':'Switch to dark mode'} aria-pressed={isDark} title={isDark?'Switch to light mode':'Switch to dark mode'}><Sun size={15} strokeWidth={1.6} className={`theme-icon ${!isDark?'active':''}`}/><Moon size={15} strokeWidth={1.25} className={`theme-icon ${isDark?'active':''}`}/></button>
  {content}
 </main></ErrorBoundary>;
}
export default App;

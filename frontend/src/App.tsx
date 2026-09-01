import { Bell, BarChart3, CircleHelp, Gauge, Map, Search, Settings2, Shield, Trophy, Users } from 'lucide-react';
import Leaderboard from './Leaderboard';

export default function App(){
  return <main className="app-shell">
    <aside className="rail">
      <div className="brand-mark">S</div><div className="rail-divider"/>
      <nav className="rail-nav" aria-label="Primary navigation">
        <button className="rail-button" title="Overview"><Gauge size={18}/></button>
        <button className="rail-button" title="Match map"><Map size={18}/></button>
        <button className="rail-button selected" title="Leaderboard"><Trophy size={18}/></button>
        <button className="rail-button" title="Squad"><Users size={18}/></button>
        <button className="rail-button" title="Performance"><BarChart3 size={18}/></button>
        <button className="rail-button" title="Defence"><Shield size={18}/></button>
      </nav>
      <div className="rail-bottom"><button className="rail-button"><CircleHelp size={18}/></button><button className="rail-button"><Settings2 size={18}/></button><div className="avatar">AM</div></div>
    </aside>
    <section className="workspace">
      <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>Leaderboard</strong></div><div className="top-actions"><div className="search-box"><Search size={15}/><span>Search anything</span><kbd>⌘ K</kbd></div><button className="icon-button"><Bell size={17}/><i/></button><div className="avatar small">AM</div></div></header>
      <div className="content"><div className="page-heading"><div><div className="eyebrow"><span className="live-dot"/> LUFC archive <span className="eyebrow-separator">•</span> 1920–present</div><h1>Opponent <span>leaderboard</span></h1><p className="subheading">Team comparison · All-time competitive head-to-head record</p></div></div><Leaderboard/></div>
    </section>
  </main>;
}

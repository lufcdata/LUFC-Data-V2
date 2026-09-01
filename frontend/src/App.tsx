import React, { Component, type ErrorInfo, type ReactNode } from 'react';
import Leaderboard from './Leaderboard';

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('LUFC Data runtime error', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="leaderboard-isolate">
          <div className="card lb-runtime-error">
            <strong>LUFC Data could not render.</strong>
            <span>{this.state.error.message}</span>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <main className="leaderboard-isolate">
        <Leaderboard />
      </main>
    </ErrorBoundary>
  );
}

export default App;

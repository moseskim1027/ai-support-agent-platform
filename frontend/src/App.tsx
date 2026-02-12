import { useState } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import Login from './components/Login';
import Register from './components/Register';
import './styles/App.css';

function App() {
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const handleShowAuth = () => {
    setShowAuth(true);
  };

  const handleCloseAuth = () => {
    setShowAuth(false);
  };

  const switchToRegister = () => {
    setAuthMode('register');
  };

  const switchToLogin = () => {
    setAuthMode('login');
  };

  return (
    <AuthProvider>
      <div className="app">
        <Header onShowAuth={handleShowAuth} />

        {showAuth && (
          <div className="auth-overlay" onClick={handleCloseAuth}>
            <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
              <button className="close-button" onClick={handleCloseAuth}>
                ×
              </button>
              {authMode === 'login' ? (
                <Login onSwitchToRegister={switchToRegister} />
              ) : (
                <Register onSwitchToLogin={switchToLogin} />
              )}
            </div>
          </div>
        )}

        <ChatInterface />
      </div>
    </AuthProvider>
  );
}

export default App;

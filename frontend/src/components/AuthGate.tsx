import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Header from './Header';
import ChatInterface from './ChatInterface';
import Login from './Login';
import Register from './Register';

const AuthGate: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const switchToRegister = () => {
    setAuthMode('register');
  };

  const switchToLogin = () => {
    setAuthMode('login');
  };

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="app loading-container">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  // If not authenticated, show login/register page
  if (!isAuthenticated) {
    return (
      <div className="app auth-page">
        <div className="auth-page-container">
          {authMode === 'login' ? (
            <Login onSwitchToRegister={switchToRegister} />
          ) : (
            <Register onSwitchToLogin={switchToLogin} />
          )}
        </div>
      </div>
    );
  }

  // If authenticated, show the main app
  return (
    <div className="app">
      <Header />
      <ChatInterface />
    </div>
  );
};

export default AuthGate;

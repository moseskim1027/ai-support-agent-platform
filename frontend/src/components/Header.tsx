import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface HeaderProps {
  onShowAuth?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onShowAuth }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const [isHealthy, setIsHealthy] = useState(false);
  const [version, setVersion] = useState('');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await apiService.checkHealth();
        setIsHealthy(health.status === 'healthy');
        setVersion(health.version);
      } catch {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1>AI Support Agent Platform</h1>
          <p>Multi-agent orchestration with LangGraph & OpenAI</p>
        </div>
        <div className="header-right">
          {isAuthenticated && user ? (
            <div className="user-menu">
              <span className="user-info">👤 {user.full_name || user.username}</span>
              <button onClick={logout} className="logout-button">
                Logout
              </button>
            </div>
          ) : (
            <button onClick={onShowAuth} className="login-button">
              Sign In
            </button>
          )}
        </div>
      </div>
      {version && (
        <div className="status-indicator">
          <span
            className="status-dot"
            style={{ backgroundColor: isHealthy ? '#10b981' : '#ef4444' }}
          ></span>
          <span>
            Backend {isHealthy ? 'Connected' : 'Disconnected'} (v{version})
          </span>
        </div>
      )}
    </header>
  );
};

export default Header;

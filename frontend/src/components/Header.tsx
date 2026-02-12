import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface HeaderProps {
  showBackButton?: boolean;
  onBack?: () => void;
}

const Header: React.FC<HeaderProps> = ({ showBackButton = false, onBack }) => {
  const { user, logout } = useAuth();
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
          <div className="user-menu">
            <div>
              <span className="user-info">👤 {user?.full_name || user?.username}</span>
              <button onClick={logout} className="logout-button">
                Logout
              </button>
            </div>
            {showBackButton && (
              <button onClick={onBack} className="back-button">
                ← Back
              </button>
            )}
          </div>
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

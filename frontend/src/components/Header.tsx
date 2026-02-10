import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

const Header = () => {
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
      <h1>AI Support Agent Platform</h1>
      <p>Multi-agent orchestration with LangGraph & OpenAI</p>
      {version && (
        <div className="status-indicator">
          <span className="status-dot" style={{ backgroundColor: isHealthy ? '#10b981' : '#ef4444' }}></span>
          <span>Backend {isHealthy ? 'Connected' : 'Disconnected'} (v{version})</span>
        </div>
      )}
    </header>
  );
};

export default Header;

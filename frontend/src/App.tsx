import { AuthProvider } from './contexts/AuthContext';
import AuthGate from './components/AuthGate';
import './styles/App.css';

function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
}

export default App;

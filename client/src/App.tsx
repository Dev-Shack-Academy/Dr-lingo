import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import TranslationChatPage from './pages/TranslationChatPage';
import AuthPage from './pages/AuthPage';
import AdminPage from './pages/AdminPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { UserMenu } from './components/auth';
import { AdminPanelSettings } from '@mui/icons-material';

// Home page component
function Home() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-black flex items-center justify-center py-12 px-4">
      <div className="max-w-4xl w-full">
        {/* Central Card */}
        <div className="rounded-2xl shadow-2xl p-12">
          {/* Logo Block */}
          <div className="text-center mb-8">
            <div className="mb-8">
              <img
                src="/devshack.png"
                alt="DevShack Logo"
                className="mx-auto w-500 h-50 object-contain"
              />
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">Medical Translation System</h1>
            <p className="text-2xl text-gray-400 font-light">AI-powered medical communication</p>
            {isAuthenticated && user && (
              <p className="text-lg text-gray-500 mt-2">
                Welcome, {user.first_name || user.username}!
              </p>
            )}
          </div>
        </div>

        <div className="text-center space-y-4 mt-8">
          {!isAuthenticated ? (
            <div>
              <Link
                to="/login"
                className="inline-block bg-white text-black px-8 py-4 rounded-lg font-semibold hover:bg-gray-200 transition-colors text-lg"
              >
                Sign In →
              </Link>
            </div>
          ) : (
            <>
              <div>
                <Link
                  to="/translation-chat"
                  className="inline-block bg-white text-black px-8 py-4 rounded-lg font-semibold hover:bg-gray-200 transition-colors text-lg"
                >
                  Translation Chat →
                </Link>
              </div>
              {(user?.role === 'admin' || user?.is_superuser) && (
                <div>
                  <Link
                    to="/admin"
                    className="inline-flex items-center gap-2 bg-purple-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-purple-700 transition-colors text-lg"
                  >
                    <AdminPanelSettings />
                    Admin Panel →
                  </Link>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Header with user menu
function Header({ hide }: { hide?: boolean }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated || hide) return null;

  return (
    <header className="bg-black border-b border-gray-800 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-white font-bold text-lg">
            Medical Translation
          </Link>
          <nav className="flex items-center gap-4">
            <Link to="/translation-chat" className="text-gray-400 hover:text-white text-sm">
              Chat
            </Link>
            {(user?.role === 'admin' || user?.is_superuser) && (
              <Link
                to="/admin"
                className="flex items-center gap-1 text-gray-400 hover:text-white text-sm"
              >
                <AdminPanelSettings className="w-4 h-4" />
                Admin
              </Link>
            )}
          </nav>
        </div>
        <UserMenu />
      </div>
    </header>
  );
}

function AppContent() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const isAdminPage = location.pathname.startsWith('/admin');

  return (
    <div className="min-h-screen bg-black flex flex-col">
      <Header hide={isAdminPage} />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Home />
              ) : (
                <AuthPage onSuccess={() => (window.location.href = '/')} />
              )
            }
          />
          <Route path="/translation-chat" element={<TranslationChatPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;

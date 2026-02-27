import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) =>
    location.pathname.startsWith(path)
      ? 'bg-slate-700 text-white'
      : 'text-slate-300 hover:bg-slate-700 hover:text-white';

  return (
    <nav className="bg-slate-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <Link to="/upload" className="text-xl font-bold text-white tracking-tight">
              LogScanner
            </Link>
            <div className="flex space-x-1">
              <Link
                to="/upload"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/upload')}`}
              >
                Upload
              </Link>
              <Link
                to="/dashboard"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/dashboard')}`}
              >
                Dashboard
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-300">
              {user?.username}
            </span>
            <button
              onClick={logout}
              className="px-3 py-1.5 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

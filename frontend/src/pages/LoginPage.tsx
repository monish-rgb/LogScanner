import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate('/upload');
    } catch {
      // error is set in context
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">LogScanner</h1>
          <p className="text-slate-400 mt-2">SOC Analyst Log Analysis Platform</p>
        </div>
        <div className="bg-slate-800 rounded-lg shadow-xl p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Sign In</h2>
          {error && (
            <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded text-red-300 text-sm">
              {error}
              <button onClick={clearError} className="float-right text-red-400 hover:text-red-200">x</button>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your username"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your password"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-blue-400 hover:text-blue-300">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

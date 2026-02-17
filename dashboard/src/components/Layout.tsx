import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Shield, 
  LayoutDashboard, 
  MessageSquare, 
  Brain, 
  Settings, 
  LogOut,
  Activity,
  FileText
} from 'lucide-react';

const Layout: React.FC = () => {
  const { logout, tenant, tier } = useAuth();
  const location = useLocation();

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/analyze', icon: MessageSquare, label: 'Analyze' },
    { path: '/feedback', icon: FileText, label: 'Feedback' },
    { path: '/learning', icon: Brain, label: 'Active Learning' },
    { path: '/metrics', icon: Activity, label: 'Metrics' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen flex bg-dark-900 text-white">
      {/* Sidebar */}
      <aside className="w-64 glass border-r border-white/10 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-lg">Restrictor</h1>
              <p className="text-xs text-gray-400">v0.2.0</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'hover:bg-white/5 text-gray-400 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Info */}
        <div className="p-4 border-t border-white/10">
          <div className="glass rounded-xl p-4 mb-3">
            <p className="text-xs text-gray-400 mb-1">Tenant</p>
            <p className="font-semibold truncate">{tenant}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`px-2 py-0.5 rounded-full text-xs ${
                tier === 'enterprise' ? 'bg-purple-500/20 text-purple-400' :
                tier === 'pro' ? 'bg-blue-500/20 text-blue-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>
                {tier}
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-4 py-2 rounded-xl text-red-400 hover:bg-red-500/10 transition"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

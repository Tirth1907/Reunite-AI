import { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Heart, Home, FileText, Users, GitCompare, Smartphone, Menu, X, LogOut, User, Eye, Video } from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

export default function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Home', href: '/dashboard', icon: Home },
    { name: 'Register New Case', href: '/dashboard/register-case', icon: FileText },
    { name: 'All Cases', href: '/dashboard/all-cases', icon: Users },
    { name: 'Match Cases', href: '/dashboard/match-cases', icon: GitCompare },
    { name: 'Mobile App', href: '/dashboard/mobile-app', icon: Smartphone },
    { name: 'Public Sightings', href: '/dashboard/sightings', icon: Eye },
    { name: 'CCTV Analysis', href: '/dashboard/video-analysis', icon: Video },
  ];

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return location.pathname === href;
    }
    return location.pathname.startsWith(href);
  };

  const handleLogout = () => {
    logout(); // This clears localStorage
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full bg-white border-r border-gray-200 z-50 transform transition-transform duration-300 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } w-64`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <Link to="/" className="flex items-center gap-2">
              <Heart className="h-8 w-8" style={{ color: '#1e1b4b' }} />
              <span className="text-xl font-bold" style={{ color: '#1e1b4b' }}>Reunite AI</span>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${active
                    ? 'text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  style={active ? { backgroundColor: '#1e1b4b' } : {}}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3 mb-4 px-4 py-2">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: '#1e1b4b' }}>
                <User className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900">{user?.name || 'User'}</div>
                <div className="text-sm text-gray-500 capitalize">{user?.role || 'Member'}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <LogOut className="h-5 w-5" />
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Mobile Header */}
        <header className="lg:hidden bg-white border-b border-gray-200 sticky top-0 z-30">
          <div className="flex items-center justify-between p-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <Menu className="h-6 w-6 text-gray-600" />
            </button>
            <Link to="/" className="flex items-center gap-2">
              <Heart className="h-6 w-6" style={{ color: '#1e1b4b' }} />
              <span className="font-bold" style={{ color: '#1e1b4b' }}>Reunite AI</span>
            </Link>
            <div className="w-10" /> {/* Spacer for alignment */}
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

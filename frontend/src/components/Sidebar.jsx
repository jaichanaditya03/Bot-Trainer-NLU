import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Home, LayoutDashboard, Shield, LogOut, Clock } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { APP_CONFIG } from '../config/config';

export const Sidebar = () => {
  const { isAuthenticated, user, logout, loginTimestamp } = useAuthStore();
  const location = useLocation();
  const [sessionTime, setSessionTime] = useState('');

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  // Calculate remaining session time
  useEffect(() => {
    if (!isAuthenticated || !loginTimestamp) return;

    const updateTimer = () => {
      const now = Date.now();
      const elapsed = now - loginTimestamp;
      const twelveHoursInMs = 12 * 60 * 60 * 1000;
      const remaining = twelveHoursInMs - elapsed;

      if (remaining <= 0) {
        setSessionTime('Session expired');
        return;
      }

      const hours = Math.floor(remaining / (60 * 60 * 1000));
      const minutes = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
      
      setSessionTime(`${hours}h ${minutes}m remaining`);
    };

    updateTimer();
    const intervalId = setInterval(updateTimer, 60000); // Update every minute

    return () => clearInterval(intervalId);
  }, [isAuthenticated, loginTimestamp]);

  const navLinks = [
    { to: '/', label: 'Home', icon: Home, show: true },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, show: isAuthenticated },
    { to: '/admin', label: 'Admin Panel', icon: Shield, show: isAuthenticated && user?.is_admin },
  ];

  return (
    <aside className="w-64 h-screen sticky top-0 flex flex-col" style={{
      background: 'rgba(5, 15, 27, 0.78)',
      backdropFilter: 'blur(18px)',
      borderRight: '1px solid rgba(142, 228, 175, 0.18)'
    }}>
      {/* Logo */}
      <div className="p-6" style={{ borderBottom: '1px solid rgba(142, 228, 175, 0.18)' }}>
        <div className="flex items-center gap-3">
          <img src={APP_CONFIG.logo} alt="Logo" className="w-12 h-12" />
          <div>
            <h1 className="font-bold text-lg" style={{ color: '#f3fbff' }}>Bot Trainer</h1>
            <p className="text-xs" style={{ color: 'rgba(243, 251, 255, 0.6)' }}>v{APP_CONFIG.version}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navLinks.map((link) => 
            link.show ? (
              <Link
                key={link.to}
                to={link.to}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive(link.to)
                    ? ''
                    : ''
                }`}
                style={isActive(link.to) 
                  ? {
                      background: 'rgba(50, 244, 122, 0.22)',
                      color: '#f3fbff',
                      boxShadow: 'inset 0 0 0 1px rgba(50, 244, 122, 0.45)'
                    }
                  : {
                      color: '#f3fbff',
                      background: 'rgba(255, 255, 255, 0.04)'
                    }
                }
                onMouseEnter={(e) => {
                  if (!isActive(link.to)) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive(link.to)) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  }
                }}
              >
                <link.icon size={20} />
                <span className="font-medium">{link.label}</span>
              </Link>
            ) : null
          )}
        </div>
      </nav>

      {/* User Info & Logout */}
      {isAuthenticated && (
        <div className="p-4" style={{ borderTop: '1px solid rgba(142, 228, 175, 0.18)' }}>
          <div className="mb-3 px-2">
            <p className="text-sm font-medium" style={{ color: '#f3fbff' }}>{user?.username}</p>
            <p className="text-xs" style={{ color: 'rgba(243, 251, 255, 0.6)' }}>{user?.email}</p>
            {sessionTime && (
              <div className="flex items-center gap-1 mt-2 text-xs" style={{ color: 'rgba(50, 244, 122, 0.8)' }}>
                <Clock size={12} />
                <span>{sessionTime}</span>
              </div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium"
            style={{ 
              color: '#ff5757',
              background: 'rgba(255, 87, 87, 0.1)',
              border: '1px solid rgba(255, 87, 87, 0.2)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 87, 87, 0.2)';
              e.currentTarget.style.borderColor = 'rgba(255, 87, 87, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 87, 87, 0.1)';
              e.currentTarget.style.borderColor = 'rgba(255, 87, 87, 0.2)';
            }}
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      )}
    </aside>
  );
};

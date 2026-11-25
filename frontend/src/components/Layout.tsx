import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  PhoneCall,
  Calendar,
  Users,
  Briefcase,
  UserCheck,
  Clock,
  BookOpen,
  Bot,
  BarChart3,
  Settings,
  LogOut,
  Building2,
  Menu,
  X,
  Volume2,
  Activity,
  Sparkles,
  HelpCircle
} from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, organization, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/calls', label: 'Call Logs', icon: PhoneCall },
    { to: '/appointments', label: 'Appointments', icon: Calendar },
    { to: '/customers', label: 'Customers', icon: Users },
    { to: '/services', label: 'Services', icon: Briefcase },
    { to: '/staff', label: 'Staff', icon: UserCheck },
    { to: '/availability', label: 'Availability', icon: Clock },
    { to: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
    { to: '/voice-agent', label: 'Voice Agent', icon: Bot },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col md:flex-row text-slate-100">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-4 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
            <Volume2 className="w-5 h-5 text-emerald-400" />
          </div>
          <span className="font-bold text-lg text-white">VoiceDesk</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-slate-400 hover:text-white"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar Desktop */}
      <aside className={`
        ${mobileMenuOpen ? 'block' : 'hidden'} 
        md:flex flex-col w-full md:w-64 bg-slate-900/90 backdrop-blur-md border-r border-slate-800/80 p-4 shrink-0
      `}>
        {/* Brand */}
        <div className="hidden md:flex items-center gap-3 px-3 py-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-0.5 shadow-lg shadow-emerald-500/10">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center text-emerald-400">
              <Bot className="w-5 h-5 text-emerald-400 animate-pulse" />
            </div>
          </div>
          <div>
            <div className="font-extrabold text-base tracking-tight text-white flex items-center gap-1.5">
              VoiceDesk
              <span className="text-[10px] font-bold tracking-wider px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">AI</span>
            </div>
            <div className="text-xs text-slate-400 font-medium truncate max-w-[140px]">
              {organization?.name || 'Receptionist OS'}
            </div>
          </div>
        </div>

        {/* Tenant Scope Card */}
        <div className="mb-5 px-3 py-2.5 rounded-xl bg-slate-850/80 border border-slate-800 text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <Building2 className="w-3.5 h-3.5 text-emerald-400" />
              Tenant Scope
            </span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          </div>
          <div className="font-semibold text-slate-200 truncate">{organization?.name}</div>
          <div className="text-[11px] text-slate-400 truncate mt-0.5 font-mono">{organization?.timezone || 'Asia/Kolkata'}</div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to || (item.to !== '/' && location.pathname.startsWith(item.to));
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
                  ${isActive
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }
                `}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* User Card & Logout */}
        <div className="pt-4 mt-4 border-t border-slate-800">
          <div className="flex items-center justify-between px-3 py-2">
            <div className="truncate pr-2">
              <div className="text-sm font-medium text-slate-200 truncate">{user?.full_name}</div>
              <div className="text-xs text-slate-400 truncate">{user?.email}</div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-slate-950 overflow-y-auto">
        <header className="sticky top-0 z-20 h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-semibold text-slate-200">
              {navItems.find((n) => location.pathname === n.to || (n.to !== '/' && location.pathname.startsWith(n.to)))?.label || 'VoiceDesk'}
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              AI Voice Engine: Online
            </div>
          </div>
        </header>

        <div className="p-6 md:p-8 max-w-7xl w-full mx-auto space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import {
  Brain,
  Bell,
  LogOut,
  Menu,
  ChevronDown,
  Settings,
  BookOpen,
  CheckCircle2
} from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  currentUser: User | null;
  onOpenFormula?: () => void;
  onOpenProfile: () => void;
  onLogout: () => void;
  onToggleMobileSidebar?: () => void;
  onSearch?: (query: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  onOpenProfile,
  onLogout,
  onToggleMobileSidebar
}) => {
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const studentName = currentUser?.full_name || 'Student';
  const initial = studentName.charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#E2E8F0] shadow-[0_1px_3px_0_rgba(15,23,42,0.03)]">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-[68px] gap-4">
        {/* Left: Mobile Menu & Logo for small screens */}
        <div className="flex items-center space-x-3.5">
          {onToggleMobileSidebar && (
            <button
              onClick={onToggleMobileSidebar}
              className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition-colors cursor-pointer"
              title="Toggle Menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="flex items-center space-x-2 lg:hidden">
            <div className="p-2 bg-[#EA580C] rounded-xl text-white shadow-xs flex items-center justify-center">
              <Brain className="w-4 h-4" />
            </div>
            <span className="text-base font-bold text-slate-900 tracking-tight">
              OBEPath <span className="text-[#EA580C]">AI</span>
            </span>
          </div>
        </div>

        {/* Right Actions: Notification & Profile */}
        <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
          {/* Notification Icon */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => {
                setNotificationsOpen(!notificationsOpen);
                setProfileDropdownOpen(false);
              }}
              className="p-2.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-full transition-colors relative cursor-pointer"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-4 h-4 bg-orange-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center ring-2 ring-white">
                3
              </span>
            </button>

            {/* Notification Dropdown Popover */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white border border-[#E2E8F0] rounded-2xl shadow-lg p-3.5 z-50 animate-fadeIn space-y-2.5">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <span className="text-xs font-bold text-slate-900">Notifications</span>
                  <span className="text-[10px] text-[#EA580C] font-semibold cursor-pointer">Mark all as read</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="p-2.5 bg-[#FAF8F5] rounded-xl border border-slate-100 flex items-start space-x-2.5">
                    <div className="p-1 bg-emerald-50 text-emerald-600 rounded-md mt-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800">Learning Path updated</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">Queue Basics is ready for your next study session.</div>
                    </div>
                  </div>
                  <div className="p-2.5 bg-[#FAF8F5] rounded-xl border border-slate-100 flex items-start space-x-2.5">
                    <div className="p-1 bg-orange-50 text-[#EA580C] rounded-md mt-0.5">
                      <BookOpen className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800">Topic mastery synchronized</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">Stack Basics evaluated with real practice attempts.</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Student Avatar, Name, Small Student Label & Profile Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => {
                setProfileDropdownOpen(!profileDropdownOpen);
                setNotificationsOpen(false);
              }}
              className="flex items-center space-x-2.5 p-1.5 sm:px-3 sm:py-1.5 hover:bg-slate-50 border border-slate-200/80 rounded-xl transition-all cursor-pointer"
            >
              {/* Avatar circle with initial */}
              <div className="w-8 h-8 rounded-full bg-[#EA580C] text-white flex items-center justify-center font-bold text-xs shadow-xs">
                {initial}
              </div>

              {/* Name & Role Label */}
              <div className="hidden sm:block text-left">
                <div className="text-xs font-bold text-slate-900 leading-tight">
                  {studentName}
                </div>
                <div className="text-[10px] text-slate-400 font-medium capitalize">
                  {currentUser?.role || 'Student'}
                </div>
              </div>

              <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
            </button>

            {/* Profile Dropdown Menu */}
            {profileDropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white border border-[#E2E8F0] rounded-2xl shadow-lg p-2 z-50 animate-fadeIn space-y-1">
                <div className="p-2.5 border-b border-slate-100">
                  <div className="text-xs font-bold text-slate-900 truncate">{studentName}</div>
                  <div className="text-[11px] text-slate-400 truncate">{currentUser?.email || ''}</div>
                  <span className={`inline-block mt-1.5 px-2 py-0.5 border text-[10px] font-bold rounded-md capitalize ${
                    currentUser?.role === 'faculty'
                      ? 'bg-purple-50 text-purple-700 border-purple-200'
                      : currentUser?.role === 'admin'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-orange-50 text-[#EA580C] border-orange-200'
                  }`}>
                    {currentUser?.role || 'Student'}
                  </span>
                </div>

                <button
                  onClick={() => {
                    setProfileDropdownOpen(false);
                    onOpenProfile();
                  }}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer"
                >
                  <Settings className="w-3.5 h-3.5 text-slate-400" />
                  <span>Settings</span>
                </button>

                <div className="border-t border-slate-100 pt-1">
                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onLogout();
                    }}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5 text-rose-500" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

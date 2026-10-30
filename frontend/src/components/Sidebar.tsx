import {
  LayoutDashboard,
  Route,
  BookOpen,
  Network,
  Bot,
  FileCheck2,
  X,
  Settings,
  GraduationCap,
  Award,
  Megaphone,
  HelpCircle,
  Users
} from 'lucide-react';
import { UserRole } from '../types';

export type ActiveTab =
  | 'dashboard'
  | 'learning-path'
  | 'courses'
  | 'knowledge-map'
  | 'ai-tutor'
  | 'assessments'
  | 'skills'
  | 'resources'
  | 'class-hub'
  | 'class-resources'
  | 'announcements'
  | 'doubts'
  | 'settings';

interface SidebarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
  role?: UserRole;
  isAdapted?: boolean;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
  onOpenProfile?: () => void;
  openDoubtsCount?: number;
  unreadAnnouncementsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  role = 'student',
  mobileOpen = false,
  onCloseMobile,
  onOpenProfile,
  openDoubtsCount = 0,
  unreadAnnouncementsCount = 0
}) => {
  const studentNavItems: { id: ActiveTab; label: string; icon: any; badge?: number }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'class-hub', label: 'Class Hub', icon: Users, badge: unreadAnnouncementsCount },
    { id: 'learning-path', label: 'Learning Path', icon: Route },
    { id: 'courses', label: 'My Course', icon: BookOpen },
    { id: 'knowledge-map', label: 'Topic Map', icon: Network },
    { id: 'ai-tutor', label: 'AI Tutor', icon: Bot },
    { id: 'assessments', label: 'Assessments', icon: FileCheck2 },
    { id: 'skills', label: 'My Skills', icon: Award }
  ];

  const facultyNavItems: { id: ActiveTab; label: string; icon: any; badge?: number }[] = [
    { id: 'dashboard', label: 'Cohort Analytics', icon: LayoutDashboard },
    { id: 'class-resources', label: 'Class Resources', icon: BookOpen },
    { id: 'announcements', label: 'Announcements', icon: Megaphone },
    { id: 'doubts', label: 'Doubts', icon: HelpCircle, badge: openDoubtsCount }
  ];

  const adminNavItems: { id: ActiveTab; label: string; icon: any; badge?: number }[] = [
    { id: 'dashboard', label: 'System Telemetry', icon: LayoutDashboard }
  ];

  const navItems = role === 'faculty' ? facultyNavItems : role === 'admin' ? adminNavItems : studentNavItems;

  const handleSelect = (tab: ActiveTab) => {
    onSelectTab(tab);
    if (onCloseMobile) onCloseMobile();
  };

  const handleProfileClick = () => {
    if (onOpenProfile) {
      onOpenProfile();
    } else {
      onSelectTab('assessments');
    }
    if (onCloseMobile) onCloseMobile();
  };

  const content = (
    <div className="w-64 flex-shrink-0 bg-[#0F172A] border-r border-slate-800/80 flex flex-col justify-between p-4 h-full text-slate-300 select-none">
      <div className="space-y-6">
        {/* Brand Header */}
        <div className="flex items-center justify-between px-2 pt-2">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-[#EA580C] rounded-xl flex items-center justify-center text-white shadow-md shadow-orange-950/40">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <div className="text-base font-bold text-white tracking-tight flex items-center space-x-1">
                <span>OBEPath</span>
                <span className="text-orange-400">AI</span>
              </div>
              <div className="text-[10px] text-slate-400 font-medium tracking-wide">
                {role === 'faculty' ? 'Faculty Portal' : role === 'admin' ? 'Admin Console' : 'Learn • Adapt • Succeed'}
              </div>
            </div>
          </div>

          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5 pt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#EA580C] text-white shadow-md shadow-orange-950/30 font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/70 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span className="tracking-tight">{item.label}</span>
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isActive
                        ? 'bg-white text-orange-600'
                        : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Divider */}
        <hr className="border-t border-slate-800 my-2" />

        {/* Settings Navigation Item */}
        <div>
          <button
            onClick={() => handleSelect('settings')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'settings'
                ? 'bg-[#EA580C] text-white shadow-md shadow-orange-950/30 font-semibold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/70 border border-transparent'
            }`}
          >
            <Settings className={`w-4 h-4 ${activeTab === 'settings' ? 'text-white' : 'text-slate-400'}`} />
            <span className="tracking-tight">Profile & Settings</span>
          </button>
        </div>
      </div>

      {/* Role-Specific Inspiration / Info Card */}
      {role === 'student' && (
        <div className="bg-[#1E293B]/80 border border-slate-800 rounded-2xl p-4 text-white relative overflow-hidden shadow-inner mt-4">
          <div className="flex items-center space-x-1 text-emerald-400 mb-2">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c2.8 0 5.3-1.1 7.1-3 .2-.2.3-.5.2-.8-.8-3.4-3.6-6-7.1-6-1.5 0-3 .5-4.2 1.3" />
              <path d="M12 2c5.5 0 10 4.5 10 10 0 2.8-1.1 5.3-3 7.1-.2.2-.5.3-.8.2-3.4-.8-6-3.6-6-7.1 0-1.5.5-3 1.3-4.2" />
            </svg>
          </div>
          <p className="text-xs font-semibold text-slate-200 leading-snug">
            Small steps make big progress!
          </p>
        </div>
      )}

      {role === 'faculty' && (
        <div className="bg-[#1E293B]/80 border border-purple-900/40 rounded-2xl p-4 text-white relative overflow-hidden shadow-inner mt-4">
          <div className="text-[11px] font-bold text-purple-300 uppercase tracking-wider">Faculty Oversight</div>
          <p className="text-xs text-slate-300 mt-1">Autonomous outcome tracking & student intervention alerts.</p>
        </div>
      )}

      {role === 'admin' && (
        <div className="bg-[#1E293B]/80 border border-rose-900/40 rounded-2xl p-4 text-white relative overflow-hidden shadow-inner mt-4">
          <div className="text-[11px] font-bold text-rose-300 uppercase tracking-wider">Admin Console</div>
          <p className="text-xs text-slate-300 mt-1">Real-time system health & multi-agent telemetry.</p>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop fixed sidebar */}
      <aside className="hidden lg:block min-h-screen">
        {content}
      </aside>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs"
            onClick={onCloseMobile}
          />
          <div className="relative z-10 animate-slideRight h-full">
            {content}
          </div>
        </div>
      )}
    </>
  );
};

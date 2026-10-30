import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, ActiveTab } from './components/Sidebar';
import { KnowledgeMapVisualizer } from './components/KnowledgeMapVisualizer';

import { LandingPage } from './pages/LandingPage';
import { AuthModal } from './pages/AuthModal';
import { AuthLandingPage } from './pages/AuthLandingPage';
import { StudentOnboardingWizard, OnboardingData } from './pages/StudentOnboardingWizard';
import { AISkillCheckView } from './pages/AISkillCheckView';
import { StudentDashboard } from './pages/StudentDashboard';
import { CourseSelectionPage } from './pages/CourseSelectionPage';
import { AssessmentsMasterPage } from './pages/AssessmentsMasterPage';
import { LearningPathPage } from './pages/LearningPathPage';
import { TopicLearningPage } from './pages/TopicLearningPage';
import { AITutorPage } from './pages/AITutorPage';
import { ResourcesPage } from './pages/ResourcesPage';
import { SettingsPage } from './pages/SettingsPage';
import { OBEDashboardPage } from './pages/OBEDashboardPage';
import { FacultyDashboardPage } from './pages/FacultyDashboardPage';
import { FacultyClassResourcesPage } from './pages/FacultyClassResourcesPage';
import { FacultyAnnouncementsPage } from './pages/FacultyAnnouncementsPage';
import { FacultyDoubtsPage } from './pages/FacultyDoubtsPage';
import { StudentClassHubPage } from './pages/StudentClassHubPage';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AdminLoginPage } from './pages/AdminLoginPage';
import { LegalPage } from './pages/LegalPage';
import { ChangePasswordModal } from './components/ChangePasswordModal';

import {
  User,
  Course,
  AgentLog
} from './types';
import { api } from './services/api';
import { StudentLearningProvider, useStudentLearning } from './context/StudentLearningContext';

export const STUDENT_ONLY_ROUTES = [
  '/courses',
  '/my-course',
  '/learning-path',
  '/knowledge-map',
  '/topic-map',
  '/ai-tutor',
  '/assessments',
  '/skills',
  '/my-skills',
  '/resources',
  '/class-hub'
];

export const FACULTY_ONLY_ROUTES = [
  '/cohort-analytics',
  '/class-resources',
  '/announcements',
  '/doubts'
];

export const PATH_TO_TAB: Record<string, ActiveTab> = {
  '/': 'dashboard',
  '/dashboard': 'dashboard',
  '/cohort-analytics': 'dashboard',
  '/class-hub': 'class-hub',
  '/class-resources': 'class-resources',
  '/announcements': 'announcements',
  '/doubts': 'doubts',
  '/courses': 'courses',
  '/my-course': 'courses',
  '/learning-path': 'learning-path',
  '/knowledge-map': 'knowledge-map',
  '/topic-map': 'knowledge-map',
  '/ai-tutor': 'ai-tutor',
  '/assessments': 'assessments',
  '/skills': 'skills',
  '/my-skills': 'skills',
  '/resources': 'resources',
  '/settings': 'settings',
  '/profile': 'settings',
};

export const TAB_TO_PATH: Record<ActiveTab, string> = {
  dashboard: '/dashboard',
  'class-hub': '/class-hub',
  'class-resources': '/class-resources',
  announcements: '/announcements',
  doubts: '/doubts',
  courses: '/courses',
  'learning-path': '/learning-path',
  'knowledge-map': '/knowledge-map',
  'ai-tutor': '/ai-tutor',
  assessments: '/assessments',
  skills: '/skills',
  resources: '/resources',
  settings: '/settings',
};

const AppContent: React.FC<{
  currentUser: User;
  onLogout: () => void;
  currentPath?: string;
  onNavigatePath?: (path: string) => void;
}> = ({ currentUser, onLogout, currentPath = '/', onNavigatePath }) => {
  const {
    studentState,
    refreshStudentState,
    loading: studentStateLoading,
    setSelectedTopicForStudy,
    activeCourseId,
    setActiveCourseId
  } = useStudentLearning();

  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    return PATH_TO_TAB[currentPath] || 'dashboard';
  });
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);

  useEffect(() => {
    setSelectedTopicId(null);
  }, [activeCourseId]);

  useEffect(() => {
    const handlePopState = () => {
      if (typeof window === 'undefined') return;
      const pathname = window.location.pathname;
      if (FACULTY_ONLY_ROUTES.includes(pathname)) {
        window.history.replaceState({}, '', '/dashboard');
        setActiveTab('dashboard');
        if (onNavigatePath) onNavigatePath('/dashboard');
        return;
      }
      const tab = PATH_TO_TAB[pathname];
      if (tab) {
        setActiveTab(tab);
        setSelectedTopicId(null);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [onNavigatePath]);

  const handleTabSelect = (tab: ActiveTab) => {
    setActiveTab(tab);
    setSelectedTopicId(null);
    const targetPath = TAB_TO_PATH[tab] || '/dashboard';
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', targetPath);
    }
    if (onNavigatePath) onNavigatePath(targetPath);
  };

  const [courses, setCourses] = useState<Course[]>([]);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);

  useEffect(() => {
    loadAuxiliaryData();
  }, [currentUser]);

  const loadAuxiliaryData = async () => {
    try {
      const [coursesList, logsList] = await Promise.all([
        api.getCourses(),
        api.getAgentLogs(currentUser.id || 1, 15)
      ]);
      setCourses(coursesList);
      setAgentLogs(logsList);
    } catch (err) {
      console.error('Failed to load auxiliary courses/logs', err);
    }
  };

  const handleRefreshLogs = async () => {
    try {
      const logs = await api.getAgentLogs(currentUser.id || 1, 15);
      setAgentLogs(logs);
    } catch (err) {
      console.error('Logs refresh failed', err);
    }
  };

  const handleRefreshPath = async () => {
    try {
      await api.generateLearningPath(activeCourseId, currentUser.id || 1);
      await refreshStudentState();
      await handleRefreshLogs();
    } catch (err) {
      console.error('Path refresh failed', err);
    }
  };

  const isAdapted = studentState?.learningPath?.items.some((i) => i.is_remedial);

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex selection:bg-orange-100 selection:text-orange-900 h-screen overflow-hidden">
      {/* 1. Global Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleTabSelect}
        role="student"
        isAdapted={isAdapted}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        onOpenProfile={() => handleTabSelect('settings')}
      />

      {/* 2. Right Column: Navbar + Main Scrollable Content */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <Navbar
          currentUser={currentUser}
          onOpenProfile={() => handleTabSelect('settings')}
          onLogout={onLogout}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />

        {/* 3. Main Content View Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-[#F8FAFC]">
          <div className="max-w-[1400px] mx-auto">
            {/* If user is studying a specific topic module */}
            {selectedTopicId !== null ? (
              <TopicLearningPage
                key={`${activeCourseId}-${selectedTopicId}`}
                topicId={selectedTopicId}
                onBack={() => setSelectedTopicId(null)}
                onTopicCompleted={async () => {
                  await refreshStudentState();
                  await handleRefreshLogs();
                  setSelectedTopicId(null);
                  setActiveTab('learning-path');
                }}
                onPathAdapted={async () => {
                  await refreshStudentState();
                  await handleRefreshLogs();
                }}
                onNavigateToOBE={async () => {
                  await refreshStudentState();
                  setSelectedTopicId(null);
                  setActiveTab('learning-path');
                }}
                onNavigateToTutor={(tId) => {
                  setSelectedTopicId(null);
                  if (tId) setSelectedTopicForStudy(tId);
                  setActiveTab('ai-tutor');
                }}
                onNavigateToTopic={(tId) => {
                  setSelectedTopicId(tId);
                }}
                onNavigateToLearningPath={() => {
                  setSelectedTopicId(null);
                  setActiveTab('learning-path');
                }}
              />
            ) : (
              <>
                {/* Dashboard */}
                {activeTab === 'dashboard' && (
                  <StudentDashboard
                    key={`dash-${activeCourseId}`}
                    currentUser={currentUser}
                    onNavigate={(tab) => setActiveTab(tab)}
                    agentLogs={agentLogs}
                    onRefreshLogs={handleRefreshLogs}
                    onSelectTopic={(topicId) => setSelectedTopicId(topicId)}
                    courses={courses}
                  />
                )}

                {/* My Learning Path */}
                {activeTab === 'learning-path' && (
                  <LearningPathPage
                    key={`lp-${activeCourseId}`}
                    onSelectTopic={(topicId) => setSelectedTopicId(topicId)}
                    onRefreshPath={handleRefreshPath}
                    onNavigateToTutor={(topicId) => {
                      if (topicId) setSelectedTopicForStudy(topicId);
                      setActiveTab('ai-tutor');
                    }}
                  />
                )}

                {/* Courses & Outcomes */}
                {activeTab === 'courses' && (
                  <CourseSelectionPage
                    key={`courses-${activeCourseId}`}
                    courses={courses}
                    activeCourseId={studentState?.enrolledCourse?.id || activeCourseId}
                    onSelectCourse={async (course) => {
                      await setActiveCourseId(course.id);
                    }}
                    onNavigateProfile={() => setActiveTab('assessments')}
                    onSelectTopic={(topicId) => setSelectedTopicId(topicId)}
                  />
                )}

                {/* Knowledge Map */}
                {activeTab === 'knowledge-map' && (
                  <KnowledgeMapVisualizer
                    key={`km-${activeCourseId}`}
                    onSelectTopic={(topicId) => setSelectedTopicId(topicId)}
                    onNavigateToTutor={(topicId) => {
                      if (topicId) setSelectedTopicForStudy(topicId);
                      setActiveTab('ai-tutor');
                    }}
                    onNavigateToPractice={(topicId) => setSelectedTopicId(topicId)}
                  />
                )}

                {/* AI Tutor */}
                {activeTab === 'ai-tutor' && (
                  <AITutorPage
                    key={`tutor-${activeCourseId}`}
                    currentUser={currentUser}
                    onNavigateToAssessment={() => setActiveTab('assessments')}
                  />
                )}

                {/* Assessments Stepper */}
                {activeTab === 'assessments' && (
                  <AssessmentsMasterPage
                    key={`assessments-${activeCourseId}`}
                    onPathGenerated={() => {
                      setActiveTab('learning-path');
                    }}
                    onNavigateToKnowledgeMap={() => setActiveTab('knowledge-map')}
                    onNavigateToTutor={() => setActiveTab('ai-tutor')}
                  />
                )}

                {/* Class Hub */}
                {activeTab === 'class-hub' && (
                  <ErrorBoundary fallbackTitle="Class Hub Encountered an Error">
                    <StudentClassHubPage
                      onNavigateToDashboard={() => handleTabSelect('dashboard')}
                    />
                  </ErrorBoundary>
                )}

                {/* My Skills */}
                {activeTab === 'skills' && <OBEDashboardPage key={`obe-${activeCourseId}`} />}

                {/* Resources */}
                {activeTab === 'resources' && <ResourcesPage key={`res-${activeCourseId}`} />}

                {/* Settings */}
                {activeTab === 'settings' && <SettingsPage />}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

const FACULTY_VALID_TABS: ActiveTab[] = ['dashboard', 'class-resources', 'announcements', 'doubts', 'settings'];

const FacultyAppContent: React.FC<{
  currentUser: User;
  onLogout: () => void;
  currentPath?: string;
  onNavigatePath?: (path: string) => void;
}> = ({ currentUser, onLogout, currentPath = '/dashboard', onNavigatePath }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    const matched = PATH_TO_TAB[currentPath];
    return matched && FACULTY_VALID_TABS.includes(matched) ? matched : 'dashboard';
  });
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [openDoubtsCount, setOpenDoubtsCount] = useState<number>(0);

  // Guard: If student-only route or invalid tab is requested, redirect to Cohort Analytics
  useEffect(() => {
    if (!FACULTY_VALID_TABS.includes(activeTab)) {
      setActiveTab('dashboard');
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', '/dashboard');
      }
      if (onNavigatePath) onNavigatePath('/dashboard');
    }
  }, [activeTab, onNavigatePath]);

  // If faculty directly enters a student-only URL path, redirect to Cohort Analytics
  useEffect(() => {
    const checkAndRedirect = () => {
      if (typeof window === 'undefined') return;
      const pathname = window.location.pathname;
      if (STUDENT_ONLY_ROUTES.includes(pathname)) {
        window.history.replaceState({}, '', '/dashboard');
        setActiveTab('dashboard');
        if (onNavigatePath) onNavigatePath('/dashboard');
      } else {
        const tab = PATH_TO_TAB[pathname];
        if (tab && FACULTY_VALID_TABS.includes(tab)) {
          setActiveTab(tab);
        } else if (pathname === '/' || pathname === '/cohort-analytics' || pathname === '/dashboard') {
          setActiveTab('dashboard');
        }
      }
    };
    checkAndRedirect();
    window.addEventListener('popstate', checkAndRedirect);
    return () => window.removeEventListener('popstate', checkAndRedirect);
  }, [onNavigatePath]);

  const handleSelectTab = (tab: ActiveTab) => {
    const target = FACULTY_VALID_TABS.includes(tab) ? tab : 'dashboard';
    setActiveTab(target);
    const targetPath = TAB_TO_PATH[target] || '/dashboard';
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', targetPath);
    }
    if (onNavigatePath) onNavigatePath(targetPath);
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex selection:bg-purple-100 selection:text-purple-900 h-screen overflow-hidden">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        role="faculty"
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        onOpenProfile={() => handleSelectTab('settings')}
        openDoubtsCount={openDoubtsCount}
      />
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <Navbar
          currentUser={currentUser}
          onOpenProfile={() => handleSelectTab('settings')}
          onLogout={onLogout}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-[#F8FAFC]">
          <div className="max-w-[1400px] mx-auto">
            {activeTab === 'dashboard' && <FacultyDashboardPage />}
            {activeTab === 'class-resources' && (
              <ErrorBoundary fallbackTitle="Class Resources View Encountered an Error">
                <FacultyClassResourcesPage
                  initialClassId={selectedClassId}
                  onSelectClass={setSelectedClassId}
                />
              </ErrorBoundary>
            )}
            {activeTab === 'announcements' && (
              <ErrorBoundary fallbackTitle="Class Announcements View Encountered an Error">
                <FacultyAnnouncementsPage
                  initialClassId={selectedClassId}
                  onSelectClass={setSelectedClassId}
                />
              </ErrorBoundary>
            )}
            {activeTab === 'doubts' && (
              <ErrorBoundary fallbackTitle="Student Doubts View Encountered an Error">
                <FacultyDoubtsPage
                  initialClassId={selectedClassId}
                  onSelectClass={setSelectedClassId}
                  onOpenDoubtsCountChange={setOpenDoubtsCount}
                />
              </ErrorBoundary>
            )}
            {activeTab === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};

const AdminAppContent: React.FC<{
  currentUser: User;
  onLogout: () => void;
  currentPath?: string;
  onNavigatePath?: (path: string) => void;
}> = ({ currentUser, onLogout, currentPath = '/dashboard', onNavigatePath }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    return currentPath === '/settings' || currentPath === '/profile' ? 'settings' : 'dashboard';
  });
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);

  useEffect(() => {
    if (activeTab !== 'dashboard' && activeTab !== 'settings') {
      setActiveTab('dashboard');
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', '/dashboard');
      }
      if (onNavigatePath) onNavigatePath('/dashboard');
    }
  }, [activeTab, onNavigatePath]);

  useEffect(() => {
    const checkAndRedirect = () => {
      if (typeof window === 'undefined') return;
      const pathname = window.location.pathname;
      if (STUDENT_ONLY_ROUTES.includes(pathname)) {
        window.history.replaceState({}, '', '/dashboard');
        setActiveTab('dashboard');
        if (onNavigatePath) onNavigatePath('/dashboard');
      } else if (pathname === '/settings' || pathname === '/profile') {
        setActiveTab('settings');
      } else if (pathname === '/dashboard' || pathname === '/admin' || pathname === '/') {
        setActiveTab('dashboard');
      }
    };
    checkAndRedirect();
    window.addEventListener('popstate', checkAndRedirect);
    return () => window.removeEventListener('popstate', checkAndRedirect);
  }, [onNavigatePath]);

  const handleSelectTab = (tab: ActiveTab) => {
    if (tab === 'settings') {
      setActiveTab('settings');
      if (typeof window !== 'undefined') {
        window.history.pushState({}, '', '/settings');
      }
      if (onNavigatePath) onNavigatePath('/settings');
    } else {
      setActiveTab('dashboard');
      if (typeof window !== 'undefined') {
        window.history.pushState({}, '', '/dashboard');
      }
      if (onNavigatePath) onNavigatePath('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex selection:bg-rose-100 selection:text-rose-900 h-screen overflow-hidden">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        role="admin"
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        onOpenProfile={() => handleSelectTab('settings')}
      />
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <Navbar
          currentUser={currentUser}
          onOpenProfile={() => handleSelectTab('settings')}
          onLogout={onLogout}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-[#F8FAFC]">
          <div className="max-w-[1400px] mx-auto">
            {activeTab === 'dashboard' && <AdminDashboardPage />}
            {activeTab === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState<boolean>(() => {
    return typeof window !== 'undefined' && Boolean(localStorage.getItem('obepath_token'));
  });

  const [currentPath, setCurrentPath] = useState<string>(() => {
    return typeof window !== 'undefined' ? window.location.pathname : '/';
  });

  const [flowState, setFlowState] = useState<'dashboard' | 'onboarding' | 'skill-check'>(() => {
    const saved = localStorage.getItem('obepath_flow_state') as any;
    return saved || 'dashboard';
  });

  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(() => {
    const saved = localStorage.getItem('obepath_onboarding_data');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return null;
      }
    }
    return null;
  });

  // Verify session on startup using /api/auth/me
  useEffect(() => {
    let isMounted = true;

    const verifySession = async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('obepath_token') : null;
      if (!token) {
        if (isMounted) setAuthLoading(false);
        return;
      }

      try {
        const data = await api.getAuthMe();
        if (isMounted) {
          setCurrentUser(data.user);
          if (data.user.role === 'student') {
            if (!data.onboarding_completed) {
              setFlowState('onboarding');
            } else {
              setFlowState('dashboard');
            }
          } else {
            // Faculty and Admin MUST NEVER see student onboarding
            setFlowState('dashboard');
            localStorage.removeItem('obepath_flow_state');
          }
        }
      } catch (err) {
        console.warn('Failed to verify session via /api/auth/me:', err);
        if (typeof window !== 'undefined') {
          localStorage.removeItem('obepath_token');
          localStorage.removeItem('obepath_current_user');
        }
        if (isMounted) {
          setCurrentUser(null);
        }
      } finally {
        if (isMounted) {
          setAuthLoading(false);
        }
      }
    };

    verifySession();

    const handleUnauthorized = () => {
      if (isMounted) {
        setCurrentUser(null);
        setFlowState('dashboard');
        setOnboardingData(null);
      }
    };

    window.addEventListener('obepath_unauthorized', handleUnauthorized);

    const handleLocationChange = () => {
      if (typeof window !== 'undefined') {
        setCurrentPath(window.location.pathname);
      }
    };
    window.addEventListener('popstate', handleLocationChange);

    return () => {
      isMounted = false;
      window.removeEventListener('obepath_unauthorized', handleUnauthorized);
      window.removeEventListener('popstate', handleLocationChange);
    };
  }, []);

  // Guard: If faculty/admin lands on a student route, or student lands on a faculty route, redirect to /dashboard
  useEffect(() => {
    if (!currentUser) return;
    if (currentUser.role === 'faculty' || currentUser.role === 'admin') {
      if (STUDENT_ONLY_ROUTES.includes(currentPath)) {
        if (typeof window !== 'undefined') {
          window.history.replaceState({}, '', '/dashboard');
        }
        setCurrentPath('/dashboard');
      }
    } else if (currentUser.role === 'student') {
      if (FACULTY_ONLY_ROUTES.includes(currentPath)) {
        if (typeof window !== 'undefined') {
          window.history.replaceState({}, '', '/dashboard');
        }
        setCurrentPath('/dashboard');
      }
    }
  }, [currentUser, currentPath]);

  const handleAuthSuccess = (user: User, isNewUser = false, onboardingCompleted = false) => {
    setCurrentUser(user);

    if (user.role === 'student' && (isNewUser || !onboardingCompleted)) {
      setFlowState('onboarding');
      localStorage.setItem('obepath_flow_state', 'onboarding');
    } else {
      setFlowState('dashboard');
      localStorage.setItem('obepath_flow_state', 'dashboard');
    }
  };

  const handleOnboardingComplete = (data: OnboardingData) => {
    setOnboardingData(data);
    localStorage.setItem('obepath_onboarding_data', JSON.stringify(data));
    setFlowState('skill-check');
    localStorage.setItem('obepath_flow_state', 'skill-check');
  };

  const handleSkillCheckComplete = () => {
    setFlowState('dashboard');
    localStorage.setItem('obepath_flow_state', 'dashboard');
    localStorage.setItem('obepath_onboarding_completed', 'true');
    localStorage.removeItem('obepath_onboarding_draft');
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setFlowState('dashboard');
    setOnboardingData(null);
    localStorage.removeItem('obepath_flow_state');
    localStorage.removeItem('obepath_onboarding_data');
    localStorage.removeItem('obepath_onboarding_draft');
    localStorage.removeItem('obepath_onboarding_completed');
  };

  // Loading spinner while verifying JWT token with /api/auth/me
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex flex-col items-center justify-center p-6 space-y-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-400 animate-spin flex items-center justify-center p-0.5 shadow-lg shadow-orange-500/20">
            <div className="w-full h-full bg-white rounded-2xl flex items-center justify-center">
              <div className="w-4 h-4 rounded-full bg-orange-500 animate-ping" />
            </div>
          </div>
        </div>
        <div className="text-center">
          <h2 className="text-sm font-bold text-slate-800 tracking-tight">Verifying OBEPath Session</h2>
          <p className="text-xs text-slate-400 mt-1">Authenticating secure token with server...</p>
        </div>
      </div>
    );
  }

  // Admin Portal Route (/admin-login)
  if (currentPath === '/admin-login' && (!currentUser || currentUser.role !== 'admin')) {
    return (
      <AdminLoginPage
        onAuthSuccess={handleAuthSuccess}
        onNavigateHome={() => {
          if (typeof window !== 'undefined') {
            window.history.pushState({}, '', '/');
            setCurrentPath('/');
          }
        }}
      />
    );
  }

  // Legal Pages: Privacy Policy & Terms of Service (/privacy, /terms)
  if (currentPath === '/privacy' || currentPath === '/terms') {
    return (
      <LegalPage
        type={currentPath === '/privacy' ? 'privacy' : 'terms'}
        onNavigateHome={() => {
          if (typeof window !== 'undefined') {
            window.history.pushState({}, '', '/');
            setCurrentPath('/');
          }
        }}
        onSwitchType={(newType) => {
          const path = `/${newType}`;
          if (typeof window !== 'undefined') {
            window.history.pushState({}, '', path);
            setCurrentPath(path);
          }
        }}
      />
    );
  }

  // If user is not authenticated, display the split-screen AuthLandingPage
  if (!currentUser) {
    return <AuthLandingPage onAuthSuccess={handleAuthSuccess} />;
  }

  // Faculty role routing - Faculty Dashboard & authorized features
  if (currentUser.role === 'faculty') {
    return (
      <>
        <FacultyAppContent
          currentUser={currentUser}
          onLogout={handleLogout}
          currentPath={currentPath}
          onNavigatePath={setCurrentPath}
        />
        {currentUser.must_change_password && (
          <ChangePasswordModal
            isOpen={true}
            userEmail={currentUser.email}
            onSuccess={() => {
              setCurrentUser(prev => prev ? { ...prev, must_change_password: false } : null);
            }}
            onLogout={handleLogout}
          />
        )}
      </>
    );
  }

  // Admin role routing - Administrator Telemetry & Console
  if (currentUser.role === 'admin') {
    return (
      <>
        <AdminAppContent
          currentUser={currentUser}
          onLogout={handleLogout}
          currentPath={currentPath}
          onNavigatePath={setCurrentPath}
        />
        {currentUser.must_change_password && (
          <ChangePasswordModal
            isOpen={true}
            userEmail={currentUser.email}
            onSuccess={() => {
              setCurrentUser(prev => prev ? { ...prev, must_change_password: false } : null);
            }}
            onLogout={handleLogout}
          />
        )}
      </>
    );
  }

  // First-time student onboarding wizard
  if (flowState === 'onboarding') {
    return (
      <>
        <StudentOnboardingWizard
          currentUser={currentUser}
          onComplete={handleOnboardingComplete}
          onSkipToDashboard={() => {
            setFlowState('dashboard');
            localStorage.setItem('obepath_flow_state', 'dashboard');
          }}
        />
        {currentUser.must_change_password && (
          <ChangePasswordModal
            isOpen={true}
            userEmail={currentUser.email}
            onSuccess={() => {
              setCurrentUser(prev => prev ? { ...prev, must_change_password: false } : null);
            }}
            onLogout={handleLogout}
          />
        )}
      </>
    );
  }

  // Friendly AI Skill Check
  if (flowState === 'skill-check') {
    return (
      <AISkillCheckView
        currentUser={currentUser}
        onboardingData={onboardingData}
        onCompleteToDashboard={handleSkillCheckComplete}
      />
    );
  }

  // Returning user / Onboarded student learning interface
  return (
    <>
      <StudentLearningProvider currentUser={currentUser}>
        <AppContent
          currentUser={currentUser}
          onLogout={handleLogout}
          currentPath={currentPath}
          onNavigatePath={setCurrentPath}
        />
      </StudentLearningProvider>
      {currentUser.must_change_password && (
        <ChangePasswordModal
          isOpen={true}
          userEmail={currentUser.email}
          onSuccess={() => {
            setCurrentUser(prev => prev ? { ...prev, must_change_password: false } : null);
          }}
          onLogout={handleLogout}
        />
      )}
    </>
  );
};

export default App;

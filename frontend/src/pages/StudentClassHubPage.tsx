import React, { useState, useEffect } from 'react';
import {
  Users,
  Megaphone,
  BookOpen,
  HelpCircle,
  Pin,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Plus,
  Send,
  Lock,
  Globe,
  Clock,
  Calendar,
  Layers,
  ChevronRight,
  ShieldCheck,
  Check
} from 'lucide-react';
import { api } from '../services/api';
import {
  StudentEnrolledClass,
  ClassAnnouncement,
  ClassResource,
  ClassDoubt,
  DoubtVisibility,
  ClassResourceType,
  Topic
} from '../types';

interface StudentClassHubPageProps {
  initialClassId?: number | null;
  onNavigateToDashboard?: () => void;
  onUnreadCountChange?: (count: number) => void;
}

export const StudentClassHubPage: React.FC<StudentClassHubPageProps> = ({
  initialClassId,
  onNavigateToDashboard,
  onUnreadCountChange
}) => {
  const [classes, setClasses] = useState<StudentEnrolledClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(initialClassId || null);
  const [classesLoading, setClassesLoading] = useState(true);
  const [classesError, setClassesError] = useState<string | null>(null);

  // Active sub-tab
  const [activeSubTab, setActiveSubTab] = useState<'announcements' | 'resources' | 'doubts'>('announcements');

  // Announcements state
  const [announcements, setAnnouncements] = useState<ClassAnnouncement[]>([]);
  const [announcementsLoading, setAnnouncementsLoading] = useState(false);
  const [announcementsError, setAnnouncementsError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [markingReadId, setMarkingReadId] = useState<number | null>(null);

  // Resources state
  const [resources, setResources] = useState<ClassResource[]>([]);
  const [resourcesLoading, setResourcesLoading] = useState(false);
  const [resourcesError, setResourcesError] = useState<string | null>(null);
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('all');

  // Doubts state
  const [doubts, setDoubts] = useState<ClassDoubt[]>([]);
  const [doubtsLoading, setDoubtsLoading] = useState(false);
  const [doubtsError, setDoubtsError] = useState<string | null>(null);
  const [doubtViewTab, setDoubtViewTab] = useState<'my' | 'class'>('my');

  // Course topics for doubt creation
  const [courseTopics, setCourseTopics] = useState<Topic[]>([]);

  // Ask Doubt Form
  const [showAskModal, setShowAskModal] = useState(false);
  const [doubtTitle, setDoubtTitle] = useState('');
  const [doubtBody, setDoubtBody] = useState('');
  const [doubtTopicId, setDoubtTopicId] = useState<number | ''>('');
  const [doubtVisibility, setDoubtVisibility] = useState<DoubtVisibility>('private');
  const [askSubmitting, setAskSubmitting] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  useEffect(() => {
    loadEnrolledClasses();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      loadAnnouncements(selectedClassId);
      loadResources(selectedClassId);
      loadDoubts(selectedClassId);
      loadTopicsForClass(selectedClassId);
    } else {
      setAnnouncements([]);
      setResources([]);
      setDoubts([]);
      setCourseTopics([]);
    }
  }, [selectedClassId]);

  const loadEnrolledClasses = async () => {
    try {
      setClassesLoading(true);
      setClassesError(null);
      const data = await api.getStudentClasses();
      setClasses(data);
      if (data.length > 0 && !selectedClassId) {
        setSelectedClassId(data[0].class_id);
      }
    } catch (err: any) {
      setClassesError(err?.message || 'Failed to load your enrolled classes.');
    } finally {
      setClassesLoading(false);
    }
  };

  const loadTopicsForClass = async (classId: number) => {
    try {
      const cls = classes.find((c) => c.class_id === classId);
      if (cls?.course_id) {
        const courseData = await api.getCourse(cls.course_id);
        setCourseTopics(courseData.topics || []);
      }
    } catch (err) {
      console.warn('Failed to load topics for course', err);
    }
  };

  const loadAnnouncements = async (classId: number) => {
    try {
      setAnnouncementsLoading(true);
      setAnnouncementsError(null);
      const [annData, countData] = await Promise.all([
        api.getStudentClassAnnouncements(classId),
        api.getStudentUnreadAnnouncementsCount(classId)
      ]);
      setAnnouncements(annData);
      setUnreadCount(countData.unread_count);
      if (onUnreadCountChange) {
        onUnreadCountChange(countData.unread_count);
      }
    } catch (err: any) {
      setAnnouncementsError(err?.message || 'Failed to load announcements.');
    } finally {
      setAnnouncementsLoading(false);
    }
  };

  const loadResources = async (classId: number) => {
    try {
      setResourcesLoading(true);
      setResourcesError(null);
      const data = await api.getStudentClassResources(classId);
      setResources(data);
    } catch (err: any) {
      setResourcesError(err?.message || 'Failed to load class resources.');
    } finally {
      setResourcesLoading(false);
    }
  };

  const loadDoubts = async (classId: number) => {
    try {
      setDoubtsLoading(true);
      setDoubtsError(null);
      const data = await api.getStudentClassDoubts(classId);
      setDoubts(data);
    } catch (err: any) {
      setDoubtsError(err?.message || 'Failed to load doubts.');
    } finally {
      setDoubtsLoading(false);
    }
  };

  const handleMarkAsRead = async (announcementId: number) => {
    if (!selectedClassId) return;
    try {
      setMarkingReadId(announcementId);
      await api.markStudentAnnouncementRead(selectedClassId, announcementId);
      setAnnouncements((prev) =>
        prev.map((a) => (a.id === announcementId ? { ...a, is_read: true } : a))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
      if (onUnreadCountChange) {
        onUnreadCountChange(Math.max(0, unreadCount - 1));
      }
    } catch (err: any) {
      console.error('Failed to mark announcement as read', err);
    } finally {
      setMarkingReadId(null);
    }
  };

  const handleOpenAskModal = () => {
    setDoubtTitle('');
    setDoubtBody('');
    setDoubtTopicId('');
    setDoubtVisibility('private');
    setAskError(null);
    setShowAskModal(true);
  };

  const handleAskDoubtSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId) return;

    const trimmedTitle = doubtTitle.trim();
    const trimmedBody = doubtBody.trim();

    if (!trimmedTitle) {
      setAskError('Question title is required.');
      return;
    }
    if (trimmedTitle.length > 150) {
      setAskError('Title must not exceed 150 characters.');
      return;
    }
    if (!trimmedBody) {
      setAskError('Question details are required.');
      return;
    }
    if (trimmedBody.length > 2000) {
      setAskError('Question details must not exceed 2,000 characters.');
      return;
    }

    try {
      setAskSubmitting(true);
      setAskError(null);
      await api.askStudentClassDoubt(selectedClassId, {
        title: trimmedTitle,
        body: trimmedBody,
        topic_id: doubtTopicId === '' ? null : Number(doubtTopicId),
        visibility: doubtVisibility
      });
      setShowAskModal(false);
      setFeedbackMsg('Your doubt has been submitted to your instructor.');
      setTimeout(() => setFeedbackMsg(null), 3500);
      loadDoubts(selectedClassId);
    } catch (err: any) {
      setAskError(err?.message || 'Failed to submit doubt. Please check your daily/hourly limits.');
    } finally {
      setAskSubmitting(false);
    }
  };

  const selectedClass = classes.find((c) => c.class_id === selectedClassId);

  const filteredResources = resources.filter((r) => {
    if (resourceTypeFilter !== 'all' && r.resource_type !== resourceTypeFilter) return false;
    return true;
  });

  const myDoubtsList = doubts.filter((d) => d.is_my_doubt);
  const classDoubtsList = doubts.filter((d) => d.visibility === 'class');
  const displayedDoubts = doubtViewTab === 'my' ? myDoubtsList : classDoubtsList;

  const getTypeBadgeStyle = (type: ClassResourceType) => {
    switch (type) {
      case 'video':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'article':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'notes':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'practice':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-orange-600 uppercase tracking-wider mb-1">
            <Users className="w-4 h-4" />
            <span>Class Community & Resources</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Class Hub</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Stay aligned with instructor announcements, verified reference links, and 1-on-1 academic doubts.
          </p>
        </div>

        {/* Class Selector Dropdown */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">My Class:</label>
          <select
            value={selectedClassId || ''}
            onChange={(e) => setSelectedClassId(Number(e.target.value))}
            disabled={classesLoading || classes.length === 0}
            className="px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all cursor-pointer min-w-[220px]"
          >
            {classes.length === 0 && <option value="">Not enrolled in any class</option>}
            {classes.map((c) => (
              <option key={c.class_id} value={c.class_id}>
                {c.name} ({c.course_code || 'Course'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedbackMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-sm font-medium animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{feedbackMsg}</span>
        </div>
      )}

      {/* Loading Classes */}
      {classesLoading && (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
          <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-500">Checking your active class enrollments...</p>
        </div>
      )}

      {/* Error Loading Classes */}
      {classesError && (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{classesError}</span>
        </div>
      )}

      {/* Empty State: Not Enrolled in Any Active Class */}
      {!classesLoading && !classesError && classes.length === 0 && (
        <div className="p-12 text-center bg-white rounded-2xl border border-dashed border-slate-300 space-y-3">
          <Layers className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No Active Class Enrolled</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            You are not currently enrolled in any active classes. Enter a 6-character class code from your instructor
            on the main Dashboard to unlock class announcements, resources, and doubts.
          </p>
          {onNavigateToDashboard && (
            <button
              onClick={onNavigateToDashboard}
              className="mt-2 px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold shadow-xs transition-colors cursor-pointer inline-flex items-center space-x-1.5"
            >
              <span>Go to Dashboard to Join Class</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Active Class Hub Content */}
      {selectedClass && (
        <div className="space-y-6">
          {/* Class Info Card */}
          <div className="bg-linear-to-r from-orange-500/10 via-amber-500/5 to-transparent border border-orange-200/80 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="text-xs font-bold text-orange-700 uppercase tracking-wider">Enrolled Class</div>
              <h2 className="text-lg font-bold text-slate-900">{selectedClass.name}</h2>
              <p className="text-xs text-slate-600">
                Course: <span className="font-semibold text-slate-800">{selectedClass.course_title}</span> • Instructor:{' '}
                <span className="font-semibold text-slate-800">{selectedClass.teacher_name}</span>
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold px-3 py-1 bg-white border border-orange-200 rounded-full text-orange-800 shadow-2xs">
                Active Member
              </span>
            </div>
          </div>

          {/* Sub-Tab Navigation Bar */}
          <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => setActiveSubTab('announcements')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center space-x-2 cursor-pointer ${
                activeSubTab === 'announcements'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Megaphone className="w-4 h-4" />
              <span>Announcements</span>
              {unreadCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
              )}
            </button>

            <button
              onClick={() => setActiveSubTab('resources')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center space-x-2 cursor-pointer ${
                activeSubTab === 'resources'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Resources ({resources.length})</span>
            </button>

            <button
              onClick={() => setActiveSubTab('doubts')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center space-x-2 cursor-pointer ${
                activeSubTab === 'doubts'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>Doubts & Inquiries</span>
            </button>
          </div>

          {/* 1. ANNOUNCEMENTS TAB */}
          {activeSubTab === 'announcements' && (
            <div className="space-y-4">
              {unreadCount > 0 && (
                <div className="p-3 bg-orange-50 border border-orange-200 rounded-xl text-xs text-orange-800 flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
                  <span>You have {unreadCount} unread announcement{unreadCount === 1 ? '' : 's'} in this class.</span>
                </div>
              )}

              {announcementsLoading && (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-slate-500">Checking announcements...</p>
                </div>
              )}

              {announcementsError && (
                <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                  <span>{announcementsError}</span>
                </div>
              )}

              {!announcementsLoading && !announcementsError && announcements.length === 0 && (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <Megaphone className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <h3 className="text-sm font-bold text-slate-800">No Announcements Yet</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Your instructor has not posted any announcements for this class.
                  </p>
                </div>
              )}

              {!announcementsLoading && !announcementsError && announcements.length > 0 && (
                <div className="space-y-4">
                  {announcements.map((ann) => (
                    <div
                      key={ann.id}
                      className={`bg-white rounded-2xl p-6 border transition-all ${
                        ann.pinned
                          ? 'border-orange-300 shadow-sm bg-linear-to-r from-orange-50/20 to-white'
                          : 'border-slate-200 shadow-xs'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                            {!ann.is_read && (
                              <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-orange-500 text-white">
                                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                                <span>Unread</span>
                              </span>
                            )}
                            {ann.pinned && (
                              <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-orange-100 text-orange-800 border border-orange-200">
                                <Pin className="w-3 h-3 text-orange-600" />
                                <span>Pinned</span>
                              </span>
                            )}
                            <span className="inline-flex items-center space-x-1 text-slate-400 text-xs">
                              <Calendar className="w-3.5 h-3.5" />
                              <span>{new Date(ann.created_at).toLocaleDateString()}</span>
                            </span>
                            <span className="inline-flex items-center space-x-1 text-slate-400 text-xs">
                              <Clock className="w-3.5 h-3.5" />
                              <span>{new Date(ann.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </span>
                          </div>

                          <h3 className="text-lg font-bold text-slate-900 leading-snug">{ann.title}</h3>
                          <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed font-sans">
                            {ann.body}
                          </p>
                        </div>

                        {!ann.is_read && (
                          <button
                            onClick={() => handleMarkAsRead(ann.id)}
                            disabled={markingReadId === ann.id}
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors cursor-pointer shrink-0 flex items-center space-x-1"
                          >
                            {markingReadId === ann.id ? (
                              <RefreshCw className="w-3.5 h-3.5 animate-spin text-orange-600" />
                            ) : (
                              <Check className="w-3.5 h-3.5" />
                            )}
                            <span>Mark Read</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 2. RESOURCES TAB */}
          {activeSubTab === 'resources' && (
            <div className="space-y-4">
              {/* Type Filter */}
              <div className="flex items-center space-x-2 bg-white p-3 rounded-xl border border-slate-200">
                <span className="text-xs font-semibold text-slate-500">Filter Type:</span>
                <div className="flex flex-wrap gap-1.5">
                  {(['all', 'video', 'article', 'notes', 'practice', 'other'] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setResourceTypeFilter(t)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                        resourceTypeFilter === t
                          ? 'bg-slate-900 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {resourcesLoading && (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-slate-500">Loading resources...</p>
                </div>
              )}

              {resourcesError && (
                <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                  <span>{resourcesError}</span>
                </div>
              )}

              {!resourcesLoading && !resourcesError && filteredResources.length === 0 && (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <h3 className="text-sm font-bold text-slate-800">No Resources Available</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Your instructor has not added reference materials under this category yet.
                  </p>
                </div>
              )}

              {!resourcesLoading && !resourcesError && filteredResources.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredResources.map((res) => (
                    <div
                      key={res.id}
                      className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                          <span
                            className={`inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full border ${getTypeBadgeStyle(
                              res.resource_type
                            )}`}
                          >
                            <span className="capitalize">{res.resource_type}</span>
                          </span>
                          {res.topic_title && (
                            <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                              Topic: {res.topic_title}
                            </span>
                          )}
                        </div>

                        <h3 className="text-base font-bold text-slate-900 leading-snug">{res.title}</h3>
                        {res.description && (
                          <p className="text-xs text-slate-600 whitespace-pre-wrap leading-relaxed">
                            {res.description}
                          </p>
                        )}
                      </div>

                      <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        <span className="text-[11px] text-slate-400">
                          Added on {new Date(res.created_at).toLocaleDateString()}
                        </span>

                        <a
                          href={res.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 font-bold text-orange-600 hover:text-orange-700 bg-orange-50 hover:bg-orange-100 px-3 py-1.5 rounded-lg transition-colors"
                          title="Opens an external site"
                        >
                          <span>Open Resource</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span className="text-[10px] font-normal text-orange-500 ml-1">(Opens an external site)</span>
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 3. DOUBTS & INQUIRIES TAB */}
          {activeSubTab === 'doubts' && (
            <div className="space-y-4">
              {/* Header with Ask Doubt Button */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setDoubtViewTab('my')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      doubtViewTab === 'my'
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    My Doubts ({myDoubtsList.length})
                  </button>
                  <button
                    onClick={() => setDoubtViewTab('class')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      doubtViewTab === 'class'
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Class Questions ({classDoubtsList.length})
                  </button>
                </div>

                <button
                  onClick={handleOpenAskModal}
                  className="px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer self-start sm:self-auto"
                >
                  <Plus className="w-4 h-4" />
                  <span>Ask a Doubt</span>
                </button>
              </div>

              {doubtsLoading && (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-slate-500">Loading doubts...</p>
                </div>
              )}

              {doubtsError && (
                <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                  <span>{doubtsError}</span>
                </div>
              )}

              {!doubtsLoading && !doubtsError && displayedDoubts.length === 0 && (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <HelpCircle className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <h3 className="text-sm font-bold text-slate-800">
                    {doubtViewTab === 'my' ? 'You Have Not Asked Any Doubts' : 'No Public Class Questions'}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    {doubtViewTab === 'my'
                      ? 'Have a question about a concept or assignment? Ask your instructor directly.'
                      : 'Classmates have not posted any public questions in this class yet.'}
                  </p>
                  {doubtViewTab === 'my' && (
                    <button
                      onClick={handleOpenAskModal}
                      className="mt-4 px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold shadow-xs transition-colors cursor-pointer"
                    >
                      Ask Question
                    </button>
                  )}
                </div>
              )}

              {!doubtsLoading && !doubtsError && displayedDoubts.length > 0 && (
                <div className="space-y-4">
                  {displayedDoubts.map((d) => (
                    <div
                      key={d.id}
                      className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4"
                    >
                      {/* Doubt Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                          {d.status === 'open' && (
                            <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                              <span>Waiting for Instructor</span>
                            </span>
                          )}
                          {d.status === 'answered' && (
                            <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>Answered</span>
                            </span>
                          )}
                          {d.status === 'closed' && (
                            <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                              <span>Closed</span>
                            </span>
                          )}

                          {d.visibility === 'private' ? (
                            <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                              <Lock className="w-3 h-3 text-slate-500" />
                              <span>Private</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-full border border-sky-200">
                              <Globe className="w-3 h-3 text-sky-600" />
                              <span>Class Question</span>
                            </span>
                          )}

                          {d.topic_title && (
                            <span className="text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                              Topic: {d.topic_title}
                            </span>
                          )}

                          <span className="text-xs text-slate-500">
                            Asked by <span className="font-bold text-slate-800">{d.author_name}</span>
                          </span>

                          <span className="text-xs text-slate-400">
                            • {new Date(d.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      {/* Doubt Body */}
                      <div>
                        <h3 className="text-base font-bold text-slate-900">{d.title}</h3>
                        <p className="text-sm text-slate-700 mt-1 whitespace-pre-wrap leading-relaxed font-sans">
                          {d.body}
                        </p>
                      </div>

                      {/* Instructor Replies */}
                      {d.replies && d.replies.length > 0 && (
                        <div className="space-y-2.5 pt-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                            Instructor Response ({d.replies.length})
                          </h4>
                          {d.replies.map((reply) => (
                            <div
                              key={reply.id}
                              className="bg-orange-50/40 border border-orange-200/60 rounded-xl p-4 space-y-1.5"
                            >
                              <div className="flex items-center space-x-2">
                                <span className="text-xs font-bold text-orange-700 bg-orange-100 px-2 py-0.5 rounded-md">
                                  {reply.author_name} (Instructor)
                                </span>
                                <span className="text-[11px] text-slate-400">
                                  {new Date(reply.created_at).toLocaleString()}
                                </span>
                              </div>
                              <p className="text-xs text-slate-800 whitespace-pre-wrap leading-relaxed font-sans">
                                {reply.body}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      {(!d.replies || d.replies.length === 0) && (
                        <p className="text-xs text-slate-400 italic">
                          No replies yet. Your instructor has been notified.
                        </p>
                      )}

                      {/* Notice that students cannot reply to doubts */}
                      <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                        Only course instructors can reply to inquiries in this version.
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Ask Doubt Modal */}
      {showAskModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <HelpCircle className="w-5 h-5 text-orange-600" />
                <h3 className="text-base font-bold text-slate-900">Ask a Question</h3>
              </div>
              <button
                onClick={() => setShowAskModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {askError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{askError}</span>
              </div>
            )}

            <form onSubmit={handleAskDoubtSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Title / Subject <span className="text-rose-500">*</span>
                  <span className="font-normal text-slate-400 ml-1">({doubtTitle.length}/150)</span>
                </label>
                <input
                  type="text"
                  maxLength={150}
                  required
                  placeholder="e.g., Confusion about recursion base case in tree traversal"
                  value={doubtTitle}
                  onChange={(e) => setDoubtTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Topic (Optional)</label>
                <select
                  value={doubtTopicId}
                  onChange={(e) => setDoubtTopicId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 cursor-pointer"
                >
                  <option value="">General Course Inquiry</option>
                  {courseTopics.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Question Details <span className="text-rose-500">*</span>
                  <span className="font-normal text-slate-400 ml-1">({doubtBody.length}/2000)</span>
                </label>
                <textarea
                  rows={4}
                  maxLength={2000}
                  required
                  placeholder="Describe where you are stuck, steps you attempted, or specific questions."
                  value={doubtBody}
                  onChange={(e) => setDoubtBody(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 font-sans"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Visibility</label>
                <div className="grid grid-cols-2 gap-2">
                  <label
                    className={`flex items-start space-x-2 p-3 rounded-xl border cursor-pointer transition-all ${
                      doubtVisibility === 'private'
                        ? 'border-orange-500 bg-orange-50/40 text-orange-950 font-semibold'
                        : 'border-slate-200 bg-slate-50 text-slate-700'
                    }`}
                  >
                    <input
                      type="radio"
                      name="doubtVisibility"
                      checked={doubtVisibility === 'private'}
                      onChange={() => setDoubtVisibility('private')}
                      className="mt-0.5 text-orange-600"
                    />
                    <div>
                      <div className="flex items-center space-x-1">
                        <Lock className="w-3.5 h-3.5 text-slate-500" />
                        <span>Private (Default)</span>
                      </div>
                      <p className="text-[11px] font-normal text-slate-500 mt-0.5">
                        Only your instructor can read and reply.
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-start space-x-2 p-3 rounded-xl border cursor-pointer transition-all ${
                      doubtVisibility === 'class'
                        ? 'border-orange-500 bg-orange-50/40 text-orange-950 font-semibold'
                        : 'border-slate-200 bg-slate-50 text-slate-700'
                    }`}
                  >
                    <input
                      type="radio"
                      name="doubtVisibility"
                      checked={doubtVisibility === 'class'}
                      onChange={() => setDoubtVisibility('class')}
                      className="mt-0.5 text-orange-600"
                    />
                    <div>
                      <div className="flex items-center space-x-1">
                        <Globe className="w-3.5 h-3.5 text-sky-600" />
                        <span>Class Visible</span>
                      </div>
                      <p className="text-[11px] font-normal text-slate-500 mt-0.5">
                        Classmates can read (your first name only is shown).
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-500 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Rate limit: max 5 doubts per hour, 20 per day. Plain text only.</span>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAskModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-xl font-bold cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={askSubmitting}
                  className="px-5 py-2 bg-[#EA580C] hover:bg-orange-600 disabled:opacity-50 text-white rounded-xl font-bold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
                >
                  {askSubmitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>{askSubmitting ? 'Submitting...' : 'Submit Question'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

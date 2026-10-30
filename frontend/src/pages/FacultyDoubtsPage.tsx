import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  MessageSquare,
  Lock,
  Globe,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Trash2,
  Send,
  Check,
  User,
  Clock,
  Layers,
  Filter
} from 'lucide-react';
import { api } from '../services/api';
import { ClassInfo, ClassDoubt, ClassDoubtReply, Topic } from '../types';

interface FacultyDoubtsPageProps {
  initialClassId?: number | null;
  onSelectClass?: (classId: number) => void;
  onOpenDoubtsCountChange?: (count: number) => void;
}

export const FacultyDoubtsPage: React.FC<FacultyDoubtsPageProps> = ({
  initialClassId,
  onSelectClass,
  onOpenDoubtsCountChange
}) => {
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(initialClassId || null);
  const [classesLoading, setClassesLoading] = useState(true);
  const [classesError, setClassesError] = useState<string | null>(null);

  const [doubts, setDoubts] = useState<ClassDoubt[]>([]);
  const [doubtsLoading, setDoubtsLoading] = useState(false);
  const [doubtsError, setDoubtsError] = useState<string | null>(null);

  // Topics for filter
  const [courseTopics, setCourseTopics] = useState<Topic[]>([]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'answered' | 'closed'>('all');
  const [topicFilter, setTopicFilter] = useState<number | 'all'>('all');

  // Reply state per doubt
  const [replyTextMap, setReplyTextMap] = useState<Record<number, string>>({});
  const [replyingId, setReplyingId] = useState<number | null>(null);
  const [replyErrorMap, setReplyErrorMap] = useState<Record<number, string>>({});

  // Close doubt state
  const [closingId, setClosingId] = useState<number | null>(null);

  // Delete reply confirmation
  const [replyToDelete, setReplyToDelete] = useState<{ doubtId: number; reply: ClassDoubtReply } | null>(null);
  const [deletingReply, setDeletingReply] = useState(false);

  // Feedback banner
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  useEffect(() => {
    loadClasses();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      loadDoubts(selectedClassId);
      loadTopicsForClass(selectedClassId);
      if (onSelectClass) onSelectClass(selectedClassId);
    } else {
      setDoubts([]);
      setCourseTopics([]);
    }
  }, [selectedClassId, statusFilter, topicFilter]);

  const loadClasses = async () => {
    try {
      setClassesLoading(true);
      setClassesError(null);
      const data = await api.getFacultyClasses();
      setClasses(data);
      if (data.length > 0 && !selectedClassId) {
        setSelectedClassId(data[0].id);
      }
    } catch (err: any) {
      setClassesError(err?.message || 'Failed to load classes.');
    } finally {
      setClassesLoading(false);
    }
  };

  const loadTopicsForClass = async (classId: number) => {
    try {
      const cls = classes.find((c) => c.id === classId);
      if (cls?.course_id) {
        const courseData = await api.getCourse(cls.course_id);
        setCourseTopics(courseData.topics || []);
      }
    } catch (err) {
      console.warn('Failed to load topics for course', err);
    }
  };

  const loadDoubts = async (classId: number) => {
    try {
      setDoubtsLoading(true);
      setDoubtsError(null);
      const statusParam = statusFilter === 'all' ? undefined : statusFilter;
      const topicParam = topicFilter === 'all' ? undefined : Number(topicFilter);
      const data = await api.getFacultyClassDoubts(classId, statusParam, topicParam);
      setDoubts(data);

      const openCount = data.filter((d) => d.status === 'open').length;
      if (onOpenDoubtsCountChange) {
        onOpenDoubtsCountChange(openCount);
      }
    } catch (err: any) {
      setDoubtsError(err?.message || 'Failed to load doubts.');
    } finally {
      setDoubtsLoading(false);
    }
  };

  const handleReplyChange = (doubtId: number, text: string) => {
    setReplyTextMap((prev) => ({ ...prev, [doubtId]: text }));
    if (replyErrorMap[doubtId]) {
      setReplyErrorMap((prev) => {
        const next = { ...prev };
        delete next[doubtId];
        return next;
      });
    }
  };

  const handleSubmitReply = async (doubtId: number) => {
    if (!selectedClassId) return;
    const body = (replyTextMap[doubtId] || '').trim();
    if (!body) {
      setReplyErrorMap((prev) => ({ ...prev, [doubtId]: 'Reply body cannot be empty.' }));
      return;
    }
    if (body.length > 2000) {
      setReplyErrorMap((prev) => ({ ...prev, [doubtId]: 'Reply must not exceed 2,000 characters.' }));
      return;
    }

    try {
      setReplyingId(doubtId);
      await api.replyToFacultyClassDoubt(selectedClassId, doubtId, body);
      setReplyTextMap((prev) => ({ ...prev, [doubtId]: '' }));
      setFeedbackMsg('Reply submitted!');
      setTimeout(() => setFeedbackMsg(null), 3000);
      loadDoubts(selectedClassId);
    } catch (err: any) {
      setReplyErrorMap((prev) => ({ ...prev, [doubtId]: err?.message || 'Failed to submit reply.' }));
    } finally {
      setReplyingId(null);
    }
  };

  const handleCloseDoubt = async (doubtId: number) => {
    if (!selectedClassId) return;
    try {
      setClosingId(doubtId);
      await api.closeFacultyClassDoubt(selectedClassId, doubtId);
      setFeedbackMsg('Doubt marked as closed.');
      setTimeout(() => setFeedbackMsg(null), 3000);
      loadDoubts(selectedClassId);
    } catch (err: any) {
      alert(err?.message || 'Failed to close doubt.');
    } finally {
      setClosingId(null);
    }
  };

  const handleDeleteReply = async () => {
    if (!selectedClassId || !replyToDelete) return;
    try {
      setDeletingReply(true);
      await api.deleteFacultyClassDoubtReply(selectedClassId, replyToDelete.doubtId, replyToDelete.reply.id);
      setReplyToDelete(null);
      setFeedbackMsg('Inappropriate reply removed.');
      setTimeout(() => setFeedbackMsg(null), 3000);
      loadDoubts(selectedClassId);
    } catch (err: any) {
      alert(err?.message || 'Failed to delete reply.');
    } finally {
      setDeletingReply(false);
    }
  };

  const selectedClass = classes.find((c) => c.id === selectedClassId);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span>Open</span>
          </span>
        );
      case 'answered':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>Answered</span>
          </span>
        );
      case 'closed':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            <Check className="w-3 h-3 text-slate-500" />
            <span>Closed</span>
          </span>
        );
      default:
        return null;
    }
  };

  const openCount = doubts.filter((d) => d.status === 'open').length;

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-orange-600 uppercase tracking-wider mb-1">
            <HelpCircle className="w-4 h-4" />
            <span>Academic Support & Q&A</span>
          </div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Student Doubts</h1>
            {openCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full bg-orange-100 text-orange-800 text-xs font-bold border border-orange-200">
                {openCount} unresolved
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Resolve student misconceptions, answer private queries, and moderate public class inquiries.
          </p>
        </div>

        {/* Class Selector */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Class:</label>
          <select
            value={selectedClassId || ''}
            onChange={(e) => setSelectedClassId(Number(e.target.value))}
            disabled={classesLoading || classes.length === 0}
            className="px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all cursor-pointer min-w-[200px]"
          >
            {classes.length === 0 && <option value="">No classes available</option>}
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.course_code || 'Course'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Success Notification */}
      {feedbackMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-sm font-medium animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{feedbackMsg}</span>
        </div>
      )}

      {/* Classes Loading / Error */}
      {classesLoading && (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
          <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-500">Loading your classes...</p>
        </div>
      )}

      {classesError && (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{classesError}</span>
        </div>
      )}

      {/* No Classes Empty State */}
      {!classesLoading && !classesError && classes.length === 0 && (
        <div className="p-12 text-center bg-white rounded-2xl border border-dashed border-slate-300">
          <Layers className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Classes Found</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
            Create a class in Cohort Analytics before reviewing student doubts.
          </p>
        </div>
      )}

      {/* Main Content Area */}
      {selectedClass && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
            {/* Status Filter */}
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-500">Status:</span>
              <div className="flex flex-wrap gap-1">
                {(['all', 'open', 'answered', 'closed'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                      statusFilter === s
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Topic Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <label className="text-xs font-semibold text-slate-500">Topic:</label>
              <select
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
                className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20"
              >
                <option value="all">All Topics</option>
                {courseTopics.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Doubts Loading */}
          {doubtsLoading && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
              <p className="text-sm text-slate-500">Loading student doubts...</p>
            </div>
          )}

          {/* Doubts Error */}
          {doubtsError && (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                <span>{doubtsError}</span>
              </div>
              <button
                onClick={() => loadDoubts(selectedClass.id)}
                className="px-3 py-1 bg-white border border-rose-300 rounded-lg text-xs font-bold text-rose-700 hover:bg-rose-100 cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {/* Empty State */}
          {!doubtsLoading && !doubtsError && doubts.length === 0 && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <MessageSquare className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">No Doubts Found</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                No questions have been submitted under the selected status/topic filter for this class.
              </p>
            </div>
          )}

          {/* Doubts Threads */}
          {!doubtsLoading && !doubtsError && doubts.length > 0 && (
            <div className="space-y-4">
              {doubts.map((d) => (
                <div
                  key={d.id}
                  className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4"
                >
                  {/* Doubt Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                    <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                      {getStatusBadge(d.status)}

                      {d.visibility === 'private' ? (
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                          <Lock className="w-3 h-3 text-slate-500" />
                          <span>Private to Faculty</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-full border border-sky-200">
                          <Globe className="w-3 h-3 text-sky-600" />
                          <span>Class Visible</span>
                        </span>
                      )}

                      {d.topic_title && (
                        <span className="text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                          Topic: {d.topic_title}
                        </span>
                      )}

                      <span className="text-xs font-bold text-slate-700 flex items-center space-x-1">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>{d.author_name}</span>
                      </span>

                      <span className="text-xs text-slate-400 flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(d.created_at).toLocaleString()}</span>
                      </span>
                    </div>

                    {d.status !== 'closed' && (
                      <button
                        onClick={() => handleCloseDoubt(d.id)}
                        disabled={closingId === d.id}
                        className="text-xs font-semibold text-slate-500 hover:text-slate-800 px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer self-start sm:self-auto shrink-0 flex items-center space-x-1"
                      >
                        {closingId === d.id && <RefreshCw className="w-3 h-3 animate-spin" />}
                        <span>Close Doubt</span>
                      </button>
                    )}
                  </div>

                  {/* Doubt Content */}
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{d.title}</h3>
                    <p className="text-sm text-slate-700 mt-1 whitespace-pre-wrap leading-relaxed">
                      {d.body}
                    </p>
                  </div>

                  {/* Replies Thread */}
                  {d.replies && d.replies.length > 0 && (
                    <div className="space-y-2.5 pt-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Instructor Responses ({d.replies.length})
                      </h4>
                      {d.replies.map((reply) => (
                        <div
                          key={reply.id}
                          className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-bold text-orange-600 bg-orange-100 px-2 py-0.5 rounded-md">
                                {reply.author_name}
                              </span>
                              <span className="text-[11px] text-slate-400">
                                {new Date(reply.created_at).toLocaleString()}
                              </span>
                            </div>

                            <button
                              onClick={() => setReplyToDelete({ doubtId: d.id, reply })}
                              className="text-slate-400 hover:text-rose-600 p-1 rounded-md hover:bg-rose-50 transition-colors cursor-pointer"
                              title="Delete reply"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <p className="text-xs text-slate-800 whitespace-pre-wrap leading-relaxed font-sans">
                            {reply.body}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reply Form */}
                  <div className="pt-3 border-t border-slate-100 space-y-2">
                    {replyErrorMap[d.id] && (
                      <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center space-x-1.5">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{replyErrorMap[d.id]}</span>
                      </div>
                    )}

                    <div className="flex items-start space-x-2">
                      <textarea
                        rows={2}
                        maxLength={2000}
                        placeholder={
                          d.status === 'closed'
                            ? 'Doubt is closed. Re-opening with a reply...'
                            : 'Write instructor response to student (plain text)...'
                        }
                        value={replyTextMap[d.id] || ''}
                        onChange={(e) => handleReplyChange(d.id, e.target.value)}
                        className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 font-sans"
                      />

                      <button
                        onClick={() => handleSubmitReply(d.id)}
                        disabled={replyingId === d.id || !(replyTextMap[d.id] || '').trim()}
                        className="px-4 py-2 bg-[#EA580C] hover:bg-orange-600 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer shrink-0 mt-0.5"
                      >
                        {replyingId === d.id ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Send className="w-3.5 h-3.5" />
                        )}
                        <span>Reply</span>
                      </button>
                    </div>
                    <div className="text-[10px] text-slate-400 text-right pr-1">
                      {(replyTextMap[d.id] || '').length}/2000 characters
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Delete Reply Confirmation Modal */}
      {replyToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <div className="p-2 bg-rose-100 rounded-xl">
                <Trash2 className="w-5 h-5 text-rose-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Delete Response</h3>
                <p className="text-xs text-slate-500">Soft delete with audit trail</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to remove this reply? It will be immediately withdrawn from student view and recorded in audit logs.
            </p>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
              <button
                type="button"
                onClick={() => setReplyToDelete(null)}
                disabled={deletingReply}
                className="px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-xl text-xs font-bold cursor-pointer transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteReply}
                disabled={deletingReply}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
              >
                {deletingReply && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>{deletingReply ? 'Deleting...' : 'Confirm Delete'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

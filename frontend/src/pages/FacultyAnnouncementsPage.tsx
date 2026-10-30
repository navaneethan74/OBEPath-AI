import React, { useState, useEffect } from 'react';
import {
  Megaphone,
  Plus,
  Trash2,
  Pin,
  PinOff,
  AlertCircle,
  RefreshCw,
  X,
  CheckCircle2,
  Layers,
  Search,
  Calendar,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import { ClassInfo, ClassAnnouncement } from '../types';

interface FacultyAnnouncementsPageProps {
  initialClassId?: number | null;
  onSelectClass?: (classId: number) => void;
}

export const FacultyAnnouncementsPage: React.FC<FacultyAnnouncementsPageProps> = ({
  initialClassId,
  onSelectClass
}) => {
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(initialClassId || null);
  const [classesLoading, setClassesLoading] = useState(true);
  const [classesError, setClassesError] = useState<string | null>(null);

  const [announcements, setAnnouncements] = useState<ClassAnnouncement[]>([]);
  const [announcementsLoading, setAnnouncementsLoading] = useState(false);
  const [announcementsError, setAnnouncementsError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');

  // Add Announcement Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [pinned, setPinned] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Pin toggling loader
  const [pinningId, setPinningId] = useState<number | null>(null);

  // Delete Confirmation Modal
  const [announcementToDelete, setAnnouncementToDelete] = useState<ClassAnnouncement | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadClasses();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      loadAnnouncements(selectedClassId);
      if (onSelectClass) onSelectClass(selectedClassId);
    } else {
      setAnnouncements([]);
    }
  }, [selectedClassId]);

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

  const loadAnnouncements = async (classId: number) => {
    try {
      setAnnouncementsLoading(true);
      setAnnouncementsError(null);
      const data = await api.getFacultyClassAnnouncements(classId);
      setAnnouncements(data);
    } catch (err: any) {
      setAnnouncementsError(err?.message || 'Failed to load announcements.');
    } finally {
      setAnnouncementsLoading(false);
    }
  };

  const handleOpenAddModal = () => {
    setTitle('');
    setBody('');
    setPinned(false);
    setFormError(null);
    setShowAddModal(true);
  };

  const handleCreateAnnouncement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId) return;

    const trimmedTitle = title.trim();
    const trimmedBody = body.trim();

    if (!trimmedTitle) {
      setFormError('Announcement title is required.');
      return;
    }
    if (trimmedTitle.length > 150) {
      setFormError('Title must not exceed 150 characters.');
      return;
    }
    if (!trimmedBody) {
      setFormError('Announcement message body is required.');
      return;
    }
    if (trimmedBody.length > 2000) {
      setFormError('Message body must not exceed 2,000 characters.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      await api.createFacultyClassAnnouncement(selectedClassId, {
        title: trimmedTitle,
        body: trimmedBody,
        pinned
      });
      setShowAddModal(false);
      setSuccessMsg('Announcement published to class!');
      setTimeout(() => setSuccessMsg(null), 3000);
      loadAnnouncements(selectedClassId);
    } catch (err: any) {
      setFormError(err?.message || 'Failed to publish announcement.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTogglePin = async (announcement: ClassAnnouncement) => {
    if (!selectedClassId) return;
    try {
      setPinningId(announcement.id);
      await api.togglePinClassAnnouncement(selectedClassId, announcement.id);
      loadAnnouncements(selectedClassId);
    } catch (err: any) {
      alert(err?.message || 'Failed to toggle pin state.');
    } finally {
      setPinningId(null);
    }
  };

  const handleDeleteAnnouncement = async () => {
    if (!selectedClassId || !announcementToDelete) return;
    try {
      setDeleting(true);
      await api.deleteFacultyClassAnnouncement(selectedClassId, announcementToDelete.id);
      setAnnouncementToDelete(null);
      setSuccessMsg('Announcement deleted.');
      setTimeout(() => setSuccessMsg(null), 3000);
      loadAnnouncements(selectedClassId);
    } catch (err: any) {
      alert(err?.message || 'Failed to delete announcement.');
    } finally {
      setDeleting(false);
    }
  };

  const selectedClass = classes.find((c) => c.id === selectedClassId);

  const filteredAnnouncements = announcements.filter((a) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return a.title.toLowerCase().includes(q) || a.body.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-orange-600 uppercase tracking-wider mb-1">
            <Megaphone className="w-4 h-4" />
            <span>Class Broadcasts & Updates</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Announcements</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Broadcast important updates, schedule changes, exam reminders, and milestones to all enrolled students.
          </p>
        </div>

        {/* Class Selector & Action Button */}
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

          {selectedClass && (
            <button
              onClick={handleOpenAddModal}
              className="px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-sm font-semibold shadow-xs transition-all flex items-center space-x-1.5 cursor-pointer whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              <span>New Announcement</span>
            </button>
          )}
        </div>
      </div>

      {/* Success Notification */}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-sm font-medium animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
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
            You do not currently manage any active classes. Create a class from Cohort Analytics first.
          </p>
        </div>
      )}

      {/* Main Content Area */}
      {selectedClass && (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="flex items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
            <div className="text-xs font-semibold text-slate-500">
              Showing {filteredAnnouncements.length} announcement{filteredAnnouncements.length === 1 ? '' : 's'}
            </div>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search announcements..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 w-full sm:w-64"
              />
            </div>
          </div>

          {/* Announcements Loading */}
          {announcementsLoading && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
              <p className="text-sm text-slate-500">Loading announcements for {selectedClass.name}...</p>
            </div>
          )}

          {/* Error Banner */}
          {announcementsError && (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                <span>{announcementsError}</span>
              </div>
              <button
                onClick={() => loadAnnouncements(selectedClass.id)}
                className="px-3 py-1 bg-white border border-rose-300 rounded-lg text-xs font-bold text-rose-700 hover:bg-rose-100 cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {/* Empty State */}
          {!announcementsLoading && !announcementsError && filteredAnnouncements.length === 0 && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <Megaphone className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">
                {announcements.length === 0 ? 'No Announcements Yet' : 'No matching announcements'}
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                {announcements.length === 0
                  ? 'Keep your students informed with important course announcements and exam schedules.'
                  : 'Try adjusting your search keywords.'}
              </p>
              {announcements.length === 0 && (
                <button
                  onClick={handleOpenAddModal}
                  className="mt-4 px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold shadow-xs transition-colors cursor-pointer"
                >
                  Post First Announcement
                </button>
              )}
            </div>
          )}

          {/* Announcements Feed */}
          {!announcementsLoading && !announcementsError && filteredAnnouncements.length > 0 && (
            <div className="space-y-4">
              {filteredAnnouncements.map((ann) => (
                <div
                  key={ann.id}
                  className={`bg-white rounded-2xl p-6 border transition-all ${
                    ann.pinned
                      ? 'border-orange-300 shadow-sm bg-linear-to-r from-orange-50/20 to-white'
                      : 'border-slate-200 shadow-xs hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        {ann.pinned && (
                          <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-orange-100 text-orange-800 border border-orange-200">
                            <Pin className="w-3 h-3 text-orange-600" />
                            <span>Pinned Announcement</span>
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
                      <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                        {ann.body}
                      </p>
                    </div>

                    {/* Actions: Pin / Delete */}
                    <div className="flex items-center space-x-1 shrink-0">
                      <button
                        onClick={() => handleTogglePin(ann)}
                        disabled={pinningId === ann.id}
                        className={`p-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer flex items-center space-x-1 ${
                          ann.pinned
                            ? 'bg-orange-100 text-orange-800 hover:bg-orange-200'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                        title={ann.pinned ? 'Unpin announcement' : 'Pin to top of class'}
                      >
                        {pinningId === ann.id ? (
                          <RefreshCw className="w-4 h-4 animate-spin text-orange-600" />
                        ) : ann.pinned ? (
                          <PinOff className="w-4 h-4" />
                        ) : (
                          <Pin className="w-4 h-4" />
                        )}
                        <span className="hidden sm:inline">{ann.pinned ? 'Unpin' : 'Pin'}</span>
                      </button>

                      <button
                        onClick={() => setAnnouncementToDelete(ann)}
                        className="p-2 text-slate-400 hover:text-rose-600 rounded-xl hover:bg-rose-50 transition-colors cursor-pointer"
                        title="Delete announcement"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Announcement Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Megaphone className="w-5 h-5 text-orange-600" />
                <h3 className="text-base font-bold text-slate-900">Post Class Announcement</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateAnnouncement} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Title <span className="text-rose-500">*</span>
                  <span className="font-normal text-slate-400 ml-1">({title.length}/150)</span>
                </label>
                <input
                  type="text"
                  maxLength={150}
                  required
                  placeholder="e.g., Midterm Project Submission Deadline Extension"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Message Body <span className="text-rose-500">*</span>
                  <span className="font-normal text-slate-400 ml-1">({body.length}/2000)</span>
                </label>
                <textarea
                  rows={5}
                  maxLength={2000}
                  required
                  placeholder="Write clear instructions or information for your class. Formatting newlines are preserved."
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 font-sans"
                />
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="pinCheckbox"
                  checked={pinned}
                  onChange={(e) => setPinned(e.target.checked)}
                  className="w-4 h-4 text-orange-600 rounded-sm border-slate-300 focus:ring-orange-500 cursor-pointer"
                />
                <label htmlFor="pinCheckbox" className="font-semibold text-slate-700 cursor-pointer">
                  Pin this announcement to top of students' feed
                </label>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-xl font-bold cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 bg-[#EA580C] hover:bg-orange-600 disabled:opacity-50 text-white rounded-xl font-bold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
                >
                  {submitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>{submitting ? 'Publishing...' : 'Publish Announcement'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {announcementToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <div className="p-2 bg-rose-100 rounded-xl">
                <Trash2 className="w-5 h-5 text-rose-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Delete Announcement</h3>
                <p className="text-xs text-slate-500">Soft delete with audit trail</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to delete <span className="font-bold text-slate-900">"{announcementToDelete.title}"</span>?
              It will be immediately removed from student view.
            </p>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
              <button
                type="button"
                onClick={() => setAnnouncementToDelete(null)}
                disabled={deleting}
                className="px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-xl text-xs font-bold cursor-pointer transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAnnouncement}
                disabled={deleting}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
              >
                {deleting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>{deleting ? 'Deleting...' : 'Confirm Delete'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

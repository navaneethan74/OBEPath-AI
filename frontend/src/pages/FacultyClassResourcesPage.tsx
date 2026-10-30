import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Plus,
  Trash2,
  ExternalLink,
  Video,
  FileText,
  Code2,
  Globe,
  AlertCircle,
  RefreshCw,
  X,
  CheckCircle2,
  Layers,
  Search
} from 'lucide-react';
import { api } from '../services/api';
import { ClassInfo, ClassResource, ClassResourceType, Course, Topic } from '../types';

interface FacultyClassResourcesPageProps {
  initialClassId?: number | null;
  onSelectClass?: (classId: number) => void;
}

export const FacultyClassResourcesPage: React.FC<FacultyClassResourcesPageProps> = ({
  initialClassId,
  onSelectClass
}) => {
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(initialClassId || null);
  const [classesLoading, setClassesLoading] = useState(true);
  const [classesError, setClassesError] = useState<string | null>(null);

  const [resources, setResources] = useState<ClassResource[]>([]);
  const [resourcesLoading, setResourcesLoading] = useState(false);
  const [resourcesError, setResourcesError] = useState<string | null>(null);

  // Topics for the selected class's course
  const [courseTopics, setCourseTopics] = useState<Topic[]>([]);

  // Filter
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Add Resource Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [resourceType, setResourceType] = useState<ClassResourceType>('article');
  const [topicId, setTopicId] = useState<number | ''>('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Delete Confirmation Modal
  const [resourceToDelete, setResourceToDelete] = useState<ClassResource | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadClasses();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      loadResources(selectedClassId);
      loadTopicsForClass(selectedClassId);
      if (onSelectClass) onSelectClass(selectedClassId);
    } else {
      setResources([]);
      setCourseTopics([]);
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

  const loadResources = async (classId: number) => {
    try {
      setResourcesLoading(true);
      setResourcesError(null);
      const data = await api.getFacultyClassResources(classId);
      setResources(data);
    } catch (err: any) {
      setResourcesError(err?.message || 'Failed to load class resources.');
    } finally {
      setResourcesLoading(false);
    }
  };

  const handleOpenAddModal = () => {
    setTitle('');
    setUrl('');
    setResourceType('article');
    setTopicId('');
    setDescription('');
    setFormError(null);
    setShowAddModal(true);
  };

  const validateUrl = (rawUrl: string): boolean => {
    try {
      const parsed = new URL(rawUrl);
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId) return;

    const trimmedTitle = title.trim();
    const trimmedUrl = url.trim();

    if (!trimmedTitle) {
      setFormError('Resource title is required.');
      return;
    }
    if (trimmedTitle.length > 150) {
      setFormError('Title must not exceed 150 characters.');
      return;
    }
    if (!trimmedUrl) {
      setFormError('URL is required.');
      return;
    }
    if (trimmedUrl.length > 500) {
      setFormError('URL must not exceed 500 characters.');
      return;
    }
    if (!validateUrl(trimmedUrl)) {
      setFormError('Invalid URL. Only http:// and https:// web addresses are accepted.');
      return;
    }
    if (description.trim().length > 2000) {
      setFormError('Description must not exceed 2,000 characters.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      await api.createFacultyClassResource(selectedClassId, {
        title: trimmedTitle,
        url: trimmedUrl,
        resource_type: resourceType,
        topic_id: topicId === '' ? null : Number(topicId),
        description: description.trim() || undefined
      });
      setShowAddModal(false);
      setSuccessMsg('Resource added successfully!');
      setTimeout(() => setSuccessMsg(null), 3000);
      loadResources(selectedClassId);
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create resource.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteResource = async () => {
    if (!selectedClassId || !resourceToDelete) return;
    try {
      setDeleting(true);
      await api.deleteFacultyClassResource(selectedClassId, resourceToDelete.id);
      setResourceToDelete(null);
      setSuccessMsg('Resource deleted.');
      setTimeout(() => setSuccessMsg(null), 3000);
      loadResources(selectedClassId);
    } catch (err: any) {
      alert(err?.message || 'Failed to delete resource.');
    } finally {
      setDeleting(false);
    }
  };

  const getTypeIcon = (type: ClassResourceType) => {
    switch (type) {
      case 'video':
        return <Video className="w-4 h-4 text-purple-600" />;
      case 'article':
        return <BookOpen className="w-4 h-4 text-blue-600" />;
      case 'notes':
        return <FileText className="w-4 h-4 text-amber-600" />;
      case 'practice':
        return <Code2 className="w-4 h-4 text-emerald-600" />;
      default:
        return <Globe className="w-4 h-4 text-slate-600" />;
    }
  };

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

  const selectedClass = classes.find((c) => c.id === selectedClassId);

  const filteredResources = resources.filter((r) => {
    if (typeFilter !== 'all' && r.resource_type !== typeFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = r.title.toLowerCase().includes(q);
      const matchDesc = r.description?.toLowerCase().includes(q);
      const matchTopic = r.topic_title?.toLowerCase().includes(q);
      return matchTitle || matchDesc || matchTopic;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-orange-600 uppercase tracking-wider mb-1">
            <BookOpen className="w-4 h-4" />
            <span>Curriculum & Knowledge Sharing</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Class Resources</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Curate and distribute verified reference materials, notes, and study links to your students.
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

          {selectedClass && (
            <button
              onClick={handleOpenAddModal}
              className="px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-sm font-semibold shadow-xs transition-all flex items-center space-x-1.5 cursor-pointer whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              <span>Add Resource</span>
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
            You have not created any classes yet. Navigate to Cohort Analytics to create your first class and share resources.
          </p>
        </div>
      )}

      {/* Main Content Area */}
      {selectedClass && (
        <div className="space-y-4">
          {/* Controls & Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-500">Filter Type:</span>
              <div className="flex flex-wrap gap-1.5">
                {(['all', 'video', 'article', 'notes', 'practice', 'other'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                      typeFilter === t
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search resources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 w-full sm:w-64"
              />
            </div>
          </div>

          {/* Resources List */}
          {resourcesLoading && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mx-auto mb-2" />
              <p className="text-sm text-slate-500">Fetching resources for {selectedClass.name}...</p>
            </div>
          )}

          {resourcesError && (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-sm flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                <span>{resourcesError}</span>
              </div>
              <button
                onClick={() => loadResources(selectedClass.id)}
                className="px-3 py-1 bg-white border border-rose-300 rounded-lg text-xs font-bold text-rose-700 hover:bg-rose-100"
              >
                Retry
              </button>
            </div>
          )}

          {!resourcesLoading && !resourcesError && filteredResources.length === 0 && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">
                {resources.length === 0 ? 'No Resources Added' : 'No matching resources'}
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                {resources.length === 0
                  ? 'Add your first reading link, video lesson, or study notes for this class.'
                  : 'Try clearing your filters or search keywords.'}
              </p>
              {resources.length === 0 && (
                <button
                  onClick={handleOpenAddModal}
                  className="mt-4 px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold shadow-xs transition-colors cursor-pointer"
                >
                  Add First Resource
                </button>
              )}
            </div>
          )}

          {!resourcesLoading && !resourcesError && filteredResources.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredResources.map((res) => (
                <div
                  key={res.id}
                  className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        <span
                          className={`inline-flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded-full border ${getTypeBadgeStyle(
                            res.resource_type
                          )}`}
                        >
                          {getTypeIcon(res.resource_type)}
                          <span className="capitalize">{res.resource_type}</span>
                        </span>
                        {res.topic_title && (
                          <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                            Topic: {res.topic_title}
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => setResourceToDelete(res)}
                        className="text-slate-400 hover:text-rose-600 p-1 rounded-md hover:bg-rose-50 transition-colors cursor-pointer shrink-0"
                        title="Delete resource"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div>
                      <h4 className="text-base font-bold text-slate-900 leading-snug">{res.title}</h4>
                      {res.description && (
                        <p className="text-xs text-slate-600 mt-1 whitespace-pre-wrap leading-relaxed line-clamp-3">
                          {res.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-400 text-[11px]">
                      {new Date(res.created_at).toLocaleDateString()}
                    </span>

                    <a
                      href={res.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 font-bold text-orange-600 hover:text-orange-700 bg-orange-50 hover:bg-orange-100 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      <span>Visit External Resource</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Resource Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-orange-600" />
                <h3 className="text-base font-bold text-slate-900">Add Class Resource</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
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

            <form onSubmit={handleCreateResource} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Title <span className="text-rose-500">*</span>
                  <span className="font-normal text-slate-400 ml-1">({title.length}/150)</span>
                </label>
                <input
                  type="text"
                  maxLength={150}
                  required
                  placeholder="e.g., Binary Search Deep Dive & Complexity Analysis"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  URL <span className="text-rose-500">*</span> (http/https only)
                </label>
                <input
                  type="url"
                  maxLength={500}
                  required
                  placeholder="https://example.com/article"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Resource Type</label>
                  <select
                    value={resourceType}
                    onChange={(e) => setResourceType(e.target.value as ClassResourceType)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 cursor-pointer"
                  >
                    <option value="article">Article / Reading</option>
                    <option value="video">Video Lecture</option>
                    <option value="notes">Lecture Notes</option>
                    <option value="practice">Practice Problem</option>
                    <option value="other">Other Reference</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Topic (Optional)</label>
                  <select
                    value={topicId}
                    onChange={(e) => setTopicId(e.target.value === '' ? '' : Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 cursor-pointer"
                  >
                    <option value="">General (No topic)</option>
                    {courseTopics.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Description / Context (Optional)
                  <span className="font-normal text-slate-400 ml-1">({description.length}/2000)</span>
                </label>
                <textarea
                  rows={3}
                  maxLength={2000}
                  placeholder="Key takeaways, relevant sections, or why students should review this."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
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
                  <span>{submitting ? 'Adding...' : 'Add Resource'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {resourceToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <div className="p-2 bg-rose-100 rounded-xl">
                <Trash2 className="w-5 h-5 text-rose-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Delete Resource</h3>
                <p className="text-xs text-slate-500">Soft delete with audit trail</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to delete <span className="font-bold text-slate-900">"{resourceToDelete.title}"</span>?
              Students will no longer see this resource in their class portal.
            </p>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
              <button
                type="button"
                onClick={() => setResourceToDelete(null)}
                disabled={deleting}
                className="px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-xl text-xs font-bold cursor-pointer transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteResource}
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

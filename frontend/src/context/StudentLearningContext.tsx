import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { CentralStudentState, User, Course } from '../types';
import { api } from '../services/api';

interface StudentLearningContextType {
  studentState: CentralStudentState | null;
  courses: Course[];
  activeCourse: Course | { id: number; code: string; title: string; description: string; } | undefined;
  loading: boolean;
  refreshStudentState: () => Promise<void>;
  submitAssessment: (
    attemptType: string,
    answers: Record<string, string>,
    topicId?: number,
    codingSubmission?: any
  ) => Promise<any>;
  simulateActivity: (
    topicId: number,
    score: number,
    activityType: string,
    reason?: string
  ) => Promise<any>;
  completeTopic: (topicId: number) => Promise<any>;
  seedDemo: () => Promise<void>;
  selectedTopicForStudy: number | null;
  setSelectedTopicForStudy: (id: number | null) => void;
  activeCourseId: number;
  setActiveCourseId: (id: number) => void;
}

const StudentLearningContext = createContext<StudentLearningContextType | undefined>(undefined);

export const StudentLearningProvider: React.FC<{
  children: React.ReactNode;
  currentUser: User | null;
}> = ({ children, currentUser }) => {
  const [studentState, setStudentState] = useState<CentralStudentState | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTopicForStudy, setSelectedTopicForStudy] = useState<number | null>(null);
  const [activeCourseId, setActiveCourseIdState] = useState<number>(() => {
    const saved = localStorage.getItem('obepath_active_course_id');
    return saved ? parseInt(saved, 10) : ((currentUser as any)?.selected_course_id || 1);
  });

  useEffect(() => {
    let isMounted = true;
    api.getCourses().then((data) => {
      if (isMounted && Array.isArray(data)) {
        setCourses(data);
      }
    }).catch((err) => console.warn('Could not load courses in context:', err));
    return () => { isMounted = false; };
  }, []);

  const activeCourse = courses.find((c) => c.id === activeCourseId) || studentState?.enrolledCourse || undefined;

  const userId = currentUser?.id || 1;

  const setActiveCourseId = useCallback(async (id: number) => {
    localStorage.setItem('obepath_active_course_id', id.toString());
    setActiveCourseIdState(id);
    setSelectedTopicForStudy(null);
    setStudentState(null);
    setLoading(true);
    try {
      await api.updateProfile({ selected_course_id: id }, userId);
    } catch (e) {
      console.warn('Could not update profile course', e);
    }
    try {
      const state = await api.getStudentState(userId, id);
      setStudentState(state);
    } catch (err) {
      console.error('Failed to load student state for new course', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const refreshStudentState = useCallback(async () => {
    try {
      setLoading(true);
      const state = await api.getStudentState(userId, activeCourseId);
      setStudentState(state);
    } catch (err) {
      console.error('Failed to load student state from backend', err);
    } finally {
      setLoading(false);
    }
  }, [userId, activeCourseId]);

  // Synchronize course selection from profile if present
  useEffect(() => {
    let isMounted = true;
    if (currentUser?.id) {
      api.getProfile(currentUser.id).then((prof) => {
        if (isMounted && prof?.selected_course_id) {
          const profileCid = prof.selected_course_id;
          const saved = localStorage.getItem('obepath_active_course_id');
          if (!saved) {
            localStorage.setItem('obepath_active_course_id', profileCid.toString());
            setActiveCourseIdState(profileCid);
          }
        }
      }).catch((e) => console.warn('Could not load user profile course', e));
    }
    return () => { isMounted = false; };
  }, [currentUser?.id]);

  useEffect(() => {
    refreshStudentState();
  }, [refreshStudentState]);

  const submitAssessment = async (
    attemptType: string,
    answers: Record<string, string>,
    topicId?: number,
    codingSubmission?: any
  ) => {
    try {
      const res = await api.submitAssessmentAttempt({
        course_id: activeCourseId,
        attempt_type: attemptType,
        answers,
        topic_id: topicId,
        coding_submission: codingSubmission
      }, userId);
      if (res.state) {
        setStudentState(res.state);
      }
      return res;
    } catch (err) {
      console.error('Failed to submit assessment', err);
      throw err;
    }
  };

  const simulateActivity = async (
    topicId: number,
    score: number,
    activityType: string,
    reason?: string
  ) => {
    try {
      const res = await api.simulateActivity({
        topic_id: topicId,
        score,
        activity_type: activityType,
        reason
      }, userId);
      if (res.state) {
        setStudentState(res.state);
      }
      return res;
    } catch (err) {
      console.error('Failed to simulate activity', err);
      throw err;
    }
  };

  const completeTopic = async (topicId: number) => {
    try {
      setLoading(true);
      const res = await api.completeTopic(topicId);
      if (res && res.state) {
        setStudentState(res.state);
      } else {
        await refreshStudentState();
      }
      return res;
    } catch (err: any) {
      if (err?.message?.includes('already completed') || err?.status === 409) {
        await refreshStudentState();
        return { alreadyCompleted: true };
      }
      console.error('Failed to complete topic', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const seedDemo = async () => {
    try {
      const state = await api.seedDemoJourney(activeCourseId, userId);
      setStudentState(state);
    } catch (err) {
      console.error('Failed to seed demo journey', err);
    }
  };

  return (
    <StudentLearningContext.Provider
      value={{
        studentState,
        courses,
        activeCourse,
        loading,
        refreshStudentState,
        submitAssessment,
        simulateActivity,
        completeTopic,
        seedDemo,
        selectedTopicForStudy,
        setSelectedTopicForStudy,
        activeCourseId,
        setActiveCourseId
      }}
    >
      {children}
    </StudentLearningContext.Provider>
  );
};

export const useStudentLearning = () => {
  const context = useContext(StudentLearningContext);
  if (!context) {
    return {
      studentState: null,
      courses: [],
      activeCourse: undefined,
      loading: false,
      refreshStudentState: async () => {},
      submitAssessment: async () => ({}),
      simulateActivity: async () => ({}),
      completeTopic: async () => ({}),
      seedDemo: async () => {},
      selectedTopicForStudy: null,
      setSelectedTopicForStudy: () => {},
      activeCourseId: 1,
      setActiveCourseId: () => {}
    };
  }
  return context;
};

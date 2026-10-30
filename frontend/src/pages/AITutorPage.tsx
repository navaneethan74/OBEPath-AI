import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Sparkles,
  CheckCircle2,
  RotateCw,
  AlertCircle,
  FileCheck2,
  BookOpen
} from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';
import { useStudentLearning } from '../context/StudentLearningContext';
import { MarkdownView } from '../components/MarkdownView';
import { DynamicPracticeAssessment } from '../components/DynamicPracticeAssessment';
import { AITutorTestMeModal } from '../components/AITutorTestMeModal';

interface Message {
  id: string;
  sender: 'user' | 'tutor';
  text: string;
  time: string;
  followups?: string[];
  isError?: boolean;
  failedPrompt?: { text: string; action?: string };
}

interface AITutorPageProps {
  currentUser?: User | null;
  onNavigateToAssessment?: () => void;
}

export const AITutorPage: React.FC<AITutorPageProps> = ({ currentUser }) => {
  const {
    studentState,
    refreshStudentState,
    selectedTopicForStudy,
    activeCourseId,
    setSelectedTopicForStudy
  } = useStudentLearning();

  const studentName = currentUser?.full_name || studentState?.studentProfile?.full_name || 'Student';

  // Dynamic target topic from single central student state
  const targetFromContext = selectedTopicForStudy
    ? studentState?.topicMastery.find((t) => t.topic_id === selectedTopicForStudy)
    : null;

  const currentTopic =
    targetFromContext ||
    studentState?.currentTargetTopic ||
    (studentState?.topicMastery ? studentState.topicMastery[0] : null);

  const topicId = currentTopic?.topic_id || 1;
  const topicTitle = currentTopic?.title || 'Queue Basics';
  const topicMastery = currentTopic ? Math.round(currentTopic.mastery) : 54;
  const rawClassification = currentTopic?.classification || 'DEVELOPING';

  // Map internal classification to student-friendly terminology
  const getFriendlyStatus = (mastery: number, classification?: string) => {
    const c = (classification || '').toUpperCase();
    if (c === 'MASTERED' || mastery >= 80) return 'Mastered';
    if (c === 'PROFICIENT' || mastery >= 70) return 'Proficient';
    if (c === 'DEVELOPING' || (mastery >= 50 && mastery < 70)) return 'In Progress';
    return 'Needs Practice';
  };

  const friendlyStatus = getFriendlyStatus(topicMastery, rawClassification);

  // Status badge styling matching OBEPath AI theme
  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case 'Mastered':
      case 'Proficient':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'In Progress':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'Needs Practice':
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200';
    }
  };

  // Find next topic in sequence for friendly personalized learning advice
  const currentIndex = studentState?.topicMastery?.findIndex((t) => t.topic_id === topicId) ?? -1;
  const nextTopic =
    currentIndex >= 0 && currentIndex < (studentState?.topicMastery?.length || 0) - 1
      ? studentState?.topicMastery[currentIndex + 1]
      : null;

  const getPersonalizedHelp = () => {
    if (topicMastery < 50 && nextTopic) {
      return `Let's strengthen the basics before moving to ${nextTopic.title}.`;
    }
    if (topicMastery < 50) {
      return `You're currently working on ${topicTitle}. Let's build a strong foundation together.`;
    }
    if (topicMastery >= 80 && nextTopic) {
      return `You have strong understanding of ${topicTitle}! Ready to advance toward ${nextTopic.title}?`;
    }
    if (topicMastery >= 80) {
      return `You're doing great on ${topicTitle}. Feel free to ask deeper questions or test your skills.`;
    }
    return `You're currently working on ${topicTitle}.`;
  };

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [assessmentSuccessMsg, setAssessmentSuccessMsg] = useState<string | null>(null);

  // Modals for real assessment execution
  const [showPracticeModal, setShowPracticeModal] = useState<boolean>(false);
  const [showTestMeModal, setShowTestMeModal] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize tutor greeting based on real student target topic and mastery
  useEffect(() => {
    const scaffoldAdvice =
      topicMastery < 50
        ? "Let's strengthen the basics first with intuitive explanations and step-by-step examples."
        : topicMastery < 80
        ? "You're making steady progress! We can work through practical examples and guided practice together."
        : "You've built high mastery on this topic! We can dive into deeper problems, edge cases, and optimizations.";

    setMessages([
      {
        id: 'welcome-1',
        sender: 'tutor',
        text: `Hi, ${studentName} 👋\n\nI'm here to help you understand **${topicTitle}**.\n\n${scaffoldAdvice}\n\nWhat would you like to explore first?`,
        time: 'Just now',
        followups: ['Explain Simply', 'Give an Example', 'Give a Hint', 'Explain Again', 'Test Me', 'Summarize']
      }
    ]);
  }, [topicTitle, topicMastery, studentName]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (text: string, action?: string) => {
    if (!text.trim() && !action) return;

    const userText = text || (action ? action.replace(/_/g, ' ') : '');
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: userText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Build recent conversation history for Gemini multi-turn pedagogical context
    const recentHistory = messages
      .filter((m) => !m.isError)
      .slice(-6)
      .map((m) => ({
        role: m.sender === 'user' ? 'user' : 'model',
        content: m.text
      }));

    try {
      const res = await api.chatWithTutor(
        topicId,
        text,
        action,
        activeCourseId || undefined,
        recentHistory,
        currentUser?.id || 1
      );

      if (res.error) {
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'tutor',
          text: `I had trouble generating a response right now. Please try again in a moment.`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true,
          failedPrompt: { text, action }
        };
        setMessages((prev) => [...prev, errorMsg]);
      } else {
        const tutorMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'tutor',
          text: res.reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          followups: res.suggested_followups
        };
        setMessages((prev) => [...prev, tutorMsg]);
      }
    } catch (err: any) {
      console.error('Tutor chat error', err);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'tutor',
        text: `I couldn't connect right now. Please check your connection and tap **Retry** below.`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
        failedPrompt: { text, action }
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = (failedPrompt?: { text: string; action?: string }) => {
    if (!failedPrompt) return;
    sendMessage(failedPrompt.text, failedPrompt.action);
  };

  const handleQuickAction = (actionKey: string, promptText: string) => {
    if (actionKey === 'test_me') {
      setShowTestMeModal(true);
      return;
    }
    sendMessage(promptText, actionKey);
  };

  const handleTestMeComplete = (summary: {
    score: number;
    maxScore: number;
    percentage: number;
    prevMastery: number;
    newMastery: number;
    classification: string;
  }) => {
    const isStrong = summary.percentage >= 60;
    const tutorMsg: Message = {
      id: Date.now().toString(),
      sender: 'tutor',
      text: `🎯 **Test Me Check Complete for ${topicTitle}!**\n\nYou answered **${summary.score} of ${summary.maxScore} (${summary.percentage}%)** correctly.\n\nYour mastery updated: **${summary.prevMastery}% ➔ ${summary.newMastery}%**.\n\n${
        isStrong
          ? '🌟 Great job! You demonstrated solid understanding. Ready to tackle more topics or try another challenge?'
          : '💡 Good practice! Reviewing the questions and examples will help strengthen your grasp. Ask me anything if you would like me to explain!'
      }`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      followups: ['Explain Simply', 'Give an Example', 'Give a Hint', 'Summarize']
    };

    setMessages((prev) => [...prev, tutorMsg]);
    setAssessmentSuccessMsg(
      `Test Me complete! Score: ${summary.percentage}%. Mastery updated: ${summary.prevMastery}% ➔ ${summary.newMastery}%.`
    );
  };

  const handlePracticeComplete = (evalResult: any) => {
    const prevM = evalResult.primary_mastery ? Math.round(evalResult.primary_mastery.previous_mastery) : topicMastery;
    const newM = evalResult.primary_mastery ? Math.round(evalResult.primary_mastery.new_mastery) : Math.round(evalResult.percentage);

    setAssessmentSuccessMsg(
      `Practice complete! Score: ${evalResult.percentage}%. Mastery updated: ${prevM}% ➔ ${newM}%.`
    );
  };

  // Quick Action Buttons requested
  const quickActionButtons = [
    {
      id: 'explain_simply',
      label: 'Explain Simply',
      prompt: `Explain ${topicTitle} simply with intuition and no jargon.`
    },
    {
      id: 'give_example',
      label: 'Give an Example',
      prompt: `Give a real-world coding example illustrating ${topicTitle}.`
    },
    {
      id: 'give_hint',
      label: 'Give a Hint',
      prompt: `Give me a conceptual hint on how to think about ${topicTitle}.`
    },
    {
      id: 'explain_again',
      label: 'Explain Again',
      prompt: `I don't understand yet. Explain ${topicTitle} again in a simpler, beginner-friendly way.`
    },
    {
      id: 'test_me',
      label: 'Test Me',
      prompt: `Test my understanding of ${topicTitle}.`
    },
    {
      id: 'summarize',
      label: 'Summarize',
      prompt: `Summarize the essential key takeaways for ${topicTitle} in bullet points.`
    }
  ];

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* 1. Page Header */}
      <div className="bg-white border border-[#E5E5DF] rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-11 h-11 bg-orange-50 border border-orange-200 text-[#EA580C] rounded-2xl flex items-center justify-center shadow-xs flex-shrink-0">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              AI Tutor
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Get help understanding your current topic.
            </p>
          </div>
        </div>

        {/* Real current topic badge */}
        <div className="flex items-center space-x-3 bg-[#FAFAF7] border border-[#E5E5DF] rounded-xl px-4 py-2.5 self-start md:self-auto">
          <div className="w-2.5 h-2.5 rounded-full bg-[#EA580C] flex-shrink-0" />
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Current topic
            </div>
            <div className="text-sm font-bold text-slate-800">
              {topicTitle}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Current Context Card */}
      <div className="bg-white border border-[#E5E5DF] rounded-2xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start sm:items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-orange-50 text-[#EA580C] border border-orange-200 flex items-center justify-center flex-shrink-0 mt-0.5 sm:mt-0">
              <BookOpen className="w-4 h-4" />
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-slate-500">Learning:</span>
                <span className="text-sm font-bold text-slate-900">{topicTitle}</span>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-bold text-orange-600 font-mono">
                  {topicMastery}% mastery
                </span>
                <span className="text-slate-300">•</span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${getStatusBadgeStyle(
                    friendlyStatus
                  )}`}
                >
                  {friendlyStatus}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {getPersonalizedHelp()}
              </p>
            </div>
          </div>

          {/* Quick assessment link if student wants a quick challenge */}
          <button
            onClick={() => setShowTestMeModal(true)}
            className="self-start sm:self-auto px-3.5 py-1.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Test Me</span>
          </button>
        </div>
      </div>

      {/* Assessment Success Notice */}
      {assessmentSuccessMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{assessmentSuccessMsg}</span>
          </div>
          <button
            onClick={() => setAssessmentSuccessMsg(null)}
            className="text-slate-400 hover:text-slate-700 text-xs px-1.5 py-0.5 rounded cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* 3. Chat Area Container */}
      <div className="bg-white border border-[#E5E5DF] rounded-2xl shadow-xs flex flex-col h-[540px] sm:h-[580px] overflow-hidden">
        {/* Messages scroll area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-orange-50 border border-orange-200 text-[#EA580C] flex items-center justify-center shadow-xs">
                <Bot className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">
                How can I help you today?
              </h3>
              <p className="text-sm text-slate-500 max-w-sm">
                Try asking about your current topic, or tap one of the quick actions below.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2 pt-2 max-w-lg">
                {quickActionButtons.map((btn) => (
                  <button
                    key={btn.id}
                    onClick={() => handleQuickAction(btn.id, btn.prompt)}
                    disabled={loading}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all shadow-2xs cursor-pointer ${
                      btn.id === 'test_me'
                        ? 'bg-[#EA580C] hover:bg-[#C2410C] text-white font-semibold'
                        : 'bg-white hover:bg-slate-50 text-slate-700 border border-[#E5E5DF]'
                    }`}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isTutor = msg.sender === 'tutor';
              return (
                <div
                  key={msg.id}
                  className={`flex items-start space-x-3 ${isTutor ? 'justify-start' : 'justify-end'}`}
                >
                  {/* Tutor Avatar on Left */}
                  {isTutor && (
                    <div className="w-8 h-8 rounded-full bg-orange-100 text-[#EA580C] border border-orange-200 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  {/* Message Content Bubble */}
                  <div className={`space-y-1.5 max-w-[85%] sm:max-w-2xl ${isTutor ? 'text-left' : 'text-right'}`}>
                    <div
                      className={`rounded-2xl shadow-xs ${
                        isTutor
                          ? msg.isError
                            ? 'bg-amber-50/80 border border-amber-200 text-slate-900 p-4 sm:p-5 rounded-tl-sm'
                            : 'bg-white border border-[#E5E5DF] text-slate-900 p-4 sm:p-5 rounded-tl-sm'
                          : 'bg-[#0F172A] text-white px-4 py-3 sm:px-5 sm:py-3.5 rounded-tr-sm text-sm'
                      }`}
                    >
                      {isTutor ? (
                        <div>
                          {msg.isError ? (
                            <div className="space-y-2">
                              <div className="flex items-center space-x-1.5 text-amber-800 font-bold text-xs">
                                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                                <span>Unable to complete response</span>
                              </div>
                              <p className="text-xs sm:text-sm text-slate-700">{msg.text}</p>
                              {msg.failedPrompt && (
                                <div className="pt-2 flex items-center space-x-2">
                                  <button
                                    onClick={() => handleRetry(msg.failedPrompt)}
                                    disabled={loading}
                                    className="px-3 py-1.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                                  >
                                    <RotateCw className="w-3.5 h-3.5" />
                                    <span>Retry</span>
                                  </button>
                                </div>
                              )}
                            </div>
                          ) : (
                            <MarkdownView content={msg.text} />
                          )}
                        </div>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap break-words">{msg.text}</p>
                      )}
                    </div>

                    {/* Followup Quick Action Chips */}
                    {isTutor && !msg.isError && msg.followups && msg.followups.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        {msg.followups.map((f, i) => (
                          <button
                            key={i}
                            onClick={() => {
                              if (f.toLowerCase().includes('test me')) {
                                setShowTestMeModal(true);
                              } else {
                                sendMessage(f);
                              }
                            }}
                            disabled={loading}
                            className="px-2.5 py-1 bg-white hover:bg-orange-50 text-slate-700 hover:text-[#EA580C] border border-[#E5E5DF] hover:border-orange-200 rounded-lg text-[11px] font-medium transition-colors cursor-pointer shadow-2xs"
                          >
                            {f}
                          </button>
                        ))}
                      </div>
                    )}

                    <div className={`text-[10px] text-slate-400 ${isTutor ? 'pl-1' : 'pr-1'}`}>
                      {msg.time}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Friendly Loading Indicator */}
          {loading && (
            <div className="flex items-start space-x-3 animate-fadeIn">
              <div className="w-8 h-8 rounded-full bg-orange-100 text-[#EA580C] border border-orange-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-white border border-[#E5E5DF] rounded-2xl rounded-tl-sm p-4 shadow-xs flex items-center space-x-2.5 text-xs text-slate-600">
                <span className="flex space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#EA580C] animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-[#EA580C] animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-[#EA580C] animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
                <span className="font-medium">AI Tutor is thinking...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* 4. Quick Action Chips Bar (Visible above input) */}
        <div className="px-4 py-2 bg-[#FAFAF7] border-t border-[#E5E5DF] overflow-x-auto no-scrollbar">
          <div className="flex items-center space-x-2">
            {quickActionButtons.map((btn) => (
              <button
                key={btn.id}
                onClick={() => handleQuickAction(btn.id, btn.prompt)}
                disabled={loading}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all shadow-2xs whitespace-nowrap cursor-pointer disabled:opacity-50 ${
                  btn.id === 'test_me'
                    ? 'bg-[#EA580C] hover:bg-[#C2410C] text-white font-semibold shadow-xs'
                    : 'bg-white hover:bg-slate-100 text-slate-700 hover:text-slate-900 border border-[#E5E5DF]'
                }`}
              >
                {btn.id === 'test_me' && '★ '}
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* 5. Clean Input Area */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim() && !loading) {
              sendMessage(input.trim());
            }
          }}
          className="p-3 sm:p-4 bg-white border-t border-[#E5E5DF] flex items-center space-x-2.5"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (input.trim() && !loading) {
                  sendMessage(input.trim());
                }
              }
            }}
            placeholder="Ask anything about this topic..."
            disabled={loading}
            className="flex-1 px-4 py-2.5 sm:py-3 bg-[#FAFAF7] border border-[#E5E5DF] rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-[#EA580C] focus:ring-2 focus:ring-orange-500/20 transition-all disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="w-10 h-10 sm:w-11 sm:h-11 bg-[#EA580C] hover:bg-[#C2410C] disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-xs hover:shadow transition-all flex-shrink-0 cursor-pointer"
            title="Send"
          >
            {loading ? (
              <RotateCw className="w-4 h-4 animate-spin" />
            ) : (
              <span>→</span>
            )}
          </button>
        </form>
      </div>

      {/* Interactive Real AI Tutor Test Me Modal */}
      {showTestMeModal && (
        <AITutorTestMeModal
          topicId={topicId}
          topicTitle={topicTitle}
          courseId={activeCourseId}
          onClose={() => setShowTestMeModal(false)}
          onSessionComplete={handleTestMeComplete}
        />
      )}

      {/* Dynamic Practice Assessment Modal (Preserved for full compatibility) */}
      {showPracticeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
          <div className="max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <DynamicPracticeAssessment
              key={`${activeCourseId}-${topicId}`}
              topicId={topicId}
              topicTitle={topicTitle}
              courseId={activeCourseId}
              mode="practice"
              onClose={() => setShowPracticeModal(false)}
              onComplete={(evalRes) => {
                handlePracticeComplete(evalRes);
              }}
              onNavigateToTutor={() => setShowPracticeModal(false)}
              onNavigateToTopic={(newTopicId) => {
                setSelectedTopicForStudy(newTopicId);
                setShowPracticeModal(false);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Terminal,
  BookOpen,
  Clock,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { pyodideRunner, PyodideStatus } from '../services/pyodideRunner';
import { CodingChallenge, CodeExecutionResult, CodingSubmission } from '../types';

interface TopicCodingCompilerProps {
  courseId?: number;
  topicId?: number;
  topicTitle?: string;
  initialCode?: string;
  onCodeChange?: (code: string) => void;
  onCompileResult?: (submission: CodingSubmission) => void;
  readOnly?: boolean;
}

export const TopicCodingCompiler: React.FC<TopicCodingCompilerProps> = ({
  courseId = 2,
  topicId,
  topicTitle,
  initialCode,
  onCodeChange,
  onCompileResult,
  readOnly = false
}) => {
  const [challenge, setChallenge] = useState<CodingChallenge | null>(null);
  const [loadingChallenge, setLoadingChallenge] = useState<boolean>(true);
  const [code, setCode] = useState<string>(initialCode || '');
  const [compiling, setCompiling] = useState<boolean>(false);
  const [compileResult, setCompileResult] = useState<CodeExecutionResult | null>(null);
  const [lastRunCode, setLastRunCode] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'tests' | 'console'>('tests');
  const [copied, setCopied] = useState<boolean>(false);
  const [showDescription, setShowDescription] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Pyodide In-Browser Runner Status
  const [pyodideStatus, setPyodideStatus] = useState<PyodideStatus>(pyodideRunner.getStatus());
  const [pyodideError, setPyodideError] = useState<string | null>(pyodideRunner.getErrorMessage());

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Subscribe to Pyodide status updates and trigger background init
  useEffect(() => {
    const unsubscribe = pyodideRunner.onStatusChange((status, err) => {
      setPyodideStatus(status);
      setPyodideError(err);
    });
    pyodideRunner.initPyodide().catch(() => {});
    return () => unsubscribe();
  }, []);

  // Fetch Topic-Specific Coding Challenge
  useEffect(() => {
    let isMounted = true;
    const loadChallenge = async () => {
      setLoadingChallenge(true);
      setErrorMsg(null);
      setCompileResult(null);
      setLastRunCode(null);
      setActiveTab('tests');
      try {
        const data = await api.getCodingChallenge(courseId, topicId, topicTitle);
        if (isMounted && data) {
          if (data.has_coding === false || !data.starter_code) {
            setChallenge({
              has_coding: false,
              title: data.message || 'Conceptual Topic — Coding Practice Not Required',
              description: 'This topic focuses on foundational theoretical principles, schema design, or conceptual analysis. Hands-on code compilation is not required for this topic. Please complete the adaptive conceptual assessment.',
              topic_title: topicTitle || `Topic ${topicId}`,
              difficulty: 'Conceptual',
              test_cases: []
            });
          } else {
            setChallenge(data);
            if (!initialCode) {
              setCode(data.starter_code);
              onCodeChange?.(data.starter_code);
            }
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setErrorMsg(err.message || 'Could not load challenge');
        }
      } finally {
        if (isMounted) setLoadingChallenge(false);
      }
    };

    loadChallenge();
    return () => {
      isMounted = false;
    };
  }, [courseId, topicId, topicTitle]);

  // Handle Tab indentation in textarea
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      const updated = code.substring(0, start) + '    ' + code.substring(end);
      setCode(updated);
      onCodeChange?.(updated);

      // Restore cursor position after state update
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4;
        }
      }, 0);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setCode(val);
    onCodeChange?.(val);
  };

  const handleReset = () => {
    if (challenge?.starter_code) {
      setCode(challenge.starter_code);
      onCodeChange?.(challenge.starter_code);
      setCompileResult(null);
      setLastRunCode(null);
      onCompileResult?.(null as any);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Compile and run code in in-browser Pyodide WebAssembly runner
  const handleRunCode = async () => {
    if (!code.trim()) return;
    setCompiling(true);
    try {
      // Execute in Web Worker with Pyodide (enforces 5s timeout, 64KB output cap, 10,000 char cap)
      const res = await pyodideRunner.runCode(
        code,
        challenge?.test_cases || []
      );
      setCompileResult(res);
      setLastRunCode(code);

      // Notify parent of self-verified practice submission
      const submission: CodingSubmission = {
        challenge_id: challenge?.id || 'custom_code',
        title: challenge?.title || 'Topic Coding Problem',
        topic_id: challenge?.topic_id || topicId,
        code,
        passed_count: res.passed_count,
        total_count: res.total_count,
        percentage: res.percentage,
        all_passed: res.all_passed,
        results: res.results,
        execution_time_ms: res.execution_time_ms,
        stdout: res.stdout,
        stderr: res.stderr,
        self_verified: true
      };
      onCompileResult?.(submission);

      if (!res.success && res.stderr) {
        setActiveTab('console');
      } else {
        setActiveTab('tests');
      }
    } catch (err: any) {
      console.error('In-browser code execution failed', err);
      const failedRes: CodeExecutionResult = {
        success: false,
        all_passed: false,
        passed_count: 0,
        total_count: challenge?.test_cases?.length || 1,
        percentage: 0,
        stdout: '',
        stderr: err.message || 'Execution failed. Please check your syntax.',
        results: [],
        execution_time_ms: 0,
        self_verified: true
      };
      setCompileResult(failedRes);
      setLastRunCode(code);

      const failedSubmission: CodingSubmission = {
        challenge_id: challenge?.id || 'custom_code',
        title: challenge?.title || 'Topic Coding Problem',
        topic_id: challenge?.topic_id || topicId,
        code,
        passed_count: 0,
        total_count: challenge?.test_cases?.length || 1,
        percentage: 0,
        all_passed: false,
        results: [],
        execution_time_ms: 0,
        stdout: '',
        stderr: err.message || 'Execution failed. Please check your syntax.',
        self_verified: true
      };
      onCompileResult?.(failedSubmission);
      setActiveTab('console');
    } finally {
      setCompiling(false);
    }
  };

  // Generate line numbers
  const lines = code.split('\n');
  const lineCount = lines.length;

  if (loadingChallenge) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl text-center space-y-3 text-slate-300">
        <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs font-mono text-slate-400">Loading topic-aligned coding challenge & compiler environment...</p>
      </div>
    );
  }

  if (challenge && challenge.has_coding === false) {
    return (
      <div className="p-8 bg-white border border-slate-200 rounded-2xl text-center space-y-4 shadow-2xs">
        <div className="w-12 h-12 rounded-2xl bg-orange-50 text-orange-600 border border-orange-200 flex items-center justify-center mx-auto">
          <BookOpen className="w-6 h-6" />
        </div>
        <div className="max-w-md mx-auto space-y-1.5">
          <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-wider">
            Conceptual Topic
          </span>
          <h4 className="text-base font-bold text-slate-900">{challenge.title}</h4>
          <p className="text-xs text-slate-600 leading-relaxed">{challenge.description}</p>
        </div>
        <div className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-4 py-2 rounded-xl inline-block">
          ✓ Conceptual Assessment Active: Complete the MCQ questions to advance topic mastery.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 1. CODING PROBLEM STATEMENT HEADER */}
      {challenge && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
          {/* Header pill bar */}
          <div className="p-4 sm:p-5 bg-gradient-to-r from-orange-50/70 to-amber-50/40 border-b border-orange-100 flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-0.5 bg-[#EA580C] text-white rounded-md text-[10px] font-bold tracking-wider uppercase">
                  Coding Challenge
                </span>
                <span className="px-2.5 py-0.5 bg-white text-orange-700 border border-orange-200 rounded-md text-[10px] font-bold">
                  {challenge.topic_title}
                </span>
                {challenge.outcome_code && (
                  <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md text-[10px] font-mono font-bold">
                    {challenge.outcome_code}
                  </span>
                )}
                <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md text-[10px] font-semibold">
                  {challenge.difficulty}
                </span>
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900">
                {challenge.title}
              </h3>
            </div>

            <button
              type="button"
              onClick={() => setShowDescription(!showDescription)}
              className="text-xs text-orange-600 font-semibold hover:underline flex items-center space-x-1"
            >
              <span>{showDescription ? 'Hide Details' : 'View Problem Details'}</span>
              {showDescription ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Expanded Problem Description */}
          {showDescription && (
            <div className="p-5 sm:p-6 space-y-4 text-xs text-slate-700 border-t border-slate-100 bg-[#FAFAFC]">
              <div className="prose prose-xs max-w-none text-slate-800 leading-relaxed whitespace-pre-line font-sans">
                {challenge.description}
              </div>

              {/* Sample test cases preview */}
              {challenge.test_cases && challenge.test_cases.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-200">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-orange-600" />
                    <span>Expected Test Specifications:</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {challenge.test_cases.slice(0, 4).map((tc, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 bg-white rounded-lg border border-slate-200 font-mono text-[11px] space-y-1 shadow-2xs"
                      >
                        <div className="text-slate-500 text-[10px]">Case {idx + 1}: {tc.input_desc || tc.call}</div>
                        <div className="flex items-center space-x-1.5 text-slate-900">
                          <span className="text-orange-600 font-bold">➔ Expected:</span>
                          <span className="bg-slate-100 px-1.5 py-0.5 rounded text-[11px] text-slate-800 font-semibold">
                            {tc.expected}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 2. PYODIDE RUNNER STATUS NOTICES */}
      {pyodideStatus === 'loading' && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center justify-between text-xs text-amber-200">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin shrink-0" />
            <span>Initializing in-browser Python engine (Pyodide v0.26.4)... Loading WebAssembly package (~5 MB).</span>
          </div>
        </div>
      )}

      {pyodideStatus === 'error' && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex flex-wrap items-center justify-between gap-2 text-xs text-rose-200">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>In-browser runner error: {pyodideError || 'Failed to initialize Pyodide environment.'}</span>
          </div>
          <button
            type="button"
            onClick={() => pyodideRunner.retryInitPyodide()}
            className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer flex items-center space-x-1"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry Runner</span>
          </button>
        </div>
      )}

      {/* 3. SELF-VERIFIED PRACTICE BADGE */}
      <div className="px-3 py-2 bg-indigo-950/40 border border-indigo-800/40 rounded-xl flex flex-wrap items-center justify-between gap-2 text-[11px] text-indigo-300">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold text-white">Self-Verified Practice:</span>
          <span>In-browser execution provides immediate formative coding feedback. Official outcome mastery is verified through assessments.</span>
        </div>
        <span className="text-[10px] bg-indigo-900/60 px-2 py-0.5 rounded text-indigo-200 font-mono">
          Pyodide WASM (5s cap)
        </span>
      </div>

      {/* 4. IN-BROWSER CODE EDITOR & COMPILER TERMINAL */}
      <div className="bg-[#0B0F19] rounded-2xl border border-slate-800 shadow-xl overflow-hidden text-slate-200 font-mono text-xs">
        {/* Editor Window Bar */}
        <div className="px-4 py-3 bg-[#111827] border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2.5">
            {/* macOS-style window dots */}
            <div className="flex space-x-1.5">
              <div className="w-3 h-3 rounded-full bg-rose-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
            </div>
            <span className="text-slate-400 text-xs font-sans font-medium pl-1">
              solution.py
            </span>
            <span className="px-2 py-0.5 bg-slate-800 text-emerald-400 border border-emerald-500/30 rounded text-[10px] font-bold">
              In-Browser Pyodide (Python 3.11)
            </span>
          </div>

          <div className="flex items-center space-x-2 font-sans">
            <button
              type="button"
              onClick={handleCopy}
              className="px-2.5 py-1 bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded-md text-[11px] font-medium transition-colors flex items-center space-x-1 cursor-pointer"
              title="Copy solution code"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            {!readOnly && (
              <button
                type="button"
                onClick={handleReset}
                className="px-2.5 py-1 bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded-md text-[11px] font-medium transition-colors flex items-center space-x-1 cursor-pointer"
                title="Reset code to starter template"
              >
                <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                <span>Reset</span>
              </button>
            )}

            {!readOnly && (
              <button
                type="button"
                onClick={handleRunCode}
                disabled={compiling || !code.trim() || pyodideStatus === 'loading'}
                className="px-4 py-1.5 bg-[#EA580C] hover:bg-[#C2410C] disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer"
              >
                {compiling ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                <span>{compiling ? 'Running in Browser...' : 'Run & Test Code'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Code Input Area with Line Numbers */}
        <div className="relative flex min-h-[220px] max-h-[400px] overflow-hidden bg-[#0B0F19]">
          {/* Gutter Line Numbers */}
          <div className="py-4 pl-3 pr-2 select-none text-right text-slate-600 bg-[#0B0F19] border-r border-slate-800/60 font-mono text-xs w-10 shrink-0">
            {Array.from({ length: Math.max(lineCount, 12) }).map((_, idx) => (
              <div key={idx} className="leading-6">
                {idx + 1}
              </div>
            ))}
          </div>

          {/* Textarea editor */}
          <div className="relative flex-1">
            <textarea
              ref={textareaRef}
              value={code}
              onChange={handleCodeChange}
              onKeyDown={handleKeyDown}
              disabled={readOnly}
              spellCheck={false}
              placeholder="# Type your Python solution code here..."
              className="w-full h-full min-h-[220px] p-4 bg-transparent text-slate-100 font-mono text-xs leading-6 resize-none focus:outline-none focus:ring-0 selection:bg-[#EA580C]/30 placeholder:text-slate-600"
            />
          </div>
        </div>

        {/* Status footer inside editor */}
        <div className="px-4 py-2 bg-[#0E1526] border-t border-slate-800/80 flex items-center justify-between text-[11px] font-sans text-slate-400">
          <div className="flex items-center space-x-3 font-mono text-[10px]">
            <span>Lines: {lineCount}</span>
            <span>Length: {code.length}/10,000</span>
            <span>Timeout: 5.0s</span>
          </div>

          {compileResult && (
            <div className="flex items-center space-x-2">
              {lastRunCode !== null && code !== lastRunCode && (
                <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Edited since test run
                </span>
              )}
              <span className="flex items-center space-x-1 text-slate-300">
                <Clock className="w-3 h-3 text-slate-400" />
                <span className="font-mono">{compileResult.execution_time_ms}ms</span>
              </span>
              <span
                className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                  compileResult.all_passed
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                }`}
              >
                {compileResult.all_passed
                  ? 'All Test Cases Passed ✓'
                  : `${compileResult.passed_count}/${compileResult.total_count} Passed`}
              </span>
            </div>
          )}
        </div>

        {/* 5. COMPILER OUTPUT & TEST RESULTS DRAWER */}
        <div className="border-t border-slate-800 bg-[#0E1526]">
          {/* Output Tab Switcher */}
          <div className="px-4 pt-2.5 pb-1 flex items-center justify-between border-b border-slate-800/80 text-xs">
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setActiveTab('tests')}
                className={`px-3 py-1.5 rounded-t-lg font-bold flex items-center space-x-1.5 transition-colors cursor-pointer ${
                  activeTab === 'tests'
                    ? 'bg-[#1E293B] text-white border-t-2 border-orange-500'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Test Cases {compileResult ? `(${compileResult.passed_count}/${compileResult.total_count})` : ''}</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('console')}
                className={`px-3 py-1.5 rounded-t-lg font-bold flex items-center space-x-1.5 transition-colors cursor-pointer ${
                  activeTab === 'console'
                    ? 'bg-[#1E293B] text-white border-t-2 border-orange-500'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Terminal className="w-3.5 h-3.5 text-orange-400" />
                <span>Console Output</span>
                {compileResult?.stderr && (
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                )}
              </button>
            </div>

            {compileResult && (
              <span className="text-[10px] text-slate-400 font-sans">
                Self-verified practice, not counted toward mastery
              </span>
            )}
          </div>

          {/* Tab 1: Structured Test Cases Breakdown */}
          {activeTab === 'tests' && (
            <div className="p-4 space-y-2.5 max-h-56 overflow-y-auto">
              {compileResult ? (
                compileResult.results && compileResult.results.length > 0 ? (
                  compileResult.results.map((r) => (
                    <div
                      key={r.test_idx}
                      className={`p-3 rounded-xl border text-xs font-mono space-y-1.5 transition-colors ${
                        r.passed
                          ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200'
                          : 'bg-rose-950/20 border-rose-800/40 text-rose-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-2 font-bold">
                          {r.passed ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          ) : (
                            <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                          )}
                          <span>Test Case #{r.test_idx}: <code className="text-white font-semibold">{r.call}</code></span>
                        </span>
                        <span className="text-[10px] text-slate-400 font-sans">{r.input_desc}</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                        <div>
                          <span className="text-slate-400">Expected: </span>
                          <span className="text-white font-bold">{r.expected}</span>
                        </div>
                        <div>
                          <span className="text-slate-400">Actual: </span>
                          <span className={r.passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                            {r.actual !== null ? r.actual : 'None'}
                          </span>
                        </div>
                      </div>

                      {r.error && (
                        <div className="text-[11px] text-rose-300 bg-rose-950/40 p-2 rounded border border-rose-800/40 mt-1">
                          Error: {r.error}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-slate-400 text-xs">
                    No individual test case results. Check the terminal console for syntax errors.
                  </div>
                )
              ) : (
                <div className="py-6 text-center text-slate-500 text-xs space-y-1">
                  <Play className="w-5 h-5 mx-auto text-slate-600 mb-1" />
                  <p>Click <strong className="text-slate-300">"Run & Test Code"</strong> above to run your code against test cases in Pyodide.</p>
                  <p className="text-[11px] text-slate-600">Runs locally in-browser with zero latency.</p>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Terminal Console Stdout / Stderr */}
          {activeTab === 'console' && (
            <div className="p-4 max-h-56 overflow-y-auto font-mono text-xs text-slate-300 space-y-2 bg-[#090D16]">
              <div className="text-slate-500 text-[10px] flex items-center space-x-1.5 pb-1 border-b border-slate-800">
                <span>$ python -u solution.py (Pyodide Worker)</span>
              </div>

              {compileResult?.stdout && (
                <div className="text-emerald-300 whitespace-pre-wrap leading-relaxed">
                  {compileResult.stdout}
                </div>
              )}

              {compileResult?.stderr && (
                <div className="text-rose-400 whitespace-pre-wrap leading-relaxed bg-rose-950/30 p-3 rounded-lg border border-rose-900/50">
                  <div className="font-bold flex items-center space-x-1 pb-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    <span>Compiler Traceback / Runtime Error:</span>
                  </div>
                  {compileResult.stderr}
                </div>
              )}

              {!compileResult?.stdout && !compileResult?.stderr && (
                <div className="text-slate-600 text-xs italic py-4 text-center">
                  Terminal console is clean. Run code to view stdout and error traces.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

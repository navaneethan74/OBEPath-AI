// Web Worker for In-Browser Python Execution with Pyodide
// Pinned CDN version (v0.26.4 - stable, production-grade release)
const PYODIDE_CDN_MJS = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.mjs';
const PYODIDE_INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';

const MAX_OUTPUT_BYTES = 64 * 1024; // 64 KB cap
const MAX_CODE_CHARS = 10000;       // 10,000 characters cap

let pyodideInstance: any = null;
let initPromise: Promise<any> | null = null;

async function getPyodide(): Promise<any> {
  if (pyodideInstance) return pyodideInstance;
  if (initPromise) return initPromise;

  initPromise = (async () => {
    try {
      // Dynamic ES module import from CDN for module web worker
      const pyodideModule: any = await import(/* @vite-ignore */ PYODIDE_CDN_MJS);
      const loadPyodide = pyodideModule?.loadPyodide || pyodideModule?.default?.loadPyodide;

      if (typeof loadPyodide !== 'function') {
        throw new Error('Pyodide load function is not available in imported module.');
      }

      const py = await loadPyodide({
        indexURL: PYODIDE_INDEX_URL
      });

      pyodideInstance = py;
      return py;
    } catch (err: any) {
      throw new Error(`Failed to load Pyodide module from CDN: ${err?.message || err}`);
    }
  })();

  return initPromise;
}

self.onmessage = async (e: MessageEvent) => {
  const { type, id, code, testCases } = e.data || {};

  if (type === 'INIT') {
    try {
      await getPyodide();
      self.postMessage({ type: 'INIT_SUCCESS' });
    } catch (err: any) {
      initPromise = null;
      pyodideInstance = null;
      self.postMessage({ type: 'INIT_ERROR', error: err?.message || String(err) });
    }
    return;
  }

  if (type === 'RUN') {
    const startTime = performance.now();

    // 1. Cap code length
    if (typeof code !== 'string' || code.length > MAX_CODE_CHARS) {
      self.postMessage({
        type: 'RUN_SUCCESS',
        id,
        result: {
          success: false,
          all_passed: false,
          passed_count: 0,
          total_count: Array.isArray(testCases) ? testCases.length : 0,
          percentage: 0.0,
          stdout: '',
          stderr: `Code length exceeds maximum allowed limit of ${MAX_CODE_CHARS} characters.`,
          results: [],
          execution_time_ms: 0,
          self_verified: true
        }
      });
      return;
    }

    try {
      const py = await getPyodide();

      // Setup in-memory stdout/stderr capture in Python with 64KB cap
      const harnessScript = `
import sys, io, json

class CappedStringIO:
    def __init__(self, max_bytes=65536):
        self.buf = io.StringIO()
        self.max_bytes = max_bytes
        self.truncated = False
        self.written = 0

    def write(self, s):
        if self.truncated:
            return
        if self.written + len(s) > self.max_bytes:
            allowed = max(0, self.max_bytes - self.written)
            self.buf.write(s[:allowed])
            self.buf.write("\\n[Output truncated at 64 KB limit]")
            self.truncated = True
            self.written = self.max_bytes
        else:
            self.buf.write(s)
            self.written += len(s)

    def getvalue(self):
        return self.buf.getvalue()

    def flush(self):
        pass

__stdout_capture = CappedStringIO(${MAX_OUTPUT_BYTES})
__stderr_capture = CappedStringIO(${MAX_OUTPUT_BYTES})
__orig_stdout = sys.stdout
__orig_stderr = sys.stderr
sys.stdout = __stdout_capture
sys.stderr = __stderr_capture
`;

      await py.runPythonAsync(harnessScript);

      // Clean execution environment for student code
      const studentScope = py.globals.get('dict')();
      let execError = null;

      try {
        await py.runPythonAsync(code, { globals: studentScope });
      } catch (err: any) {
        execError = err?.message || String(err);
      }

      // Restore stdout and retrieve captured buffers
      await py.runPythonAsync(`
sys.stdout = __orig_stdout
sys.stderr = __orig_stderr
__final_stdout = __stdout_capture.getvalue()
__final_stderr = __stderr_capture.getvalue()
`);

      const stdout = py.globals.get('__final_stdout') || '';
      let stderr = py.globals.get('__final_stderr') || '';
      if (execError) {
        stderr = (stderr ? stderr + '\n' : '') + execError;
      }

      // Truncate to 64KB max if string length exceeds limit
      const finalStdout = stdout.length > MAX_OUTPUT_BYTES 
        ? stdout.slice(0, MAX_OUTPUT_BYTES) + '\n[Output truncated at 64 KB limit]' 
        : stdout;
      const finalStderr = stderr.length > MAX_OUTPUT_BYTES 
        ? stderr.slice(0, MAX_OUTPUT_BYTES) + '\n[Output truncated at 64 KB limit]' 
        : stderr;

      // Evaluate predefined test cases
      const testResults: any[] = [];
      let passedCount = 0;
      const tcs = Array.isArray(testCases) ? testCases : [];

      if (!execError) {
        for (let i = 0; i < tcs.length; i++) {
          const tc = tcs[i] || {};
          const callExpr = String(tc.call || '').trim();
          const expected = String(tc.expected ?? '').trim();
          const inputDesc = tc.input_desc || callExpr;

          // Validate predefined call pattern: simple alphanumeric function call identifier
          // Enforces that only predefined calls (e.g. solve(1, 2) or func_name()) are run
          const isSafeCall = /^[a-zA-Z_][a-zA-Z0-9_]*\(.*?\)$/s.test(callExpr);

          if (!isSafeCall) {
            testResults.push({
              test_idx: i + 1,
              call: callExpr,
              input_desc: inputDesc,
              expected,
              actual: 'Invalid Call Pattern',
              passed: false,
              error: 'Invalid or unsafe call pattern'
            });
            continue;
          }

          try {
            // Evaluate student function call inside studentScope
            const rawActual = await py.runPythonAsync(callExpr, { globals: studentScope });
            let actualStr = '';
            if (rawActual === undefined || rawActual === null) {
              actualStr = 'None';
            } else if (typeof rawActual === 'boolean') {
              actualStr = rawActual ? 'True' : 'False';
            } else if (rawActual?.toJs) {
              try {
                const jsVal = rawActual.toJs();
                actualStr = JSON.stringify(jsVal);
              } catch {
                actualStr = String(rawActual);
              }
            } else {
              actualStr = String(rawActual);
            }

            // Normalise comparisons for common python output differences
            const cleanActual = actualStr.trim().replace(/^['"]|['"]$/g, '');
            const cleanExpected = expected.trim().replace(/^['"]|['"]$/g, '');
            let passed = cleanActual === cleanExpected || actualStr.trim() === expected;

            // Numeric equivalence (e.g. JS float representation '5' vs Python '5.0')
            if (!passed && cleanActual !== '' && cleanExpected !== '') {
              const numActual = Number(cleanActual);
              const numExpected = Number(cleanExpected);
              if (!Number.isNaN(numActual) && !Number.isNaN(numExpected)) {
                passed = numActual === numExpected;
              }
            }

            // JSON equivalence (e.g. dictionaries / lists with single vs double quotes)
            if (!passed) {
              try {
                const jsonActual = JSON.parse(cleanActual.replace(/'/g, '"'));
                const jsonExpected = JSON.parse(cleanExpected.replace(/'/g, '"'));
                passed = JSON.stringify(jsonActual) === JSON.stringify(jsonExpected);
              } catch {
                // Ignore parse errors
              }
            }

            if (passed) passedCount++;

            testResults.push({
              test_idx: i + 1,
              call: callExpr,
              input_desc: inputDesc,
              expected,
              actual: actualStr,
              passed,
              error: null
            });
          } catch (tcErr: any) {
            testResults.push({
              test_idx: i + 1,
              call: callExpr,
              input_desc: inputDesc,
              expected,
              actual: 'Execution Error',
              passed: false,
              error: tcErr?.message || String(tcErr)
            });
          }
        }
      } else {
        // Code compilation/runtime failed
        for (let i = 0; i < tcs.length; i++) {
          const tc = tcs[i] || {};
          testResults.push({
            test_idx: i + 1,
            call: tc.call || '',
            input_desc: tc.input_desc || tc.call || '',
            expected: String(tc.expected ?? ''),
            actual: 'Syntax/Runtime Error',
            passed: false,
            error: execError
          });
        }
      }

      const totalCount = tcs.length;
      const allPassed = totalCount > 0 && passedCount === totalCount && !execError;
      const percentage = totalCount > 0 ? Math.round((passedCount / totalCount) * 1000) / 10 : 0.0;
      const executionTimeMs = Math.round(performance.now() - startTime);

      self.postMessage({
        type: 'RUN_SUCCESS',
        id,
        result: {
          success: !execError,
          all_passed: allPassed,
          passed_count: passedCount,
          total_count: totalCount,
          percentage,
          stdout: finalStdout,
          stderr: finalStderr,
          results: testResults,
          execution_time_ms: executionTimeMs,
          self_verified: true
        }
      });
    } catch (fatalErr: any) {
      self.postMessage({
        type: 'RUN_SUCCESS',
        id,
        result: {
          success: false,
          all_passed: false,
          passed_count: 0,
          total_count: Array.isArray(testCases) ? testCases.length : 0,
          percentage: 0.0,
          stdout: '',
          stderr: `Pyodide Runner Error: ${fatalErr?.message || String(fatalErr)}`,
          results: [],
          execution_time_ms: Math.round(performance.now() - startTime),
          self_verified: true
        }
      });
    }
  }
};

import { CodeExecutionResult } from '../types';

export type PyodideStatus = 'uninitialized' | 'loading' | 'ready' | 'error';

class PyodideRunnerService {
  private worker: Worker | null = null;
  private status: PyodideStatus = 'uninitialized';
  private errorMessage: string | null = null;
  private initPromise: Promise<void> | null = null;
  private statusListeners: Array<(status: PyodideStatus, error: string | null) => void> = [];

  public getStatus(): PyodideStatus {
    return this.status;
  }

  public getErrorMessage(): string | null {
    return this.errorMessage;
  }

  public onStatusChange(callback: (status: PyodideStatus, error: string | null) => void): () => void {
    this.statusListeners.push(callback);
    callback(this.status, this.errorMessage);
    return () => {
      this.statusListeners = this.statusListeners.filter(cb => cb !== callback);
    };
  }

  private notifyListeners(): void {
    this.statusListeners.forEach(cb => cb(this.status, this.errorMessage));
  }

  public isSupported(): boolean {
    return typeof window !== 'undefined' && typeof Worker !== 'undefined' && typeof WebAssembly !== 'undefined';
  }

  private createWorker(): Worker {
    if (!this.isSupported()) {
      throw new Error('Your browser does not support WebAssembly or Web Workers required for the in-browser Python runner.');
    }
    // Instantiate module worker via Vite URL syntax
    return new Worker(
      new URL('../workers/pyodide.worker.ts', import.meta.url),
      { type: 'module' }
    );
  }

  public async initPyodide(): Promise<void> {
    if (this.status === 'ready') return;
    if (this.initPromise) return this.initPromise;

    if (!this.isSupported()) {
      this.status = 'error';
      this.errorMessage = 'WebAssembly or Web Workers are not supported in this browser.';
      this.notifyListeners();
      throw new Error(this.errorMessage);
    }

    this.status = 'loading';
    this.errorMessage = null;
    this.notifyListeners();

    this.initPromise = new Promise<void>((resolve, reject) => {
      try {
        if (this.worker) {
          this.worker.terminate();
          this.worker = null;
        }

        const worker = this.createWorker();
        this.worker = worker;

        const handleInitMessage = (e: MessageEvent) => {
          const { type, error } = e.data || {};
          if (type === 'INIT_SUCCESS') {
            worker.removeEventListener('message', handleInitMessage);
            this.status = 'ready';
            this.errorMessage = null;
            this.notifyListeners();
            resolve();
          } else if (type === 'INIT_ERROR') {
            worker.removeEventListener('message', handleInitMessage);
            this.status = 'error';
            this.errorMessage = error || 'Failed to initialize in-browser Pyodide environment.';
            this.notifyListeners();
            reject(new Error(this.errorMessage || 'Initialization failed.'));
          }
        };

        worker.addEventListener('message', handleInitMessage);
        worker.addEventListener('error', (err) => {
          this.status = 'error';
          this.errorMessage = err.message || 'Worker initialization failed.';
          this.notifyListeners();
          reject(new Error(this.errorMessage || 'Worker error.'));
        });

        worker.postMessage({ type: 'INIT' });
      } catch (err: any) {
        this.status = 'error';
        this.errorMessage = err?.message || 'Could not instantiate Web Worker.';
        this.notifyListeners();
        reject(err);
      }
    }).finally(() => {
      this.initPromise = null;
    });

    return this.initPromise;
  }

  public async retryInitPyodide(): Promise<void> {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    this.status = 'uninitialized';
    this.errorMessage = null;
    this.notifyListeners();
    return this.initPyodide();
  }

  /**
   * Executes student Python code in the Web Worker.
   * Strictly enforces:
   * 1. 5-second timeout (terminates worker on timeout)
   * 2. 10,000 character code length limit
   * 3. 64 KB output buffer cap (enforced inside worker)
   * 4. Predefined call patterns only (no arbitrary client eval)
   * 5. Self-verified marking
   */
  public async runCode(
    code: string,
    testCases: any[] = []
  ): Promise<CodeExecutionResult> {
    // 1. Cap code length
    if (typeof code !== 'string' || code.length > 10000) {
      return {
        success: false,
        all_passed: false,
        passed_count: 0,
        total_count: testCases.length,
        percentage: 0.0,
        stdout: '',
        stderr: 'Code length exceeds maximum allowed limit of 10,000 characters.',
        results: [],
        execution_time_ms: 0,
        self_verified: true
      };
    }

    // Ensure Pyodide is initialized
    if (this.status !== 'ready') {
      try {
        await this.initPyodide();
      } catch (err: any) {
        return {
          success: false,
          all_passed: false,
          passed_count: 0,
          total_count: testCases.length,
          percentage: 0.0,
          stdout: '',
          stderr: `In-browser runner failed to initialize: ${err?.message || err}. Please click Retry.`,
          results: [],
          execution_time_ms: 0,
          self_verified: true
        };
      }
    }

    const runId = Math.random().toString(36).slice(2);
    const worker = this.worker;
    if (!worker) {
      return {
        success: false,
        all_passed: false,
        passed_count: 0,
        total_count: testCases.length,
        percentage: 0.0,
        stdout: '',
        stderr: 'Worker is unavailable.',
        results: [],
        execution_time_ms: 0,
        self_verified: true
      };
    }

    return new Promise<CodeExecutionResult>((resolve) => {
      let isSettled = false;
      const TIMEOUT_MS = 5000; // 5-second timeout

      // Timeout watchdog: Terminate worker if execution exceeds 5 seconds
      const timeoutTimer = setTimeout(() => {
        if (isSettled) return;
        isSettled = true;

        // Force terminate the hung worker to stop infinite loops / hangs
        if (this.worker) {
          this.worker.terminate();
          this.worker = null;
        }
        this.status = 'uninitialized';
        this.notifyListeners();

        // Re-initialize worker in the background for subsequent runs
        this.initPyodide().catch(() => {});

        resolve({
          success: false,
          all_passed: false,
          passed_count: 0,
          total_count: testCases.length,
          percentage: 0.0,
          stdout: '',
          stderr: `Time Limit Exceeded: Execution terminated after exceeding the 5.0 second safety limit. Check for infinite loops or heavy operations.`,
          results: testCases.map((tc, idx) => ({
            test_idx: idx + 1,
            call: tc.call || '',
            input_desc: tc.input_desc || tc.call || '',
            expected: String(tc.expected ?? ''),
            actual: 'Timed Out',
            passed: false,
            error: 'Timeout > 5.0s'
          })),
          execution_time_ms: TIMEOUT_MS,
          self_verified: true
        });
      }, TIMEOUT_MS);

      const onMessage = (e: MessageEvent) => {
        const { type, id, result } = e.data || {};
        if (type === 'RUN_SUCCESS' && id === runId) {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutTimer);
          worker.removeEventListener('message', onMessage);
          resolve(result);
        }
      };

      worker.addEventListener('message', onMessage);

      // Post execution task to worker
      worker.postMessage({
        type: 'RUN',
        id: runId,
        code,
        testCases
      });
    });
  }
}

export const pyodideRunner = new PyodideRunnerService();

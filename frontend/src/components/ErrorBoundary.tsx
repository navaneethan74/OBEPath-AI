import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onRetry?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an unhandled render error:', error, errorInfo);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-white border border-rose-200 rounded-2xl shadow-xs space-y-4 my-4 animate-fadeIn">
          <div className="flex items-start space-x-3 text-rose-700">
            <span className="p-2 bg-rose-100 rounded-xl mt-0.5">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
            </span>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-900">
                {this.props.fallbackTitle || 'Unable to display this dashboard tab'}
              </h3>
              <p className="text-xs text-rose-600">
                {this.state.error?.message || 'An unexpected rendering error occurred while loading this view.'}
              </p>
              <p className="text-[11px] text-slate-400">
                The rest of the dashboard remains operational. You can attempt to reload this section below.
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-end">
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5 text-[#635BFF]" />
              <span>Retry Tab</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

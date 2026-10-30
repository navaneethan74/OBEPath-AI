import React, { useState } from 'react';
import { Copy, Check, Info } from 'lucide-react';

interface MarkdownViewProps {
  content: string;
  className?: string;
}

const CodeBlock: React.FC<{ code: string; language?: string }> = ({ code, language }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code to clipboard', err);
    }
  };

  return (
    <div className="my-3 rounded-xl border border-[#E5E5DF] overflow-hidden bg-slate-900 text-slate-100 shadow-xs">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-xs">
        <span className="font-mono text-[11px] text-slate-300 uppercase tracking-wider font-semibold">
          {language || 'Code'}
        </span>
        <button
          onClick={handleCopy}
          className="inline-flex items-center space-x-1 text-[11px] text-slate-300 hover:text-white px-2 py-0.5 rounded hover:bg-slate-700 transition-colors cursor-pointer"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-3.5 text-xs sm:text-sm font-mono leading-relaxed bg-[#0B132B]/80 text-slate-100">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, className = '' }) => {
  if (!content) return null;

  // Split lines and group code blocks
  const lines = content.split('\n');
  const blocks: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeBlockLines: string[] = [];
  let codeLanguage = '';

  const renderFormattedInline = (text: string) => {
    const parts: (string | React.ReactNode)[] = [];
    const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={match.index} className="font-bold text-slate-900">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('*') && token.endsWith('*')) {
        parts.push(
          <em key={match.index} className="italic text-slate-800">
            {token.slice(1, -1)}
          </em>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code
            key={match.index}
            className="px-1.5 py-0.5 rounded bg-orange-50 text-orange-800 font-mono text-xs border border-orange-200"
          >
            {token.slice(1, -1)}
          </code>
        );
      }
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Check code block fence
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // End of code block
        blocks.push(
          <CodeBlock
            key={`code-${i}`}
            code={codeBlockLines.join('\n')}
            language={codeLanguage}
          />
        );
        inCodeBlock = false;
        codeBlockLines = [];
        codeLanguage = '';
      } else {
        // Start of code block
        inCodeBlock = true;
        codeLanguage = trimmed.slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      continue;
    }

    // Empty line
    if (!trimmed) {
      blocks.push(<div key={`empty-${i}`} className="h-1.5" />);
      continue;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      blocks.push(
        <h4 key={`h3-${i}`} className="text-sm font-bold text-slate-900 mt-3 mb-1">
          {renderFormattedInline(trimmed.slice(4))}
        </h4>
      );
      continue;
    }
    if (trimmed.startsWith('## ')) {
      blocks.push(
        <h3 key={`h2-${i}`} className="text-base font-bold text-slate-900 mt-3.5 mb-1.5">
          {renderFormattedInline(trimmed.slice(3))}
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith('# ')) {
      blocks.push(
        <h2 key={`h1-${i}`} className="text-lg font-bold text-slate-900 mt-4 mb-2">
          {renderFormattedInline(trimmed.slice(2))}
        </h2>
      );
      continue;
    }

    // Important notes / Blockquotes / Alerts
    if (trimmed.startsWith('> ') || trimmed.startsWith('Note:') || trimmed.startsWith('Important:')) {
      const calloutText = trimmed.startsWith('> ') ? trimmed.slice(2) : trimmed;
      blocks.push(
        <div
          key={`note-${i}`}
          className="my-2.5 p-3 rounded-xl bg-orange-50/70 border-l-3 border-[#EA580C] text-xs sm:text-sm text-slate-800 flex items-start space-x-2 shadow-2xs"
        >
          <Info className="w-4 h-4 text-[#EA580C] flex-shrink-0 mt-0.5" />
          <div className="flex-1">{renderFormattedInline(calloutText)}</div>
        </div>
      );
      continue;
    }

    // Bullet points
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      blocks.push(
        <div key={`bullet-${i}`} className="flex items-start space-x-2 pl-2 my-0.5">
          <span className="text-orange-600 font-bold mt-1 text-xs">•</span>
          <span className="flex-1">{renderFormattedInline(trimmed.slice(2))}</span>
        </div>
      );
      continue;
    }

    // Numbered steps
    if (/^\d+\.\s/.test(trimmed)) {
      const match = trimmed.match(/^(\d+\.)\s(.*)/);
      if (match) {
        blocks.push(
          <div key={`num-${i}`} className="flex items-start space-x-2 pl-2 my-0.5">
            <span className="text-orange-600 font-mono text-xs font-semibold mt-0.5">
              {match[1]}
            </span>
            <span className="flex-1">{renderFormattedInline(match[2])}</span>
          </div>
        );
        continue;
      }
    }

    // Normal paragraph
    blocks.push(
      <p key={`p-${i}`} className="my-1">
        {renderFormattedInline(line)}
      </p>
    );
  }

  // Handle unclosed code block if any
  if (inCodeBlock && codeBlockLines.length > 0) {
    blocks.push(
      <CodeBlock
        key="code-unclosed"
        code={codeBlockLines.join('\n')}
        language={codeLanguage}
      />
    );
  }

  return (
    <div className={`space-y-1 text-slate-800 text-sm leading-relaxed ${className}`}>
      {blocks}
    </div>
  );
};

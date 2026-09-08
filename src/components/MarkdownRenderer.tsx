import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  // Pre-process content to normalize line breaks and prevent table parsing issues
  // Ensure tables with preceding text have a newline separation
  let normalizedContent = content
    // Normalize newlines
    .replace(/\r\n/g, '\n')
    // Fix tables immediately following text without double newlines
    .replace(/([^\n])\n(\|.*\|)\n(\|[-:\s|]+\|)/g, '$1\n\n$2\n$3');

  return (
    <div className="prose prose-sm prose-slate max-w-none text-slate-700">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h2 className="font-black text-[15px] text-slate-900 mt-3 mb-2 pb-1 border-b border-slate-100 flex items-center gap-1.5 first:mt-0 tracking-tight">
              {children}
            </h2>
          ),
          h2: ({ children }) => (
            <h3 className="font-extrabold text-[14px] text-slate-900 mt-3 mb-1.5 pb-0.5 first:mt-0 tracking-tight">
              {children}
            </h3>
          ),
          h3: ({ children }) => (
            <h4 className="font-bold text-[13.5px] text-purple-950 mt-2.5 mb-1 first:mt-0 tracking-tight">
              {children}
            </h4>
          ),
          h4: ({ children }) => (
            <h5 className="font-semibold text-[13px] text-slate-800 mt-2 mb-1 first:mt-0">
              {children}
            </h5>
          ),

          // Paragraphs & text
          p: ({ children }) => (
            <p className="text-[13px] leading-relaxed text-slate-700 my-1.5 first:mt-0 last:mb-0">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-slate-900">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-slate-800">
              {children}
            </em>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="list-disc pl-5 space-y-1.5 my-2 text-slate-700">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 space-y-1.5 my-2 text-slate-700">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-[13px] leading-relaxed pl-0.5">
              {children}
            </li>
          ),

          // GitHub Flavored Markdown Tables
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 rounded-xl border border-slate-200/80 shadow-xs bg-white">
              <table className="min-w-full divide-y divide-slate-200 text-left text-[12.5px]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-purple-50/90 text-purple-950 font-bold border-b border-purple-100/90">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="px-3.5 py-2.5 font-bold text-purple-900 text-[12px] tracking-wide">
              {children}
            </th>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-slate-100 bg-white">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="even:bg-slate-50/60 hover:bg-purple-50/30 transition-colors">
              {children}
            </tr>
          ),
          td: ({ children }) => (
            <td className="px-3.5 py-2 text-slate-700 leading-snug align-top text-[12.5px]">
              {children}
            </td>
          ),

          // Code
          code: ({ className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');
            const isCodeBlock = Boolean(match) || (typeof children === 'string' && children.includes('\n'));
            
            if (!isCodeBlock) {
              return (
                <code className="bg-purple-50 text-purple-700 font-mono text-[11.5px] px-1.5 py-0.5 rounded border border-purple-100 font-semibold" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className="font-mono text-[11.5px] text-slate-100" {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="bg-slate-900 text-slate-100 p-3 rounded-xl font-mono text-xs overflow-x-auto my-2.5 border border-slate-800 shadow-inner">
              {children}
            </pre>
          ),

          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-purple-500 bg-purple-50/40 px-3.5 py-2 rounded-r-lg my-2.5 text-slate-700 italic text-[12.5px]">
              {children}
            </blockquote>
          ),

          // Horizontal rule
          hr: () => (
            <hr className="border-t border-slate-200 my-3" />
          ),

          // Links
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-600 hover:text-purple-800 hover:underline font-semibold"
            >
              {children}
            </a>
          ),

          // HTML line breaks
          br: () => <br className="my-0.5" />
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;

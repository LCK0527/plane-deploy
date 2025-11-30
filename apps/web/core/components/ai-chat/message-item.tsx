"use client";

import { observer } from "mobx-react";
import { useState, useMemo } from "react";
import React from "react";
import { Edit2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
// plane imports
import { Button } from "@plane/propel/button";
import { cn } from "@plane/utils";
// types
import type { AIChatMessage } from "@/services/ai-chat.service";

interface Props {
  message: AIChatMessage;
  onEdit?: (messageId: string) => void;
  isUser: boolean;
}

export const AIChatMessageItem = observer((props: Props) => {
  const { message, onEdit, isUser } = props;
  const [isHovered, setIsHovered] = useState(false);

  const handleEdit = () => {
    if (onEdit) {
      onEdit(message.id);
    }
  };

  // Process content to support multiple math formats
  const processedContent = useMemo(() => {
    let content = String(message.content || "");
    
    let matchCount = 0;
    
    // Step 1: Convert LaTeX standard format \[...\] to $$...$$ (block math)
    // This is the standard LaTeX math display format
    content = content.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
      const trimmed = formula.trim();
      if (trimmed.length > 0 && trimmed.length < 1000) {
        matchCount++;
        console.log(`[Math Renderer] Converted LaTeX format \\[...\\]:`, trimmed.substring(0, 100));
        return `$$${trimmed}$$`;
      }
      return match;
    });
    
    // Step 2: Convert LaTeX inline format \(...\) to $...$ (inline math)
    // This is the standard LaTeX inline math format
    content = content.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
      const trimmed = formula.trim();
      if (trimmed.length > 0 && trimmed.length < 500) {
        matchCount++;
        console.log(`[Math Renderer] Converted LaTeX inline format \\(...\\):`, trimmed.substring(0, 100));
        return `$${trimmed}$`;
      }
      return match;
    });
    
    // Step 3: Convert square bracket format [formula] to $$...$$ (block math)
    // This handles formats like [ \Phi_E = E \cdot A = E \cdot (2 \pi r L) ] (with spaces)
    // Only process if not already converted
    const matches: string[] = [];
    content = content.replace(
      /\[\s*([^[\]]+?)\s*\]/g,
      (match, formula) => {
        const trimmed = formula.trim();
        matches.push(match);
        
        // Very lenient detection: if it contains backslash, treat as math
        // This catches all LaTeX commands: \Phi, \cdot, \pi, \frac, \text, \varepsilon_0, etc.
        const hasBackslash = /\\/.test(trimmed);
        
        // Convert to block math format if it has LaTeX commands
        if (hasBackslash && trimmed.length < 1000 && trimmed.length > 1) {
          matchCount++;
          console.log(`[Math Renderer] Converted bracket format [formula]:`, trimmed.substring(0, 100));
          return `$$${trimmed}$$`;
        }
        
        // Also check for math patterns without backslash (like E = ... with subscripts)
        const hasMathOperators = /[=\+\-\*\/]/.test(trimmed);
        const hasSubscripts = /_[a-zA-Z\{]/.test(trimmed);
        const hasGreek = /[α-ωΑ-Ωπ∑∫∂∈∞±×÷√∇∆ε]/.test(trimmed);
        
        if ((hasMathOperators && (hasSubscripts || hasGreek)) && trimmed.length < 1000 && trimmed.length > 1) {
          matchCount++;
          console.log(`[Math Renderer] Converted bracket format (operators/subscripts/greek):`, trimmed.substring(0, 100));
          return `$$${trimmed}$$`;
        }
        
        return match;
      }
    );
    
    // Debug: log if we found any matches
    if (typeof window !== 'undefined' && matchCount > 0) {
      console.log(`[Math Renderer] Total converted: ${matchCount} math formula(s)`);
    }
    
    return content;
  }, [message.content]);

  // Markdown components for better styling
  const markdownComponents = {
    h1: ({ children }: { children: React.ReactNode }) => (
      <h1 className="text-lg font-semibold mb-2 mt-4 first:mt-0">{children}</h1>
    ),
    h2: ({ children }: { children: React.ReactNode }) => (
      <h2 className="text-base font-semibold mb-2 mt-3 first:mt-0">{children}</h2>
    ),
    h3: ({ children }: { children: React.ReactNode }) => (
      <h3 className="text-sm font-semibold mb-1 mt-2 first:mt-0">{children}</h3>
    ),
    p: ({ children }: { children: React.ReactNode }) => (
      <p className="mb-2 last:mb-0">{children}</p>
    ),
    ul: ({ children }: { children: React.ReactNode }) => (
      <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>
    ),
    ol: ({ children }: { children: React.ReactNode }) => (
      <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>
    ),
    li: ({ children }: { children: React.ReactNode }) => (
      <li className="leading-relaxed">{children}</li>
    ),
    pre: ({ children }: { children: React.ReactNode }) => {
      // Check if children contains a code element (code block structure from react-markdown)
      const childrenArray = React.Children.toArray(children);
      const hasCodeChild = childrenArray.some(
        (child) => React.isValidElement(child) && child.type === "code"
      );
      
      if (hasCodeChild) {
        // This is a code block: pre > code
        // Style the pre element as a code block container
        return (
          <pre
            className={cn(
              "p-3 rounded text-sm font-mono overflow-x-auto my-2 whitespace-pre-wrap",
              isUser ? "bg-white/20 text-white" : "bg-custom-background-90 text-custom-text-100"
            )}
          >
            {children}
          </pre>
        );
      }
      
      // Regular pre element (not a code block)
      return (
        <pre
          className={cn(
            "p-3 rounded text-sm font-mono overflow-x-auto my-2 whitespace-pre-wrap",
            isUser ? "bg-white/20 text-white" : "bg-custom-background-90 text-custom-text-100"
          )}
        >
          {children}
        </pre>
      );
    },
    code: ({ children, className, ...props }: { children: React.ReactNode; className?: string; [key: string]: any }) => {
      // Check if this is a code block (has className with language-*)
      const match = /language-(\w+)/.exec(className || "");
      const isCodeBlock = !!match || !!className;
      
      if (isCodeBlock) {
        // This is a code block (inside a pre element)
        // The pre element handles the container styling
        // Just preserve the language class and render content
        return (
          <code className={className} {...props}>
            {children}
          </code>
        );
      }
      
      // Inline code
      return (
        <code
          className={cn(
            "px-1.5 py-0.5 rounded text-xs font-mono",
            isUser ? "bg-white/20 text-white" : "bg-custom-background-90 text-custom-text-100"
          )}
          {...props}
        >
          {children}
        </code>
      );
    },
    blockquote: ({ children }: { children: React.ReactNode }) => (
      <blockquote
        className={cn(
          "border-l-2 pl-3 my-2 italic",
          isUser ? "border-white/30" : "border-custom-border-300"
        )}
      >
        {children}
      </blockquote>
    ),
    a: ({ href, children }: { href?: string; children: React.ReactNode }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "underline hover:no-underline",
          isUser ? "text-white/90" : "text-custom-primary-100"
        )}
      >
        {children}
      </a>
    ),
    strong: ({ children }: { children: React.ReactNode }) => (
      <strong className="font-semibold">{children}</strong>
    ),
    em: ({ children }: { children: React.ReactNode }) => (
      <em className="italic">{children}</em>
    ),
    table: ({ children }: { children: React.ReactNode }) => (
      <div className="overflow-x-auto my-2">
        <table
          className={cn(
            "min-w-full border-collapse border",
            isUser ? "border-white/30" : "border-custom-border-300"
          )}
        >
          {children}
        </table>
      </div>
    ),
    thead: ({ children }: { children: React.ReactNode }) => (
      <thead className={cn(isUser ? "bg-white/20" : "bg-custom-background-90")}>
        {children}
      </thead>
    ),
    tbody: ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>,
    tr: ({ children }: { children: React.ReactNode }) => (
      <tr className={cn("border-b", isUser ? "border-white/30" : "border-custom-border-300")}>
        {children}
      </tr>
    ),
    th: ({ children }: { children: React.ReactNode }) => (
      <th
        className={cn(
          "border px-2 py-1 text-left font-semibold",
          isUser ? "border-white/30" : "border-custom-border-300"
        )}
      >
        {children}
      </th>
    ),
    td: ({ children }: { children: React.ReactNode }) => (
      <td
        className={cn(
          "border px-2 py-1",
          isUser ? "border-white/30" : "border-custom-border-300"
        )}
      >
        {children}
      </td>
    ),
  };

  return (
    <div
      className={cn(
        "group relative flex gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2 relative",
          isUser
            ? "bg-custom-primary-100 text-white"
            : "bg-custom-background-80 text-custom-text-100"
        )}
      >
        {isUser && isHovered && onEdit && (
          <button
            onClick={handleEdit}
            className="absolute -left-8 top-0 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-custom-background-90 rounded"
            aria-label="編輯並重新開始對話"
          >
            <Edit2 className="h-4 w-4 text-custom-text-400" />
          </button>
        )}
        <div className={cn(
          "text-sm break-words",
          isUser ? "text-white" : "text-custom-text-100",
          "[&_.katex]:text-inherit"
        )}>
          <ReactMarkdown 
            remarkPlugins={[remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={markdownComponents}
          >
            {processedContent}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
});


"use client";

import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { localizeReportMarkdown } from "@/lib/reportLocalize";

type MarkdownViewProps = {
  content: string;
  className?: string;
  /** Apply Chinese glosses to report structural headings (default true). */
  localize?: boolean;
};

function isExternalHref(href?: string): boolean {
  if (!href) return false;
  return /^https?:\/\//i.test(href) || href.startsWith("//");
}

function looksLikeCitation(href?: string, childrenText?: string): boolean {
  if (!href && !childrenText) return false;
  const t = `${href || ""} ${childrenText || ""}`.toLowerCase();
  return (
    t.includes("http") ||
    t.includes("arxiv") ||
    t.includes("ssrn") ||
    t.includes("source") ||
    t.includes("引用") ||
    t.includes("参考") ||
    /\[\d+\]/.test(childrenText || "") ||
    /^\d+$/.test((childrenText || "").trim())
  );
}

const components: Components = {
  a({ href, children }) {
    const text = String(children ?? "");
    const external = isExternalHref(href);
    const citation = looksLikeCitation(href, text);
    const className = citation
      ? "md-citation"
      : external
        ? "md-ext-link"
        : undefined;

    if (!href) {
      return <span className={className}>{children}</span>;
    }

    return (
      <a
        href={href}
        className={className}
        target={external ? "_blank" : undefined}
        rel={external ? "noopener noreferrer" : undefined}
      >
        {citation && !text.startsWith("〔") ? <span className="md-citation-mark">〔</span> : null}
        {children}
        {citation && !text.endsWith("〕") ? <span className="md-citation-mark">〕</span> : null}
        {external ? <span className="md-ext-icon" aria-hidden>↗</span> : null}
      </a>
    );
  },
  strong({ children }) {
    return <strong className="md-strong">{children}</strong>;
  },
  em({ children }) {
    return <em className="md-em">{children}</em>;
  },
  blockquote({ children }) {
    return <blockquote className="md-quote">{children}</blockquote>;
  },
  code({ className, children, ...props }) {
    const inline = !className;
    if (inline) {
      return (
        <code className="md-inline-code" {...props}>
          {children}
        </code>
      );
    }
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};

export function MarkdownView({
  content,
  className = "",
  localize = true,
}: MarkdownViewProps) {
  if (!content.trim()) {
    return <p className="text-sm text-[var(--muted)]">暂无内容</p>;
  }

  const rendered = localize ? localizeReportMarkdown(content) : content;

  return (
    <div className={`markdown-body ${className}`.trim()}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {rendered}
      </ReactMarkdown>
    </div>
  );
}

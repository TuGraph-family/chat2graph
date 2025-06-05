import { DocsLayout } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { baseOptions } from "@/app/layout.config";
import { source } from "@/lib/source";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <DocsLayout
      tree={source.pageTree}
      {...baseOptions}
      sidebar={{
        footer: (
          <div className="flex items-center justify-center p-4 border-t border-border">
            <a
              href="https://github.com/memfuse/memfuse"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <img
                src="/asset/image/github-icon.svg"
                alt="GitHub"
                className="w-5 h-5"
              />
              <span className="text-sm">GitHub</span>
            </a>
          </div>
        ),
      }}
    >
      {children}
    </DocsLayout>
  );
}

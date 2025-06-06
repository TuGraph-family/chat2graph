import { DocsLayout } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { baseOptions } from "@/app/layout.config";
import { getLanguagePageTree } from "@/lib/source";
import { isValidLanguage } from "@/lib/i18n";

interface LayoutProps {
  children: ReactNode;
  params: Promise<{ lang: string }>;
}

export default async function Layout({ children, params }: LayoutProps) {
  const { lang } = await params;
  
  // 验证语言参数
  if (!isValidLanguage(lang)) {
    notFound();
  }

  // 获取当前语言的页面树
  const languagePageTree = getLanguagePageTree(lang) as any;

  return (
    <DocsLayout
      tree={languagePageTree}
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
                src="/assets/images/github-icon.svg"
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
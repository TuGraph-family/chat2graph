import { DocsLayout } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { baseOptions } from "@/app/layout.config";
import { getLanguagePageTree } from "@/lib/source";
import { isValidLanguage } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/language-switcher";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { GitHubButton } from "@/components/github-button";

interface LayoutProps {
  children: ReactNode;
  params: Promise<{ lang: string }>;
}

export default async function Layout({ children, params }: LayoutProps) {
  const { lang } = await params;
  
  // Validate language parameter
  if (!isValidLanguage(lang)) {
    notFound();
  }

  // Get page tree for current language
  const languagePageTree = getLanguagePageTree(lang) as any;

  return (
    <DocsLayout
      tree={languagePageTree}
      {...baseOptions}
      sidebar={{
        footer: (
          <div className="p-4 border-t border-border">
            {/* Language and Theme Switchers */}
            <div className="flex items-center justify-center gap-2">
              <LanguageSwitcher />
              <ThemeSwitcher />
              <GitHubButton />
            </div>
          </div>
        ),
      }}
    >
      {children}
    </DocsLayout>
  );
}
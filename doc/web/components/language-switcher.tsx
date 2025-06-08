'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Globe } from 'lucide-react';
import { getLanguageFromPath } from '@/lib/i18n';

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  
  // Use the fixed function to get current language
  const currentLanguage = getLanguageFromPath(pathname);

  const switchLanguage = () => {
    const newLanguage = currentLanguage === 'en-us' ? 'zh-cn' : 'en-us';
    
    // Parse current path
    const segments = pathname.split('/').filter(Boolean);
    
    if (segments.length >= 2 && segments[0] === 'chat2graph') {
      // If in documentation page, replace language segment and keep other paths
      const remainingPath = segments.slice(2); // Remove 'chat2graph' and current language segment
      const newSegments = ['chat2graph', newLanguage, ...remainingPath];
      const newPath = '/' + newSegments.join('/');
      router.push(newPath);
    } else {
      // If not in documentation page, redirect to documentation homepage
      router.push(`/chat2graph/${newLanguage}/introduction`);
    }
  };

  const targetLanguageName = currentLanguage === 'en-us' ? '中文' : 'English';

  return (
    <button
      onClick={switchLanguage}
      className="gap-1 h-6 px-2 bg-background/80 backdrop-blur-sm border border-border rounded-md hover:bg-accent hover:text-accent-foreground flex items-center text-xs font-medium transition-colors shadow-sm"
    >
      <Globe className="h-3 w-3" />
      <span className="text-xs">
        {targetLanguageName}
      </span>
    </button>
  );
}

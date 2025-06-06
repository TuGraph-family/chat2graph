'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Globe } from 'lucide-react';
import { languages, getLanguageFromPath, defaultLanguage } from '@/lib/i18n';

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  
  // 使用修复后的函数获取当前语言
  const currentLanguage = getLanguageFromPath(pathname);

  const switchLanguage = () => {
    const newLanguage = currentLanguage === 'en' ? 'cn' : 'en';
    
    // 解析当前路径
    const segments = pathname.split('/').filter(Boolean);
    
    if (segments.length >= 2 && segments[0] === 'chat2graph') {
      // 如果在文档页面中，替换语言段并保持其他路径
      const remainingPath = segments.slice(2); // 移除 'chat2graph' 和当前语言段
      const newSegments = ['chat2graph', newLanguage, ...remainingPath];
      const newPath = '/' + newSegments.join('/');
      router.push(newPath);
    } else {
      // 如果不在文档页面，重定向到文档首页
      router.push(`/chat2graph/${newLanguage}/principle/overview`);
    }
  };

  const currentLanguageName = languages.find(lang => lang.code === currentLanguage)?.name || 'Eng';
  const targetLanguageName = currentLanguage === 'en' ? '中' : 'Eng';

  return (
    <button
      onClick={switchLanguage}
      className="gap-2 h-8 px-2 bg-transparent border border-border rounded-md hover:bg-accent hover:text-accent-foreground flex items-center text-sm font-medium transition-colors"
    >
      <Globe className="h-4 w-4" />
      <span className="text-sm">
        {targetLanguageName}
      </span>
    </button>
  );
}

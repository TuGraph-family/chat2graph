'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Globe } from 'lucide-react';
import { getLanguageFromPath } from '@/lib/i18n';

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  
  // 使用修复后的函数获取当前语言
  const currentLanguage = getLanguageFromPath(pathname);

  const switchLanguage = () => {
    const newLanguage = currentLanguage === 'en-us' ? 'zh-cn' : 'en-us';
    
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
      router.push(`/chat2graph/${newLanguage}/introduction`);
    }
  };

  const targetLanguageName = currentLanguage === 'en-us' ? '中' : 'Eng';

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

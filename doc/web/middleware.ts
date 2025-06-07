import { NextRequest, NextResponse } from 'next/server';
import { defaultLanguage, isValidLanguage } from './lib/i18n';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // 检查是否是文档路径
  if (pathname.startsWith('/chat2graph')) {
    const segments = pathname.split('/').filter(Boolean);
    
    // 如果路径是 /chat2graph 或 /chat2graph/，重定向到默认语言
    if (segments.length === 1 && segments[0] === 'chat2graph') {
      return NextResponse.redirect(
        new URL(`/chat2graph/${defaultLanguage}`, request.url)
      );
    }
    
    // 如果第二个段不是有效语言，重定向到默认语言
    if (segments.length >= 2 && segments[0] === 'chat2graph') {
      const langSegment = segments[1];
      
      if (!isValidLanguage(langSegment)) {
        // 将当前路径作为文档路径，添加默认语言前缀
        const docPath = segments.slice(1).join('/');
        return NextResponse.redirect(
          new URL(`/chat2graph/${defaultLanguage}/${docPath}`, request.url)
        );
      }
    }
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    // 匹配所有路径，除了静态文件和 API 路由
    '/((?!api|_next/static|_next/image|favicon.ico|asset).*)',
  ],
};
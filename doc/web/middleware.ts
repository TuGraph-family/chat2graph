import { NextRequest, NextResponse } from 'next/server';
import { defaultLanguage, isValidLanguage } from './lib/i18n';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Check if this is a documentation path
  if (pathname.startsWith('/chat2graph')) {
    const segments = pathname.split('/').filter(Boolean);
    
    // If path is /chat2graph or /chat2graph/, redirect to default language
    if (segments.length === 1 && segments[0] === 'chat2graph') {
      return NextResponse.redirect(
        new URL(`/chat2graph/${defaultLanguage}`, request.url)
      );
    }
    
    // If second segment is not a valid language, redirect to default language
    if (segments.length >= 2 && segments[0] === 'chat2graph') {
      const langSegment = segments[1];
      
      if (!isValidLanguage(langSegment)) {
        // Use current path as document path, add default language prefix
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
    '/((?!api|_next/static|_next/image|favicon.ico|asset).*)',
  ],
};
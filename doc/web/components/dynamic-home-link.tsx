'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getLanguageFromPath } from "@/lib/i18n";

export function DynamicHomeLink() {
  const pathname = usePathname();
  const currentLanguage = getLanguageFromPath(pathname);
  
  // Determine home link based on current language
  const homeUrl = `/chat2graph/${currentLanguage}/introduction`;
  
  return (
    <Link href={homeUrl} className="flex items-center gap-2">
        <>
            <img
                src="/asset/image/logo.png"
                alt="Chat2Graph Logo"
                className="w-8 h-8"
            />
            <span className="text-lg font-bold">Chat2Graph</span>
        </>
    </Link>
  );
}

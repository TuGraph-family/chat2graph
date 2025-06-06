import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import { LanguageSwitcher } from "@/components/language-switcher";
import { DynamicHomeLink } from "@/components/dynamic-home-link";

/**
 * Shared layout configurations
 *
 * you can customise layouts individually from:
 * Home Layout: app/(home)/layout.tsx
 * Docs Layout: app/docs/layout.tsx
 */
export const baseOptions: BaseLayoutProps = {
  nav: {
    // 直接设置为 null 或者 false 来禁用默认的 title 链接行为
    title: null,
    children: (
      <>
        <DynamicHomeLink />
        <LanguageSwitcher />
      </>
    ),
  },
  links: [],
};

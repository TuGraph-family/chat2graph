import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import { LanguageSwitcher } from "@/components/language-switcher";
import { HomeLink } from "@/components/home-link";

/**
 * Shared layout configurations
 *
 * you can customise layouts individually from:
 * Home Layout: app/(home)/layout.tsx
 * Docs Layout: app/docs/layout.tsx
 */
export const baseOptions: BaseLayoutProps = {
  nav: {
    title: <HomeLink />,
    children: <LanguageSwitcher />,
  },
  links: [],
};

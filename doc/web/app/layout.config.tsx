import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
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
    // Set to null or false to disable default title link behavior
    title: null,
    children: (
      <>
        <DynamicHomeLink />
      </>
    ),
  },
  links: [],
  // Disable system default theme switcher
  themeSwitch: {
    enabled: false,
  },
};

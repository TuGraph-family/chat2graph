import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";

/**
 * Shared layout configurations
 *
 * you can customise layouts individually from:
 * Home Layout: app/(home)/layout.tsx
 * Docs Layout: app/docs/layout.tsx
 */
export const baseOptions: BaseLayoutProps = {
  nav: {
    title: (
      <>
        <img
          src="/asset/image/memfuse-logo.svg"
          alt="MemFuse Logo"
          className="w-8 h-8"
        />
        <span className="text-lg font-bold">MemFuse</span>
      </>
    ),
  },
  links: [],
};

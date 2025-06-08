import { docs } from '@/.source';
import { loader } from 'fumadocs-core/source';

// `loader()` also assign a URL to your pages
// See https://fumadocs.vercel.app/docs/headless/source-api for more info
export const source = loader({
  baseUrl: '/chat2graph',
  source: docs.toFumadocsSource(),
});

// Get filtered page tree by language
export function getLanguagePageTree(lang: string) {
  const allPages = source.pageTree as any;
  
  // Check pageTree structure
  if (!allPages || typeof allPages !== 'object' || !allPages.children) {
    console.warn('Invalid pageTree structure');
    return { name: "", children: [] };
  }

  // Find the corresponding language folder
  const languageFolder = allPages.children.find((child: any) => 
    child.$id === lang
  );

  if (!languageFolder) {
    console.warn(`Language folder not found for: ${lang}`);
    return { name: "", children: [] };
  }

  // Process page URLs to ensure complete language prefix path is maintained
  const processItems = (items: any[]): any[] => {
    return items.map((item: any) => {
      if (item.type === 'page') {
        return {
          ...item,
          // Maintain complete /chat2graph/lang/path format
          url: item.url
        };
      } else if (item.type === 'folder' && item.children) {
        return {
          ...item,
          children: processItems(item.children),
          ...(item.index && {
            index: {
              ...item.index,
              // Maintain complete /chat2graph/lang/path format
              url: item.index.url
            }
          })
        };
      }
      return item;
    });
  };

  // Create new page tree structure, maintaining the root object format expected by fumadocs
  const processedChildren = processItems(languageFolder.children || []);
  
  // If language folder has index page, process it and add to the beginning
  if (languageFolder.index) {
    const indexPage = {
      ...languageFolder.index,
      // Maintain complete /chat2graph/lang/path format
      url: languageFolder.index.url
    };
    processedChildren.unshift(indexPage);
  }

  return {
    name: "",
    children: processedChildren
  };
}

// Get page by language and slug
export function getPageByLanguage(slug: string[], lang: string) {
  // Build complete path with language prefix
  const fullSlug = [lang, ...slug];
  
  // Try exact match
  let page = source.getPage(fullSlug);
  
  if (!page && slug.length === 0) {
    // If it's root path, try to find index page
    page = source.getPage([lang, 'index']);
  }
  
  return page;
}

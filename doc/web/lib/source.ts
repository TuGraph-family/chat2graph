import { docs } from '@/.source';
import { loader } from 'fumadocs-core/source';

// `loader()` also assign a URL to your pages
// See https://fumadocs.vercel.app/docs/headless/source-api for more info
export const source = loader({
  baseUrl: '/chat2graph',
  source: docs.toFumadocsSource(),
});

// 根据语言获取过滤后的页面树
export function getLanguagePageTree(lang: string) {
  const allPages = source.pageTree as any;
  
  // 检查pageTree结构
  if (!allPages || typeof allPages !== 'object' || !allPages.children) {
    console.warn('Invalid pageTree structure');
    return { name: "", children: [] };
  }

  // 找到对应语言的文件夹
  const languageFolder = allPages.children.find((child: any) => 
    child.$id === lang
  );

  if (!languageFolder) {
    console.warn(`Language folder not found for: ${lang}`);
    return { name: "", children: [] };
  }

  // 处理页面URL，确保保持完整的语言前缀路径
  const processItems = (items: any[]): any[] => {
    return items.map((item: any) => {
      if (item.type === 'page') {
        return {
          ...item,
          // 保持完整的 /chat2graph/lang/path 格式
          url: item.url
        };
      } else if (item.type === 'folder' && item.children) {
        return {
          ...item,
          children: processItems(item.children),
          ...(item.index && {
            index: {
              ...item.index,
              // 保持完整的 /chat2graph/lang/path 格式
              url: item.index.url
            }
          })
        };
      }
      return item;
    });
  };

  // 创建新的页面树结构，保持fumadocs期望的根对象格式
  const processedChildren = processItems(languageFolder.children || []);
  
  // 如果语言文件夹有index页面，将其处理并添加到开头
  if (languageFolder.index) {
    const indexPage = {
      ...languageFolder.index,
      // 保持完整的 /chat2graph/lang/path 格式
      url: languageFolder.index.url
    };
    processedChildren.unshift(indexPage);
  }

  return {
    name: "",
    children: processedChildren
  };
}

// 根据语言和 slug 获取页面
export function getPageByLanguage(slug: string[], lang: string) {
  // 构建包含语言前缀的完整路径
  const fullSlug = [lang, ...slug];
  
  // 尝试精确匹配
  let page = source.getPage(fullSlug);
  
  if (!page && slug.length === 0) {
    // 如果是根路径，尝试查找 index 页面
    page = source.getPage([lang, 'index']);
  }
  
  return page;
}

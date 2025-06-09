import { defineDocs, defineConfig } from "fumadocs-mdx/config";
import { remarkMermaid } from "@theguild/remark-mermaid";
import { z } from "zod";
import path from "path";
import { URL } from 'url';

// 1. Configuration Center
const config = {
  basePath: '/chat2graph',
  docRoot: 'public',
  publicAssetPrefix: '/asset/image',
};

// 2. Custom Rehype Plugins

/**
 * Rehype plugin: Handles image paths and default attributes.
 */
function rehypeImageDefaults(options: { publicAssetPrefix?: string } = {}) {
  const { publicAssetPrefix = config.publicAssetPrefix } = options;

  return (tree: any) => {
    function visit(node: any) {
      if (node.type === 'element' && node.tagName === 'img') {
        node.properties = node.properties || {};
        const src = node.properties.src;

        if (src && typeof src === 'string' && (src.startsWith('./') || src.startsWith('../'))) {
          const imageName = path.basename(src);
          node.properties.src = `${publicAssetPrefix}/${imageName}`;
        }
        
        if (!node.properties.width) node.properties.width = '800';
        if (!node.properties.height) node.properties.height = '600';
        if (!node.properties.alt) node.properties.alt = 'Document Image';
        
        const existingStyle = node.properties.style || '';
        node.properties.style = `${existingStyle}; max-width: 100%; height: auto;`.replace(/^;\s*/, '');
      }
      
      if (node.children) {
        node.children.forEach((child: any) => visit(child));
      }
    }
    
    visit(tree);
  };
}

/**
 * Rehype plugin: Handles internal Markdown links in multilingual documents.
 */
function rehypeLinkDefaults(options: { basePath?: string, docRoot?: string } = {}) {
  const { basePath = config.basePath, docRoot = config.docRoot } = options;

  return (tree: any, file: any) => {
    function getContentPath(filePath: string, rootMarker: string) {
      const normalizedPath = filePath.replace(/\\/g, '/');
      const marker = `/${rootMarker}/`;
      const parts = normalizedPath.split(marker);
      
      if (parts.length > 1) {
        return parts.pop();
      }
      return null;
    }

    function visit(node: any) {
      if (node.type === 'element' && node.tagName === 'a' && node.properties?.href) {
        const href = node.properties.href;
        
        const isProcessableLink = !/^(https?:|#|\/)/.test(href) && href.endsWith('.md');

        if (isProcessableLink) {
          const filePath = file?.history?.[0] || file?.path;
          if (!filePath) {
            console.warn(`[rehypeLinkDefaults] Unable to resolve link "${href}", file path unavailable.`);
            return;
          }

          const contentPath = getContentPath(filePath, docRoot);
          if (contentPath) {
            const baseUrl = `http://dummy.com/${contentPath}`;
            const resolvedUrl = new URL(href, baseUrl);
            let targetPath = resolvedUrl.pathname.replace(/^\//, '').replace(/\.md$/, '');
            
            const finalBasePath = basePath.endsWith('/') ? basePath : `${basePath}/`;
            node.properties.href = `${finalBasePath}${targetPath}`;
          } else {
            console.warn(`[rehypeLinkDefaults] Could not find docRoot ("${docRoot}") in path "${filePath}".`);
          }
        }
      }

      if (node.children) {
        node.children.forEach((child: any) => visit(child));
      }
    }
    visit(tree);
  };
}

// 3. Fumadocs Configuration Export
export const docs = defineDocs({
  dir: path.resolve(process.cwd(), config.docRoot),
  docs: {
    schema: z.object({
      title: z.string().optional(),
      description: z.string().optional(),
      icon: z.string().optional(),
      full: z.boolean().optional(),   
    }),
  },
});

export default defineConfig({
  mdxOptions: {
    remarkPlugins: [remarkMermaid],
    remarkImageOptions: false,
    rehypePlugins: [
      rehypeImageDefaults,
      rehypeLinkDefaults,
    ],
  },
});

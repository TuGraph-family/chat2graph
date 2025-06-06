import { defineDocs, defineConfig } from "fumadocs-mdx/config";
import { remarkMermaid } from "@theguild/remark-mermaid";
import { z } from "zod";
import path from "path";
import { URL } from 'url';

// 将所有可变配置集中在此处，方便统一管理和修改。
const config = {
  // 最终生成的链接的基础路径 (e.g., /chat2graph/zh-cn/...)
  basePath: '/chat2graph',
  // 包含所有语言文档的根目录名称
  docRoot: 'doc',
  // 公共图片资源的 URL 前缀
  publicAssetPrefix: '/asset/image',
};

/**
 * Rehype 插件：处理图片路径和默认属性。
 * - 将相对路径的图片转换为基于 publicAssetPrefix 的绝对路径。
 * - 为图片添加默认的 alt, width, height 和响应式样式。
 * @param {object} [options={}] - 配置选项。
 * @param {string} options.publicAssetPrefix - 公共资源 URL 前缀。
 */
function rehypeImageDefaults(options = {}) {
  const { publicAssetPrefix = '/asset/image' } = options;

  return (tree) => {
    function visit(node) {
      if (node.type === 'element' && node.tagName === 'img') {
        node.properties = node.properties || {};
        const src = node.properties.src;

        // 只处理相对路径的图片
        if (src && typeof src === 'string' && (src.startsWith('./') || src.startsWith('../'))) {
          // 使用 path.basename 提取图片文件名，这是最稳健的方式
          const imageName = path.basename(src);
          // 构建标准化的、绝对的资源路径
          node.properties.src = `${publicAssetPrefix}/${imageName}`;
        }
        
        // 添加默认属性
        if (!node.properties.width) node.properties.width = '800';
        if (!node.properties.height) node.properties.height = '600';
        if (!node.properties.alt) node.properties.alt = 'Document Image';
        
        // 添加响应式样式
        const existingStyle = node.properties.style || '';
        node.properties.style = `${existingStyle}; max-width: 100%; height: auto;`.replace(/^;\s*/, '');
      }
      
      if (node.children) {
        node.children.forEach(visit);
      }
    }
    
    visit(tree);
  };
}

/**
 * Rehype 插件：处理多语言文档中的内部 Markdown 链接。
 * @param {object} [options={}] - 配置选项。
 * @param {string} options.basePath - 链接的基础路径。
 * @param {string} options.docRoot - 文档根目录。
 */
function rehypeLinkDefaults(options = {}) {
  const { basePath = '/', docRoot = 'doc' } = options;

  return (tree, file) => {
    /**
     * [BUG FIX] 提取相对于文档根目录的内容路径。
     * 新的实现方式使用 split 和 pop，以确保我们总是从最后一个 'docRoot' 实例获取路径。
     * 这可以正确处理像 '.../doc/web/doc/en-us/page.md' 这样的嵌套路径。
     */
    function getContentPath(filePath, rootMarker) {
      // 为了保持一致性，将所有路径分隔符标准化为正斜杠
      const normalizedPath = filePath.replace(/\\/g, '/');
      const marker = `/${rootMarker}/`;
      
      const parts = normalizedPath.split(marker);
      
      // 如果路径成功被分割，我们需要的URL部分就是最后一段。
      if (parts.length > 1) {
        return parts.pop();
      }
      
      // 如果在路径中找不到标记，则返回 null。
      return null;
    }

    function visit(node) {
      if (node.type === 'element' && node.tagName === 'a' && node.properties?.href) {
        const href = node.properties.href;
        const isRelativeMdLink = (href.startsWith('./') || href.startsWith('../')) && href.endsWith('.md');

        if (isRelativeMdLink) {
          const filePath = file?.history?.[0] || file?.path;
          if (!filePath) {
            console.warn(`[rehypeLinkDefaults] 无法解析链接 "${href}"，文件路径不可用。`);
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
            console.warn(`[rehypeLinkDefaults] 在路径 "${filePath}" 中找不到 docRoot ("${docRoot}")。`);
          }
        }
      }

      if (node.children) {
        node.children.forEach(visit);
      }
    }
    visit(tree);
  };
}

export const docs = defineDocs({
  // 注意：这里的 'doc' 目录名应与上面 config.docRoot 保持一致
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
    remarkImageOptions: false, // 禁用默认图片处理以使用自定义插件
    rehypePlugins: [
      // 传入配置，使插件可重用
      [rehypeImageDefaults, { publicAssetPrefix: config.publicAssetPrefix }],
      [rehypeLinkDefaults, { basePath: config.basePath, docRoot: config.docRoot }],
    ],
  },
});

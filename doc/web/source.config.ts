import { defineDocs, defineConfig } from "fumadocs-mdx/config";
import { remarkMermaid } from "@theguild/remark-mermaid";
import { z } from "zod";

// 自定义 rehype 插件来处理图片属性
function rehypeImageDefaults() {
  return (tree: any, file: any) => {
    function visit(node: any) {
      if (node.type === 'element' && node.tagName === 'img') {
        // 确保 properties 对象存在
        node.properties = node.properties || {};
        
        // 处理相对路径图片，转换为绝对路径
        if (node.properties.src && typeof node.properties.src === 'string') {
          const src = node.properties.src;
          
          // 从文件路径推断当前文件的语言
          const filePath = file?.history?.[0] || file?.path || '';
          const isChinesePath = filePath.includes('/cn/') || filePath.includes('\\cn\\');
          const currentLanguage = isChinesePath ? 'cn' : 'en';
          
          // 处理各种相对路径格式
          if (src.includes('/img/') && (src.startsWith('./') || src.startsWith('../'))) {
            // 处理 ./img/xxx.png, ../img/xxx.png, ../../en/img/xxx.png 等格式
            
            // 检查路径中是否包含语言标识
            let targetLanguage = currentLanguage;
            let imageName = '';
            
            if (src.includes('/en/img/')) {
              targetLanguage = 'en';
              imageName = src.split('/img/')[1];
            } else if (src.includes('/cn/img/')) {
              targetLanguage = 'cn';
              imageName = src.split('/img/')[1];
            } else {
              // 普通的 ./img/ 或 ../img/ 格式，使用当前文件的语言
              imageName = src.replace(/^\.\.?\/img\//, '');
            }
            
            node.properties.src = `/${targetLanguage}/img/${imageName}`;
          }
        }
        
        // 添加必需的属性
        if (!node.properties.width) {
          node.properties.width = '800';
        }
        if (!node.properties.height) {
          node.properties.height = '600';
        }
        if (!node.properties.alt) {
          node.properties.alt = '';
        }
        
        // 添加样式使图片响应式
        const existingStyle = node.properties.style || '';
        node.properties.style = `${existingStyle}; max-width: 100%; height: auto;`.replace(/^;\s*/, '');
      }
      
      // 递归处理子节点
      if (node.children && Array.isArray(node.children)) {
        node.children.forEach(visit);
      }
    }
    
    visit(tree);
    return tree;
  };
}

export const docs = defineDocs({
  dir: "doc", // 使用 link 链接到 doc 目录，来从父级目录访问 doc
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
    remarkImageOptions: false, // 禁用默认图片处理
    rehypePlugins: [rehypeImageDefaults], // 添加自定义图片处理
  },
});

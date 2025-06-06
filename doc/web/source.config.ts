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
          const isChinesePath = filePath.includes('/zh-cn/') || filePath.includes('\\zh-cn\\');
          const currentLanguage = isChinesePath ? 'zh-cn' : 'en-us';
          
          // 处理各种相对路径格式
          if (src.startsWith('./') || src.startsWith('../') || src.startsWith('../../asset/')) {
            // 处理新的图片路径格式：../../asset/image/xxx.png 或 ../asset/image/xxx.png
            if (src.includes('/asset/image/')) {
              // 提取图片文件名
              const imageName = src.split('/asset/image/')[1];
              node.properties.src = `/asset/image/${imageName}`;
            } else if (src.includes('/img/') && (src.startsWith('./') || src.startsWith('../'))) {
              // 处理旧的 ./img/xxx.png, ../img/xxx.png 格式
              // 检查路径中是否包含语言标识
              let targetLanguage = currentLanguage;
              let imageName = '';
              
              if (src.includes('/en/img/')) {
                targetLanguage = 'en-us';
                imageName = src.split('/img/')[1];
              } else if (src.includes('/cn/img/')) {
                targetLanguage = 'zh-cn';
                imageName = src.split('/img/')[1];
              } else {
                // 普通的 ./img/ 或 ../img/ 格式，使用当前文件的语言
                imageName = src.replace(/^\.\.?\/img\//, '');
              }
              
              // 将旧的图片路径转换为新的 asset 路径
              node.properties.src = `/asset/image/${imageName}`;
            }
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

// 自定义 rehype 插件来处理内部链接
function rehypeLinkDefaults() {
  return (tree: any, file: any) => {
    function visit(node: any) {
      if (node.type === 'element' && node.tagName === 'a') {
        // 确保 properties 对象存在
        node.properties = node.properties || {};
        
        // 处理相对路径链接
        if (node.properties.href && typeof node.properties.href === 'string') {
          const href = node.properties.href;
          
          // 从文件路径推断当前文件的语言
          const filePath = file?.history?.[0] || file?.path || '';
          const isChinesePath = filePath.includes('/zh-cn/') || filePath.includes('\\zh-cn\\');
          const currentLanguage = isChinesePath ? 'zh-cn' : 'en-us';
          
          // 只处理以 ./ 或 ../ 开头且以 .md 结尾的相对链接
          if ((href.startsWith('./') || href.startsWith('../')) && href.endsWith('.md')) {
            // 移除 .md 扩展名
            let linkPath = href.replace(/\.md$/, '');
            
            // 处理 ../cookbook/graphdb.md -> cookbook/graphdb
            if (linkPath.startsWith('../')) {
              linkPath = linkPath.replace(/^\.\.\//, '');
            }
            // 处理 ./memory.md -> memory
            else if (linkPath.startsWith('./')) {
              linkPath = linkPath.replace(/^\.\//, '');
            }
            
            // 构建完整的内部链接路径
            node.properties.href = `/chat2graph/${currentLanguage}/${linkPath}`;
          }
        }
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
    rehypePlugins: [rehypeImageDefaults, rehypeLinkDefaults], // 添加自定义图片和链接处理
  },
});

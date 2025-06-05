import type { MDXComponents } from 'mdx/types'

// 自定义图片组件，绕过 Next.js 的图片检查
function CustomImage(props: any) {
  const { src, alt = '', ...rest } = props;
  
  // 为所有图片提供默认尺寸
  const defaultProps = {
    width: rest.width || 800,
    height: rest.height || 600,
    alt,
    style: { maxWidth: '100%', height: 'auto' },
    ...rest,
  };
  
  // 使用普通的 img 标签而不是 Next.js 的 Image 组件
  return <img {...defaultProps} src={src} />;
}

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    // 覆盖默认的 img 标签处理
    img: CustomImage,
    ...components,
  }
}

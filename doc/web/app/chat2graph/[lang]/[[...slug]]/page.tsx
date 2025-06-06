import { source, getPageByLanguage } from '@/lib/source';
import {
  DocsPage,
  DocsBody,
  DocsDescription,
  DocsTitle,
} from 'fumadocs-ui/page';
import { notFound, redirect } from 'next/navigation';
import defaultMdxComponents from 'fumadocs-ui/mdx';
import type { Metadata } from 'next';

interface PageProps {
  params: Promise<{
    lang: string;
    slug?: string[];
  }>;
}

export default async function Page({ params }: PageProps) {
  const { lang, slug = [] } = await params;
  
  // 验证语言
  if (lang !== 'en' && lang !== 'cn') {
    notFound();
  }
  
  // 如果是语言根路径，重定向到 overview 页面
  if (slug.length === 0) {
    redirect(`/chat2graph/${lang}/principle/overview`);
  }
  
  // 查找对应语言的页面
  const page = getPageByLanguage(slug, lang);
  
  if (!page) {
    notFound();
  }

  const MDX = page.data.body;

  return (
    <DocsPage
      toc={page.data.toc}
      full={page.data.full}
      tableOfContent={{
        style: 'clerk',
        single: false,
      }}
    >
      <DocsTitle>{page.data.title}</DocsTitle>
      <DocsDescription>{page.data.description}</DocsDescription>
      <DocsBody>
        <MDX components={{ ...defaultMdxComponents }} />
      </DocsBody>
    </DocsPage>
  );
}

export async function generateStaticParams() {
  const params: { lang: string; slug?: string[] }[] = [];
  
  // 为每种语言生成参数
  const languages = ['en', 'cn'];
  const allParams = source.generateParams();
  
  for (const param of allParams) {
    for (const lang of languages) {
      // 检查是否存在对应语言的页面
      if (param.slug && param.slug.length > 0) {
        const firstSegment = param.slug[0];
        if (firstSegment === lang) {
          // 如果第一个段是语言代码，移除它并生成对应的路由
          const slug = param.slug.slice(1);
          params.push({
            lang,
            slug: slug.length > 0 ? slug : undefined,
          });
        }
      }
    }
  }
  
  // 添加语言根路径
  for (const lang of languages) {
    params.push({
      lang,
      slug: undefined,
    });
  }
  
  return params;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { lang, slug = [] } = await params;
  const page = getPageByLanguage(slug, lang);

  if (!page) notFound();

  return {
    title: page.data.title,
    description: page.data.description,
  };
}

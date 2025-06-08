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
  
  // Validate language
  if (lang !== 'en-us' && lang !== 'zh-cn') {
    notFound();
  }
  
  // If it's language root path, redirect to introduction page
  if (slug.length === 0) {
    redirect(`/chat2graph/${lang}/introduction`);
  }
  
  // Find page for corresponding language
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
  
  // Generate parameters for each language
  const languages = ['en-us', 'zh-cn'];
  const allParams = source.generateParams();
  
  for (const param of allParams) {
    for (const lang of languages) {
      // Check if page exists for corresponding language
      if (param.slug && param.slug.length > 0) {
        const firstSegment = param.slug[0];
        if (firstSegment === lang) {
          // If first segment is language code, remove it and generate corresponding route
          const slug = param.slug.slice(1);
          params.push({
            lang,
            slug: slug.length > 0 ? slug : undefined,
          });
        }
      }
    }
  }
  
  // Add language root paths
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

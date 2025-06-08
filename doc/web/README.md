# 📚 Chat2Graph Documentation Website

> A modern, multilingual documentation website built with Next.js and Fumadocs

This is the official documentation website for Chat2Graph, featuring a clean, responsive design with support for multiple languages (English and Chinese). Built using Next.js and the powerful Fumadocs framework.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm, pnpm, or yarn

### Development

Start the development server:

```bash
# Using npm
npm run dev

# Using pnpm (recommended)
pnpm dev

# Using yarn
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the result.

### Build for Production

```bash
npm run build
npm run start
```

## 📁 Project Structure

```
doc/web/
├── app/                    # Next.js App Router pages
│   ├── chat2graph/        # Documentation routes
│   └── layout.tsx         # Root layout
├── components/            # Reusable UI components
│   ├── language-switcher.tsx
│   ├── theme-switcher.tsx
│   └── ...
├── doc/                   # Documentation content
│   ├── en-us/            # English documentation
│   └── zh-cn/            # Chinese documentation
├── lib/                   # Utility functions
│   ├── i18n.ts           # Internationalization
│   └── source.ts         # Content source
└── public/               # Static assets
```

## 🔧 Configuration

### Language Support

The website supports multiple languages configured in `lib/i18n.ts`:

- **English** (`en-us`) - Default language
- **Chinese** (`zh-cn`) - Simplified Chinese

### Content Management

Documentation content is organized in the `doc/` directory:

- Place English content in `doc/en-us/`
- Place Chinese content in `doc/zh-cn/`
- Use MDX format for rich content with React components

### Customization

Key configuration files:

- `source.config.ts` - Fumadocs configuration and custom plugins
- `next.config.mjs` - Next.js configuration
- `app/layout.config.tsx` - Layout and navigation settings

## 📖 Learn More

Expand your knowledge with these helpful resources:

### 📚 Documentation

- **[Next.js Documentation](https://nextjs.org/docs)** - Learn about Next.js features and API
- **[Fumadocs](https://fumadocs.vercel.app)** - Comprehensive guide to Fumadocs
- **[MDX](https://mdxjs.com/)** - Learn about MDX for interactive documentation

### 🎓 Tutorials

- **[Next.js Learn](https://nextjs.org/learn)** - Interactive Next.js tutorial
- **[React Documentation](https://react.dev/)** - Official React documentation

### 🛠️ Tools & Libraries

- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[Lucide Icons](https://lucide.dev/)** - Beautiful & consistent icon toolkit
- **[TypeScript](https://www.typescriptlang.org/)** - Typed JavaScript

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the same license as Chat2Graph. See [LICENSE](../../LICENSE) for details.

---

<div align="center">
  <strong>Built with ❤️ using Next.js and Fumadocs</strong>
</div>

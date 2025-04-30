import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {},
  access: {},
  model: {},
  initialState: {},
  request: {
    dataField: ''
  },
  // layout: {
  //   title: '@umijs/max',
  // },
  proxy: {
    '/api': {
      'target': 'http://127.0.0.1:5010',
      'changeOrigin': true,
      // 'pathRewrite': { '^/api' : '' },
    }
  },
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      name: '首页',
      path: '/home',
      component: './Home',
    },
    {
      path: '/manager',
      redirect: '/manager/knowledgebase',
    },
    {
      name: '管理',
      path: '/manager/*',
      component: './Manager',
    },

  ],
  npmClient: 'tnpm',
  locale: {
    antd: true,
    default: 'zh-CN',
    baseSeparator: '-',
  },
  links: [
    {
      rel: 'stylesheet',
      href: 'https://at.alicdn.com/t/a/font_4885401_0nj0i854xmuc.css',
    },
  ],
});


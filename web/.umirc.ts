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
      'target': 'http://localhost:8000',
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
});


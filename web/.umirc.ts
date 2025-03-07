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
      'target': 'http://127.0.0.1:5000',
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
      name: '管理',
      path: '/manager/*',
      component: './Manager',
    },
  ],
  npmClient: 'tnpm',
});


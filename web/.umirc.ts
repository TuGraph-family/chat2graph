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
      'target': 'http://gengsheng.alipay.net:5000',
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
  ],
  npmClient: 'tnpm',
});


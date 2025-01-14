import { createRouter, createWebHistory } from 'vue-router'
import CreateGraphView from '../views/create_graph.vue'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      name: 'CreateGraph',
      component: CreateGraphView
    }
  ]
})

export default router

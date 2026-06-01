import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/admin/select-school',
    name: 'SelectSchool',
    component: () => import('../views/admin/SelectSchool.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    component: () => import('../views/admin/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'score-entry', name: 'ScoreEntry', component: () => import('../views/admin/ScoreEntry.vue') },
      { path: 'students', name: 'Students', component: () => import('../views/admin/Students.vue') },
      { path: 'statistics', name: 'Statistics', component: () => import('../views/admin/Statistics.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/admin/Settings.vue') }
    ]
  },
  {
    path: '/student/login',
    name: 'StudentLogin',
    component: () => import('../views/student/Login.vue')
  },
  {
    path: '/student/scores',
    name: 'StudentScores',
    component: () => import('../views/student/Scores.vue')
  },
  { path: '/', redirect: '/admin/login' },
  { path: '/:pathMatch(.*)*', redirect: '/admin/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('admin_token')
    if (!token) {
      return next('/admin/login')
    }
  }
  next()
})

export default router

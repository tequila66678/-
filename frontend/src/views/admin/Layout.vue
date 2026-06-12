<template>
  <el-container style="min-height:100vh">
    <!-- Mobile overlay sidebar -->
    <div v-if="mobileOpen" class="sidebar-overlay" @click="mobileOpen = false" />
    <el-aside :width="mobileOpen ? '220px' : '0px'" class="sidebar" :class="{ 'sidebar-fixed': isMobile }">
      <div class="logo">{{ schoolName }}</div>
      <el-menu
        :default-active="route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
        @select="mobileOpen = false"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon> 仪表盘
        </el-menu-item>
        <el-menu-item index="/admin/score-entry">
          <el-icon><EditPen /></el-icon> 成绩录入
        </el-menu-item>
        <el-menu-item index="/admin/students">
          <el-icon><User /></el-icon> 学生管理
        </el-menu-item>
        <el-menu-item index="/admin/statistics">
          <el-icon><TrendCharts /></el-icon> 统计分析
        </el-menu-item>
        <el-menu-item v-if="adminInfo?.role !== 'teacher'" index="/admin/settings">
          <el-icon><Setting /></el-icon> 系统设置
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <el-button text @click="mobileOpen = !mobileOpen" class="menu-btn">
            <el-icon :size="22"><Expand v-if="!mobileOpen" /><Fold v-else /></el-icon>
          </el-button>
          <span class="school-short">{{ schoolName }}</span>
        </div>
        <div class="topbar-right">
          <!-- School switcher for super-admin -->
          <el-select
            v-if="adminInfo?.role === 'super'"
            v-model="currentSchoolId"
            size="small"
            class="school-switch"
            @change="switchSchool"
            placeholder="全部学校"
          >
            <el-option :value="null" label="全部学校" />
            <el-option v-for="s in schools" :key="s.id" :value="s.id" :label="s.name" />
          </el-select>
          <span class="user-name">{{ adminInfo?.display_name }}</span>
          <el-button type="danger" text @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const adminInfo = ref(null)
const schoolName = ref('')
const mobileOpen = ref(false)
const isMobile = ref(window.innerWidth < 768)
const schools = ref([])
const currentSchoolId = ref(null)

function onResize() { isMobile.value = window.innerWidth < 768 }

onMounted(async () => {
  const info = localStorage.getItem('admin_info')
  if (info) {
    adminInfo.value = JSON.parse(info)
    currentSchoolId.value = adminInfo.value.school_id
  }
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || '体育成绩管理系统'
  } catch {}
  if (adminInfo.value?.role === 'super') {
    try {
      const res = await api.get('/schools')
      schools.value = res.data
    } catch {}
  }
  window.addEventListener('resize', onResize)
})

onUnmounted(() => { window.removeEventListener('resize', onResize) })

async function switchSchool(schoolId) {
  try {
    const res = await api.post('/auth/switch-school', { school_id: schoolId })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    adminInfo.value = res.data.admin
    currentSchoolId.value = schoolId
    schoolName.value = res.data.admin.school_name || '全部学校'
    location.reload()
  } catch {
    location.reload()
  }
}

function logout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
  router.push('/admin/login')
}
</script>

<style scoped>
.sidebar { transition: width 0.3s; overflow: hidden; background: #304156; }
.sidebar-fixed { position: fixed; left: 0; top: 0; bottom: 0; z-index: 1000; }
.sidebar-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999; }
.logo { color: white; text-align: center; padding: 16px 8px; font-size: 14px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1); white-space: nowrap; }
.topbar { background: white; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; height: 50px; }
.topbar-left { display: flex; align-items: center; gap: 8px; }
.topbar-right { display: flex; align-items: center; }
.school-short { font-size: 14px; font-weight: bold; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-name { font-size: 13px; color: #666; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.main-content { padding: 12px; background: #f0f2f5; min-height: calc(100vh - 50px); }
@media (max-width: 767px) {
  .main-content { padding: 8px; }
  .menu-btn { padding: 4px; }
}
</style>

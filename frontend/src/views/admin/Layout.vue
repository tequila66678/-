<template>
  <el-container style="min-height:100vh">
    <el-aside width="220px" style="background:#304156">
      <div class="logo">{{ schoolName }}</div>
      <el-menu :default-active="route.path" background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF" router>
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
        <el-menu-item v-if="adminInfo?.is_super" index="/admin/settings">
          <el-icon><Setting /></el-icon> 开发人员选项
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:white;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:flex-end">
        <span>{{ adminInfo?.display_name }}</span>
        <el-button type="danger" text @click="logout" style="margin-left:16px">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const adminInfo = ref(null)
const schoolName = ref('')

onMounted(async () => {
  const info = localStorage.getItem('admin_info')
  if (info) adminInfo.value = JSON.parse(info)
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || '体育成绩管理系统'
  } catch {}
})

function logout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
  router.push('/admin/login')
}
</script>

<style scoped>
.logo {
  color: white; text-align: center; padding: 16px 8px;
  font-size: 15px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1);
  word-break: break-all;
}
</style>

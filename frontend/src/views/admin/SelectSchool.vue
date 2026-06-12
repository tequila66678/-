<template>
  <div class="ss-bg">
    <div class="ss-card">
      <div class="ss-icon">🏫</div>
      <h2>选择学校</h2>
      <p class="ss-sub">请选择要管理的学校</p>
      <div v-if="loading" style="text-align:center;padding:20px">加载中...</div>
      <div v-else class="ss-list">
        <div v-for="s in schools" :key="s.id" class="ss-item" @click="selectSchool(s)">
          {{ s.name }}
        </div>
      </div>
      <el-button text @click="logout" style="margin-top:12px">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const schools = ref([])
const loading = ref(true)

onMounted(async () => {
  const info = localStorage.getItem('admin_info')
  if (info) {
    const admin = JSON.parse(info)
    if (admin.role !== 'super') {
      router.push('/admin/dashboard')
      return
    }
  }
  try {
    const res = await api.get('/schools')
    schools.value = res.data
  } catch {} finally { loading.value = false }
})

async function selectSchool(school) {
  try {
    const res = await api.post('/auth/switch-school', { school_id: school.id })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    router.push('/admin/dashboard')
  } catch { ElMessage.error('切换失败') }
}

function logout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
  router.push('/admin/login')
}
</script>

<style scoped>
.ss-bg { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 20px; }
.ss-card { background: white; padding: 40px 28px; border-radius: 20px; width: 400px; max-width: 100%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
.ss-icon { font-size: 48px; margin-bottom: 8px; }
.ss-card h2 { font-size: 20px; color: #303133; margin: 0 0 4px; }
.ss-sub { color: #999; font-size: 13px; margin: 0 0 20px; }
.ss-list { display: flex; flex-direction: column; gap: 10px; }
.ss-item { padding: 14px 16px; background: #f5f7fa; border-radius: 10px; font-size: 15px; cursor: pointer; transition: all 0.2s; }
.ss-item:hover { background: #ecf5ff; color: #409EFF; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(64,158,255,0.15); }
</style>

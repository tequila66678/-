<template>
  <div class="login-bg">
    <div class="login-card">
      <div class="lc-icon">🏅</div>
      <h1>{{ schoolName }}</h1>
      <h2>管理员登录</h2>
      <el-form @submit.prevent="login" class="lc-form">
        <el-input v-model="username" placeholder="用户名" size="large" class="lc-input" />
        <el-input v-model="password" type="password" placeholder="密码" size="large" show-password class="lc-input" />
        <el-button type="primary" size="large" @click="login" :loading="loading" class="lc-btn">登 录</el-button>
      </el-form>
      <p class="lc-footer">Designed by {{ designer }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const schoolName = ref('体育成绩管理系统')
const designer = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || schoolName.value
    designer.value = res.data.designer || ''
  } catch {}
})

async function login() {
  loading.value = true
  try {
    const res = await api.post('/auth/login', { username: username.value, password: password.value })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    if (res.data.admin.role === 'super') {
      router.push('/admin/select-school')
    } else {
      router.push('/admin/dashboard')
    }
  } catch { ElMessage.error('用户名或密码错误') } finally { loading.value = false }
}
</script>

<style scoped>
.login-bg { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 20px; }
.login-card { background: white; padding: 40px 28px; border-radius: 20px; width: 380px; max-width: 100%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
.lc-icon { font-size: 48px; margin-bottom: 8px; }
.login-card h1 { font-size: 18px; color: #303133; margin: 0 0 4px; }
.login-card h2 { font-size: 14px; color: #999; margin: 0 0 28px; font-weight: 400; }
.lc-form { display: flex; flex-direction: column; gap: 14px; }
.lc-input :deep(.el-input__inner) { border-radius: 10px; height: 44px; }
.lc-btn { width: 100%; height: 44px; border-radius: 10px; font-size: 16px; letter-spacing: 4px; }
.lc-footer { margin-top: 24px; color: #ddd; font-size: 11px; }
</style>

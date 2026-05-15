<template>
  <div class="login-container">
    <div class="login-card">
      <h1>{{ schoolName }}</h1>
      <h2>管理员登录</h2>
      <el-form @submit.prevent="login">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="login" :loading="loading" style="width:100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <p class="designer">Designed by {{ designer }}</p>
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
    const res = await api.post('/auth/login', {
      username: username.value,
      password: password.value
    })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    router.push('/admin/dashboard')
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  background: white; padding: 40px; border-radius: 12px;
  width: 400px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.login-card h1 { text-align: center; font-size: 20px; color: #333; margin-bottom: 4px; }
.login-card h2 { text-align: center; font-size: 16px; color: #999; margin-bottom: 24px; font-weight: normal; }
.designer { text-align: center; color: #ccc; font-size: 12px; margin-top: 16px; }
</style>

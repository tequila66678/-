<template>
  <div class="login-container">
    <div class="login-card">
      <h1>{{ schoolName }}</h1>
      <h2>学生成绩查询</h2>
      <el-form @submit.prevent="login">
        <el-form-item>
          <el-input v-model="studentId" placeholder="学号" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="login" :loading="loading" style="width:100%">登录</el-button>
        </el-form-item>
        <el-form-item>
          <el-button text @click="showChangePwd = true">修改密码</el-button>
        </el-form-item>
      </el-form>
      <p class="designer">Designed by {{ designer }}</p>
    </div>

    <el-dialog v-model="showChangePwd" title="修改密码" width="350px">
      <el-form label-width="80px">
        <el-form-item label="学号"><el-input v-model="studentId" /></el-form-item>
        <el-form-item label="原密码"><el-input v-model="oldPwd" type="password" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="newPwd" type="password" /></el-form-item>
        <el-button type="primary" @click="changePassword">确认修改</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const studentId = ref('')
const password = ref('')
const loading = ref(false)
const schoolName = ref('体育成绩管理系统')
const designer = ref('')

const showChangePwd = ref(false)
const oldPwd = ref('')
const newPwd = ref('')

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
    const res = await api.post('/student/login', {
      student_id: studentId.value,
      password: password.value
    })
    sessionStorage.setItem('student_token', res.data.token)
    sessionStorage.setItem('student_id', studentId.value)
    sessionStorage.setItem('student_info', JSON.stringify(res.data.student))
    router.push('/student/scores')
  } catch {
    ElMessage.error('学号或密码错误')
  } finally { loading.value = false }
}

async function changePassword() {
  try {
    const token = sessionStorage.getItem('student_token') || ''
    await api.put('/student/password', {
      old_password: oldPwd.value,
      new_password: newPwd.value
    }, {
      params: { student_id: studentId.value, token }
    })
    ElMessage.success('密码修改成功')
    showChangePwd.value = false
  } catch { ElMessage.error('修改失败，请检查原密码') }
}
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}
.login-card {
  background: white; padding: 40px; border-radius: 12px;
  width: 400px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.login-card h1 { text-align: center; font-size: 20px; color: #333; margin-bottom: 4px; }
.login-card h2 { text-align: center; font-size: 16px; color: #999; margin-bottom: 24px; font-weight: normal; }
.designer { text-align: center; color: #ccc; font-size: 12px; margin-top: 16px; }
</style>

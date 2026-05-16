<template>
  <div class="login-bg">
    <div class="login-card">
      <div class="lc-icon">📊</div>
      <h1>{{ schoolName }}</h1>
      <h2>学生成绩查询</h2>
      <el-form @submit.prevent="login" class="lc-form">
        <el-input v-model="studentId" placeholder="学号" size="large" class="lc-input" />
        <el-input v-model="password" type="password" placeholder="密码（默认学号后6位）" size="large" show-password class="lc-input" />
        <el-button type="primary" size="large" @click="login" :loading="loading" class="lc-btn">登 录</el-button>
        <el-button text size="small" @click="showChangePwd = true" class="lc-pwd">修改密码</el-button>
      </el-form>
      <p class="lc-footer">Designed by {{ designer }}</p>
    </div>

    <el-dialog v-model="showChangePwd" title="修改密码" width="90%">
      <el-form label-width="70px">
        <el-form-item label="学号"><el-input v-model="studentId" /></el-form-item>
        <el-form-item label="原密码"><el-input v-model="oldPwd" type="password" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="newPwd" type="password" /></el-form-item>
        <el-button type="primary" @click="changePassword" style="width:100%">确认修改</el-button>
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
const studentId = ref(''); const password = ref(''); const loading = ref(false)
const schoolName = ref('体育成绩管理系统'); const designer = ref('')
const showChangePwd = ref(false); const oldPwd = ref(''); const newPwd = ref('')

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
    const res = await api.post('/student/login', { student_id: studentId.value, password: password.value })
    sessionStorage.setItem('student_token', res.data.token)
    sessionStorage.setItem('student_id', studentId.value)
    sessionStorage.setItem('student_info', JSON.stringify(res.data.student))
    router.push('/student/scores')
  } catch { ElMessage.error('学号或密码错误') } finally { loading.value = false }
}

async function changePassword() {
  try {
    await api.put('/student/password', { old_password: oldPwd.value, new_password: newPwd.value }, { params: { student_id: studentId.value, token: sessionStorage.getItem('student_token') || '' } })
    ElMessage.success('密码修改成功'); showChangePwd.value = false
  } catch { ElMessage.error('修改失败，请检查原密码') }
}
</script>

<style scoped>
.login-bg { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #0c3483 0%, #1e5eb6 50%, #2989d8 100%); padding: 20px; }
.login-card { background: white; padding: 40px 28px; border-radius: 20px; width: 380px; max-width: 100%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.25); }
.lc-icon { font-size: 48px; margin-bottom: 8px; }
.login-card h1 { font-size: 18px; color: #303133; margin: 0 0 4px; }
.login-card h2 { font-size: 14px; color: #999; margin: 0 0 28px; font-weight: 400; }
.lc-form { display: flex; flex-direction: column; gap: 14px; }
.lc-input :deep(.el-input__inner) { border-radius: 10px; height: 44px; }
.lc-btn { width: 100%; height: 44px; border-radius: 10px; font-size: 16px; letter-spacing: 4px; }
.lc-pwd { align-self: center; }
.lc-footer { margin-top: 24px; color: #ddd; font-size: 11px; }
</style>

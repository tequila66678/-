<template>
  <div class="student-scores">
    <div class="ss-header">
      <h3 class="ss-school">{{ schoolName }}</h3>
      <div class="ss-user">
        <span>{{ studentInfo?.name }}</span>
        <el-button text size="small" @click="showChangePwd = true">改密</el-button>
        <el-button text size="small" type="danger" @click="logout">退出</el-button>
      </div>
    </div>

    <p class="ss-info">{{ studentInfo?.class_grade }}{{ studentInfo?.class_name }} | {{ studentInfo?.student_id }}</p>

    <el-card style="margin-bottom:12px">
      <template #header>成绩总览</template>
      <div v-for="s in currentScores" :key="s.event_name" class="score-row">
        <span class="sr-name">{{ s.event_name }}</span>
        <span class="sr-value">{{ s.raw_value }}</span>
        <span class="sr-score">{{ s.earned_score }}分</span>
      </div>
      <div class="total-row">总分: {{ total }} / {{ maxTotal }}</div>
    </el-card>

    <el-card style="margin-bottom:12px">
      <template #header>中考推荐</template>
      <div v-for="r in recommended" :key="r.rank" class="rec-item">{{ r.medal }} {{ r.event_name }} — {{ r.score }} 分</div>
      <div v-if="!recommended.length" style="color:#ccc;text-align:center">暂无数据</div>
    </el-card>

    <el-card>
      <template #header>历史记录</template>
      <div v-if="Object.keys(history).length === 0" style="color:#ccc;text-align:center;padding:20px">暂无成绩记录</div>
      <div v-for="(scores, date) in history" :key="date" class="history-group">
        <div class="hg-date">{{ date }}</div>
        <div v-for="sc in scores" :key="sc.event_name" class="hg-item">{{ sc.event_name }}: {{ sc.raw_value }} → {{ sc.earned_score }}分</div>
      </div>
    </el-card>

    <el-dialog v-model="showChangePwd" title="修改密码" width="90%">
      <el-form label-width="60px">
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
const schoolName = ref('体育成绩管理系统')
const studentInfo = ref({})
const currentScores = ref([])
const total = ref(0)
const maxTotal = ref(90)
const recommended = ref([])
const history = ref({})
const showChangePwd = ref(false)
const oldPwd = ref('')
const newPwd = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || schoolName.value
  } catch {}
  const info = sessionStorage.getItem('student_info')
  if (!info) { router.push('/student/login'); return }
  studentInfo.value = JSON.parse(info)
  loadScores()
})

async function loadScores() {
  const res = await api.get('/student/scores', { params: { student_id: sessionStorage.getItem('student_id'), token: sessionStorage.getItem('student_token') } })
  currentScores.value = res.data.current_scores; total.value = res.data.total; maxTotal.value = res.data.max_total
  recommended.value = res.data.recommended; history.value = res.data.history_by_date
}

async function changePassword() {
  try {
    await api.put('/student/password', { old_password: oldPwd.value, new_password: newPwd.value }, { params: { student_id: sessionStorage.getItem('student_id'), token: sessionStorage.getItem('student_token') } })
    ElMessage.success('密码修改成功'); showChangePwd.value = false
  } catch { ElMessage.error('修改失败') }
}

function logout() { sessionStorage.clear(); router.push('/student/login') }
</script>

<style scoped>
.student-scores { max-width: 500px; margin: 0 auto; padding: 12px; }
.ss-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.ss-school { font-size: 16px; margin: 0; }
.ss-user { display: flex; align-items: center; font-size: 13px; }
.ss-info { color: #999; font-size: 13px; margin: 4px 0 12px; }
.score-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f0f0f0; }
.sr-name { font-size: 14px; }
.sr-value { color: #666; }
.sr-score { font-weight: bold; color: #409EFF; }
.total-row { text-align: right; margin-top: 8px; font-size: 16px; font-weight: bold; }
.rec-item { font-size: 16px; margin: 4px 0; }
.history-group { margin-bottom: 12px; }
.hg-date { font-weight: bold; font-size: 13px; color: #409EFF; margin-bottom: 4px; }
.hg-item { font-size: 13px; margin-left: 12px; color: #666; }
</style>

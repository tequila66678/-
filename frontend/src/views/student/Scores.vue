<template>
  <div style="max-width:600px;margin:0 auto;padding:20px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h3>{{ schoolName }}</h3>
      <div>
        <span>{{ studentInfo?.name }}</span>
        <el-button text @click="showChangePwd = true">修改密码</el-button>
        <el-button text type="danger" @click="logout">退出</el-button>
      </div>
    </div>

    <h4>{{ studentInfo?.class_grade }}{{ studentInfo?.class_name }} | {{ studentInfo?.student_id }}</h4>

    <el-card style="margin-bottom:16px">
      <template #header>本学期成绩总览</template>
      <el-table :data="currentScores" border size="small">
        <el-table-column prop="event_name" label="项目" />
        <el-table-column prop="raw_value" label="成绩" />
        <el-table-column prop="earned_score" label="得分" />
      </el-table>
      <div style="text-align:right;margin-top:12px;font-size:18px;font-weight:bold">
        总分: {{ total }} / {{ maxTotal }}
      </div>
    </el-card>

    <el-card style="margin-bottom:16px">
      <template #header>中考推荐项目</template>
      <div v-for="r in recommended" :key="r.rank" style="font-size:18px;margin:8px 0">
        {{ r.medal }} {{ r.event_name }} — {{ r.score }} 分
      </div>
    </el-card>

    <el-card>
      <template #header>历史成绩记录</template>
      <div v-if="Object.keys(history).length === 0" style="color:#ccc">暂无成绩记录</div>
      <div v-for="(scores, date) in history" :key="date" style="margin-bottom:16px">
        <strong>{{ date }}</strong>
        <div v-for="sc in scores" :key="sc.event_name" style="margin-left:16px">
          {{ sc.event_name }}: {{ sc.raw_value }} → {{ sc.earned_score }}分
        </div>
      </div>
    </el-card>

    <el-dialog v-model="showChangePwd" title="修改密码" width="350px">
      <el-form label-width="80px">
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
  const res = await api.get('/student/scores', {
    params: {
      student_id: sessionStorage.getItem('student_id'),
      token: sessionStorage.getItem('student_token')
    }
  })
  currentScores.value = res.data.current_scores
  total.value = res.data.total
  maxTotal.value = res.data.max_total
  recommended.value = res.data.recommended
  history.value = res.data.history_by_date
}

async function changePassword() {
  try {
    await api.put('/student/password', {
      old_password: oldPwd.value,
      new_password: newPwd.value
    }, {
      params: {
        student_id: sessionStorage.getItem('student_id'),
        token: sessionStorage.getItem('student_token')
      }
    })
    ElMessage.success('密码修改成功')
    showChangePwd.value = false
  } catch { ElMessage.error('修改失败') }
}

function logout() {
  sessionStorage.clear()
  router.push('/student/login')
}
</script>

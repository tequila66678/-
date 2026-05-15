<template>
  <div>
    <h3>统计分析</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="班级统计" name="class">
        <el-row :gutter="10" style="margin-bottom:16px">
          <el-col :span="8">
            <el-select v-model="statsClassId" placeholder="选择班级" @change="loadClassStats" style="width:100%">
              <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
            </el-select>
          </el-col>
          <el-col :span="16">
            <el-select v-model="statsEventIds" multiple placeholder="选择项目（默认全部）" @change="loadClassStats" style="width:100%">
              <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
          </el-col>
        </el-row>
        <el-button type="primary" @click="exportClassScores" style="margin-bottom:16px">导出班级成绩</el-button>

        <el-row :gutter="20" v-if="classStats">
          <el-col :span="6">
            <el-card><template #header>平均分</template><h2>{{ classStats.avg_score }}</h2></el-card>
          </el-col>
          <el-col :span="6">
            <el-card><template #header>优秀率(9-10分)</template><h2>{{ classStats.excellent_rate }}%</h2></el-card>
          </el-col>
          <el-col :span="6">
            <el-card><template #header>及格率(≥6分)</template><h2>{{ classStats.pass_rate }}%</h2></el-card>
          </el-col>
          <el-col :span="6">
            <el-card><template #header>总人数</template><h2>{{ classStats.total_students }}</h2></el-card>
          </el-col>
        </el-row>

        <div v-if="classStats?.event_avgs?.length" style="margin-top:20px">
          <h4>各项目平均分</h4>
          <div v-for="e in classStats.event_avgs" :key="e.event_id" class="event-bar">
            <span class="event-name">{{ e.event_name }}</span>
            <el-progress :percentage="e.avg_score * 10" :color="'#409EFF'" style="flex:1;margin:0 12px" />
            <span>{{ e.avg_score }}</span>
          </div>
        </div>

        <div v-if="classStats?.warning_students?.length" style="margin-top:20px">
          <h4 style="color:#e6a23c">退步预警学生</h4>
          <el-table :data="classStats.warning_students" border size="small">
            <el-table-column prop="student_no" label="学号" />
            <el-table-column prop="student_name" label="姓名" />
            <el-table-column prop="event_name" label="项目" />
            <el-table-column prop="prev_score" label="上次" />
            <el-table-column prop="curr_score" label="本次" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="个人统计" name="student">
        <el-row :gutter="10" style="margin-bottom:16px">
          <el-col :span="8">
            <el-input v-model="studentSearch" placeholder="输入学号或姓名搜索学生" @change="searchStudent" />
          </el-col>
          <el-col :span="16">
            <el-select v-model="studentEventIds" multiple placeholder="选择项目（默认全部）" @change="reloadStudentStats" style="width:100%">
              <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
          </el-col>
        </el-row>

        <div v-if="studentStats">
          <h4>{{ studentStats.student.name }} ({{ studentStats.student.student_id }})</h4>
          <el-button @click="exportStudentScores" style="margin-bottom:16px">导出个人成绩</el-button>

          <el-card style="margin-bottom:16px">
            <template #header>中考推荐项目</template>
            <div v-for="r in studentStats.recommended_events" :key="r.rank" style="margin:8px 0;font-size:18px">
              {{ r.medal }} {{ r.event_name }} — {{ r.score }} 分
            </div>
          </el-card>

          <el-card v-if="studentStats.scores_by_event">
            <template #header>各项目得分记录</template>
            <div v-for="(scoreList, eventName) in studentStats.scores_by_event" :key="eventName" style="margin:8px 0">
              <strong>{{ eventName }}</strong>:
              <span v-for="sc in scoreList" :key="sc.id" style="margin-left:8px">
                {{ sc.earned_score }}({{ sc.test_date }})
              </span>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const activeTab = ref('class')
const classes = ref([])
const events = ref([])

const statsClassId = ref(null)
const statsEventIds = ref([])
const classStats = ref(null)

const studentSearch = ref('')
const studentEventIds = ref([])
const studentStats = ref(null)
let currentStudentId = null

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([
    api.get('/events/classes'),
    api.get('/events')
  ])
  classes.value = cRes.data
  events.value = eRes.data
})

async function loadClassStats() {
  if (!statsClassId.value) return
  const params = { class_id: statsClassId.value }
  if (statsEventIds.value.length) params.event_ids = statsEventIds.value.join(',')
  const res = await api.get('/scores/class-stats', { params })
  classStats.value = res.data
}

async function searchStudent() {
  if (!studentSearch.value) return
  const res = await api.get('/students', { params: { search: studentSearch.value, page_size: 10 } })
  if (res.data.length > 0) {
    currentStudentId = res.data[0].id
    loadStudentStats()
  }
}

async function loadStudentStats() {
  const params = {}
  if (studentEventIds.value.length) params.event_ids = studentEventIds.value.join(',')
  const res = await api.get(`/scores/student-stats/${currentStudentId}`, { params })
  studentStats.value = res.data
}

function reloadStudentStats() {
  if (currentStudentId) loadStudentStats()
}

function exportClassScores() {
  if (!statsClassId.value) return
  let url = `/api/scores/export/class?class_id=${statsClassId.value}`
  if (statsEventIds.value.length) url += `&event_ids=${statsEventIds.value.join(',')}`
  window.open(url)
}

function exportStudentScores() {
  if (!currentStudentId) return
  window.open(`/api/scores/export/student/${currentStudentId}`)
}
</script>

<style scoped>
.event-bar { display: flex; align-items: center; margin: 8px 0; }
.event-name { width: 120px; font-size: 14px; }
</style>

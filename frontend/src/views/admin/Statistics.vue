<template>
  <div class="stats-page">
    <h3 style="margin-bottom:12px">统计分析</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="班级统计" name="class">
        <el-select v-model="statsClassId" placeholder="选择班级" @change="loadClassStats" style="width:100%;margin-bottom:8px" size="default">
          <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
        </el-select>
        <el-select v-model="statsEventIds" multiple placeholder="选择项目（可选）" @change="loadClassStats" style="width:100%;margin-bottom:8px" size="default">
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-button type="primary" size="small" @click="exportClassScores" style="margin-bottom:12px">导出班级成绩</el-button>

        <el-row :gutter="8" v-if="classStats" class="stat-cards">
          <el-col :span="12" class="stat-col"><el-card><template #header>平均分</template><h2>{{ classStats.avg_score }}</h2></el-card></el-col>
          <el-col :span="12" class="stat-col"><el-card><template #header>优秀率</template><h2>{{ classStats.excellent_rate }}%</h2></el-card></el-col>
          <el-col :span="12" class="stat-col"><el-card><template #header>及格率</template><h2>{{ classStats.pass_rate }}%</h2></el-card></el-col>
          <el-col :span="12" class="stat-col"><el-card><template #header>人数</template><h2>{{ classStats.total_students }}</h2></el-card></el-col>
        </el-row>

        <div v-if="classStats?.event_avgs?.length" style="margin-top:12px">
          <h4>各项目平均分</h4>
          <div v-for="e in classStats.event_avgs" :key="e.event_id" class="event-bar">
            <span class="event-name">{{ e.event_name }}</span>
            <el-progress :percentage="e.avg_score * 10" color="#409EFF" style="flex:1;margin:0 8px" />
            <span>{{ e.avg_score }}</span>
          </div>
        </div>

        <div v-if="classStats?.warning_students?.length" style="margin-top:12px">
          <h4 style="color:#e6a23c">橙色预警</h4>
          <div v-for="w in classStats.warning_students" :key="w.student_no" class="warn-card">
            {{ w.student_name }}({{ w.student_no }}) {{ w.event_name }}: {{ w.prev_score }}→{{ w.curr_score }}
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="个人统计" name="student">
        <el-input v-model="studentSearch" placeholder="输入学号或姓名搜索" @change="searchStudent" style="margin-bottom:8px" clearable />
        <el-select v-model="studentEventIds" multiple placeholder="选择项目（可选）" @change="reloadStudentStats" style="width:100%;margin-bottom:8px">
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>

        <div v-if="studentStats">
          <h4>{{ studentStats.student.name }} ({{ studentStats.student.student_id }})</h4>
          <el-button size="small" @click="exportStudentScores" style="margin-bottom:12px">导出个人成绩</el-button>

          <el-card style="margin-bottom:12px">
            <template #header>中考推荐</template>
            <div v-for="r in studentStats.recommended_events" :key="r.rank" class="rec-item">{{ r.medal }} {{ r.event_name }} — {{ r.score }} 分</div>
          </el-card>

          <el-card v-if="studentStats.scores_by_event">
            <template #header>成绩记录</template>
            <div v-for="(scoreList, eventName) in studentStats.scores_by_event" :key="eventName" style="margin:6px 0">
              <strong>{{ eventName }}</strong>: <span v-for="sc in scoreList" :key="sc.id" style="margin-left:6px;font-size:13px">{{ sc.earned_score }}分({{ sc.test_date }})</span>
            </div>
          </el-card>
        </div>
        <div v-else style="text-align:center;color:#ccc;padding:40px">请搜索学生姓名或学号</div>
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
  const [cRes, eRes] = await Promise.all([api.get('/events/classes'), api.get('/events')])
  classes.value = cRes.data; events.value = eRes.data
})

async function loadClassStats() {
  if (!statsClassId.value) return
  const params = { class_id: statsClassId.value }
  if (statsEventIds.value.length) params.event_ids = statsEventIds.value.join(',')
  const res = await api.get('/scores/class-stats', { params }); classStats.value = res.data
}

async function searchStudent() {
  if (!studentSearch.value) return
  const res = await api.get('/students', { params: { search: studentSearch.value, page_size: 10 } })
  if (res.data.length > 0) { currentStudentId = res.data[0].id; loadStudentStats() }
}

async function loadStudentStats() {
  const params = {}
  if (studentEventIds.value.length) params.event_ids = studentEventIds.value.join(',')
  const res = await api.get(`/scores/student-stats/${currentStudentId}`, { params }); studentStats.value = res.data
}

function reloadStudentStats() { if (currentStudentId) loadStudentStats() }

function exportClassScores() {
  if (!statsClassId.value) return
  let url = `/api/scores/export/class?class_id=${statsClassId.value}`
  if (statsEventIds.value.length) url += `&event_ids=${statsEventIds.value.join(',')}`; window.open(url)
}

function exportStudentScores() {
  if (!currentStudentId) return; window.open(`/api/scores/export/student/${currentStudentId}`)
}
</script>

<style scoped>
.stat-col { margin-bottom: 8px; }
.stat-cards .el-card :deep(.el-card__header) { padding: 8px 12px; font-size: 13px; }
.stat-cards h2 { margin: 4px 0; font-size: 24px; }
.event-bar { display: flex; align-items: center; margin: 6px 0; }
.event-name { width: 100px; font-size: 13px; flex-shrink: 0; }
.warn-card { padding: 8px; background: #fef0f0; border-radius: 6px; margin-bottom: 4px; font-size: 13px; }
.rec-item { font-size: 16px; margin: 6px 0; }
</style>

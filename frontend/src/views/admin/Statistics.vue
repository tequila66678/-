<template>
  <div class="stats-page">
    <el-button text @click="$router.push('/admin/dashboard')" class="back-btn">← 返回仪表盘</el-button>
    <h3 style="margin:8px 0 12px">统计分析</h3>
    <el-tabs v-model="activeTab">
      <!-- 全校统计 -->
      <el-tab-pane label="全校统计" name="school">
        <el-select v-model="schoolEventIds" multiple placeholder="选择项目（可选）" @change="loadSchoolStats" style="width:100%;margin-bottom:8px" size="default" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showExport = true" style="margin-bottom:12px">导出全校成绩</el-button>

        <el-row :gutter="8" v-if="schoolStats">
          <el-col :span="6" class="stat-col"><el-card><template #header>总人数</template><h2>{{ schoolStats.total_students }}</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>班级数</template><h2>{{ schoolStats.total_classes }}</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>平均分</template><h2>{{ schoolStats.avg_score }}</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>优秀率</template><h2>{{ schoolStats.excellent_rate }}%</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>及格率</template><h2>{{ schoolStats.pass_rate }}%</h2></el-card></el-col>
        </el-row>

        <div v-if="schoolStats?.event_avgs?.length" style="margin-top:12px">
          <h4>各项目全校平均分</h4>
          <div v-for="e in schoolStats.event_avgs" :key="e.event_id" class="event-bar">
            <span class="event-name">{{ e.event_name }}</span>
            <el-progress :percentage="e.avg_score * 10" color="#409EFF" style="flex:1;margin:0 8px" />
            <span>{{ e.avg_score }} ({{ e.count }}人)</span>
          </div>
        </div>

        <div v-if="schoolStats?.class_summaries?.length" style="margin-top:12px">
          <h4>各班平均分</h4>
          <div v-for="c in schoolStats.class_summaries" :key="c.class_id" class="event-bar">
            <span class="event-name">{{ c.class_name }}</span>
            <el-progress :percentage="c.avg_score * 10" color="#67c23a" style="flex:1;margin:0 8px" />
            <span>{{ c.avg_score }} ({{ c.students }}人)</span>
          </div>
        </div>

        <div v-if="schoolStats?.warning_students?.length" style="margin-top:12px">
          <h4 style="color:#e6a23c">全校橙色预警</h4>
          <div v-for="w in schoolStats.warning_students.slice(0, 10)" :key="w.student_no" class="warn-card">
            {{ w.student_name }}({{ w.student_gender === 'M' ? '男' : '女' }}) {{ w.student_no }} {{ w.event_name }}: {{ w.prev_score }}→{{ w.curr_score }}
          </div>
        </div>
      </el-tab-pane>

      <!-- 班级统计 -->
      <el-tab-pane label="班级统计" name="class">
        <el-select v-model="statsClassId" placeholder="选择班级" @change="loadClassStats" style="width:100%;margin-bottom:8px" size="default">
          <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
        </el-select>
        <el-select v-model="statsEventIds" multiple placeholder="选择项目（可选）" @change="loadClassStats" style="width:100%;margin-bottom:8px" size="default" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showExport = true" style="margin-bottom:12px">导出班级成绩</el-button>

        <el-row :gutter="8" v-if="classStats">
          <el-col :span="6" class="stat-col"><el-card><template #header>平均分</template><h2>{{ classStats.avg_score }}</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>优秀率</template><h2>{{ classStats.excellent_rate }}%</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>及格率</template><h2>{{ classStats.pass_rate }}%</h2></el-card></el-col>
          <el-col :span="6" class="stat-col"><el-card><template #header>人数</template><h2>{{ classStats.total_students }}</h2></el-card></el-col>
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
            {{ w.student_name }}({{ w.student_gender === 'M' ? '男' : '女' }}) {{ w.student_no }} {{ w.event_name }}: {{ w.prev_score }}→{{ w.curr_score }}
          </div>
        </div>
      </el-tab-pane>

      <!-- 个人统计 -->
      <el-tab-pane label="个人统计" name="student">
        <el-input v-model="studentSearch" placeholder="输入学号或姓名搜索" @change="searchStudent" style="margin-bottom:8px" clearable />
        <el-select v-model="studentEventIds" multiple placeholder="选择项目（可选）" @change="reloadStudentStats" style="width:100%;margin-bottom:8px" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>

        <div v-if="studentStats">
          <h4>{{ studentStats.student.name }}({{ studentStats.student.gender === 'M' ? '男' : '女' }}) {{ studentStats.student.student_id }}</h4>
          <el-button type="primary" size="small" @click="showExport = true" style="margin-bottom:12px">导出个人成绩</el-button>

          <el-card style="margin-bottom:12px">
            <template #header>中考推荐</template>
            <div v-for="r in studentStats.recommended_events" :key="r.rank" class="rec-item">{{ r.medal }} {{ r.event_name }} — {{ r.score }} 分</div>
          </el-card>

          <el-card v-if="studentStats.scores_by_event">
            <template #header>成绩记录</template>
            <div v-for="(scoreList, eventName) in studentStats.scores_by_event" :key="eventName" style="margin:6px 0">
              <strong>{{ eventName }}</strong>:
              <span v-for="sc in scoreList" :key="sc.id" style="margin-left:6px;font-size:13px">
                {{ sc.raw_value }}（{{ sc.earned_score }}分）{{ sc.test_date }}
                <el-button text type="danger" size="small" @click="deleteScore(sc.id)" style="padding:0;margin:0;font-size:11px">×</el-button>
              </span>
            </div>
          </el-card>

          <el-card v-if="chartOption" style="margin-top:12px">
            <template #header>成绩趋势</template>
            <v-chart :option="chartOption" style="height:320px" autoresize />
          </el-card>
        </div>
        <div v-else style="text-align:center;color:#ccc;padding:40px">请搜索学生姓名或学号</div>
      </el-tab-pane>
    </el-tabs>

    <ExportDialog v-model="showExport" :classes="classes" :events="events" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import ExportDialog from '../../components/ExportDialog.vue'
import VChart from 'vue-echarts'
import 'echarts'

const activeTab = ref('school')
const classes = ref([])
const events = ref([])
const showExport = ref(false)

// School stats
const schoolEventIds = ref([])
const schoolStats = ref(null)

// Class stats
const statsClassId = ref(null)
const statsEventIds = ref([])
const classStats = ref(null)

// Student stats
const studentSearch = ref('')
const studentEventIds = ref([])
const studentStats = ref(null)
let currentStudentId = null

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([api.get('/events/classes'), api.get('/events')])
  classes.value = cRes.data; events.value = eRes.data
  loadSchoolStats()
})

async function loadSchoolStats() {
  const params = {}
  if (schoolEventIds.value.length) params.event_ids = schoolEventIds.value.join(',')
  const res = await api.get('/scores/school-stats', { params }); schoolStats.value = res.data
}

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

async function deleteScore(scoreId) {
  try { await ElMessageBox.confirm('确定删除这条成绩记录？', '确认删除', { type: 'warning' }) } catch { return }
  await api.delete(`/scores/${scoreId}`)
  ElMessage.success('已删除')
  loadStudentStats()
}

function reloadStudentStats() { if (currentStudentId) loadStudentStats() }

const chartOption = computed(() => {
  if (!studentStats.value?.scores_by_event) return null
  const data = studentStats.value.scores_by_event
  const eventNames = Object.keys(data).filter(k => {
    return data[k].length >= 2 && data[k].some(s => s.numeric_value != null)
  })
  if (!eventNames.length) return null

  const allDates = new Set()
  const eventData = {}
  for (const name of eventNames) {
    eventData[name] = {}
    for (const s of data[name]) {
      allDates.add(s.test_date)
      eventData[name][s.test_date] = { numeric: s.numeric_value, raw: s.raw_value, score: s.earned_score, unit: s.unit, higher: s.higher_better }
    }
  }
  const dates = [...allDates].sort()
  const colors = ['#409EFF','#67C23A','#E6A23C','#F56C6C','#909399','#B37FEB','#36CFC9','#FF85C0']

  const yAxes = []
  const series = eventNames.map((name, i) => {
    const side = i % 2 === 0 ? 'left' : 'right'
    const offset = Math.floor(i / 2) * 50
    const unit = data[name][0]?.unit || ''
    const higherBetter = data[name][0]?.higher_better
    yAxes.push({
      type: 'value', name: unit, nameTextStyle: { fontSize: 10 },
      position: side, offset: offset || undefined,
      axisLabel: { fontSize: 9 },
      splitLine: { show: i === 0 },
      inverse: higherBetter === false
    })
    const seriesData = dates.map(d => {
      const pt = eventData[name][d]
      return pt ? { value: pt.numeric, raw: pt.raw, score: pt.score } : null
    })
    return {
      name, type: 'line', smooth: true,
      yAxisIndex: i, color: colors[i % colors.length],
      data: seriesData,
      label: { show: true, formatter: p => p.data ? `${p.data.raw} (${p.data.score}分)` : '', fontSize: 10 },
      emphasis: { focus: 'series' },
      markLine: i === 0 ? { silent: true, symbol: 'none', data: [] } : undefined
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params[0]?.axisValue || ''
        let tip = date + '<br/>'
        for (const p of params) {
          if (p.data) {
            const dir = data[p.seriesName]?.[0]?.higher_better ? '越大越好' : '越小越好'
            tip += `${p.marker} ${p.seriesName}: ${p.data.raw} (${p.data.score}分) ${dir}<br/>`
          }
        }
        return tip
      }
    },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 10 } },
    grid: { left: 45, right: 45, top: 10, bottom: 50 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: yAxes,
    series
  }
})
</script>

<style scoped>
.back-btn { margin-bottom: 4px; }
.stat-col { margin-bottom: 8px; }
.stat-col .el-card :deep(.el-card__header) { padding: 8px 10px; font-size: 12px; }
.stat-col h2 { margin: 4px 0; font-size: 22px; }
.event-bar { display: flex; align-items: center; margin: 6px 0; }
.event-name { width: 100px; font-size: 13px; flex-shrink: 0; }
.warn-card { padding: 8px; background: #fef0f0; border-radius: 6px; margin-bottom: 4px; font-size: 13px; }
.rec-item { font-size: 16px; margin: 4px 0; }
</style>

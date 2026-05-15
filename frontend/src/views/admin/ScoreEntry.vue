<template>
  <div class="score-entry">
    <div v-if="!started">
      <h3>成绩录入</h3>
      <el-form label-width="80px" style="max-width:400px">
        <el-form-item label="选择班级">
          <el-select v-model="selectedClassId" placeholder="请选择班级" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择项目">
          <el-select v-model="selectedEventId" placeholder="请选择项目" style="width:100%">
            <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试日期">
          <el-date-picker v-model="testDate" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startEntry" :disabled="!selectedClassId || !selectedEventId">
            开始录入
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-else>
      <div class="entry-header">
        <el-button text @click="started = false">← 返回</el-button>
        <span>{{ selectedClassLabel }} - {{ selectedEventName }}</span>
      </div>

      <div class="student-card" v-if="currentStudent">
        <div class="student-nav">
          <el-button circle @click="prevStudent" :disabled="currentIndex === 0">◀</el-button>
          <div class="student-info">
            <div class="student-name">{{ currentStudent.name }}</div>
            <div class="student-id">{{ currentStudent.student_id }}</div>
            <div class="progress">{{ currentIndex + 1 }} / {{ students.length }}</div>
          </div>
          <el-button circle @click="nextStudent" :disabled="currentIndex >= students.length - 1">▶</el-button>
        </div>

        <div class="input-area">
          <el-input
            v-model="currentValue"
            :placeholder="placeholder"
            size="large"
            class="score-input"
            @input="onValueChange"
          />
        </div>

        <div class="voice-area">
          <VoiceButton @result="onVoiceResult" />
        </div>

        <div class="score-result" v-if="currentScore !== null">
          <div class="earned">得分: {{ currentScore }} 分</div>
          <div class="change" v-if="previousScore !== null">
            上次: {{ previousScore }} 分
            <span v-if="change > 0 && isPraise" class="praise">↑+{{ change }} ✨ 进步表扬</span>
            <span v-else-if="change < 0 && isWarning" class="warning">↓{{ change }} 🟠 橙色预警</span>
            <span v-else-if="change > 0">↑+{{ change }}</span>
            <span v-else-if="change < 0">↓{{ change }}</span>
            <span v-else>→ 持平</span>
          </div>
          <div v-else class="change muted">- 首次测试</div>
        </div>

        <el-button type="primary" size="large" @click="saveAndNext" :loading="saving" class="save-btn">
          保存并下一个
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'
import VoiceButton from '../../components/VoiceButton.vue'

const classes = ref([])
const events = ref([])
const selectedClassId = ref(null)
const selectedEventId = ref(null)
const testDate = ref(new Date().toISOString().split('T')[0])
const started = ref(false)

const students = ref([])
const currentIndex = ref(0)
const currentValue = ref('')
const currentScore = ref(null)
const previousScore = ref(null)
const change = ref(null)
const isPraise = ref(false)
const isWarning = ref(false)
const saving = ref(false)

const selectedClassLabel = computed(() => {
  const c = classes.value.find(c => c.id === selectedClassId.value)
  return c ? c.label : ''
})
const selectedEventName = computed(() => {
  const e = events.value.find(e => e.id === selectedEventId.value)
  return e ? e.name : ''
})
const selectedEvent = computed(() => events.value.find(e => e.id === selectedEventId.value))
const currentStudent = computed(() => students.value[currentIndex.value])

const placeholder = computed(() => {
  if (!selectedEvent.value) return '输入成绩'
  const fmt = selectedEvent.value.input_format
  if (fmt === 'time_ms') return "例如: 3'30"
  if (fmt === 'decimal_seconds') return '例如: 8.1'
  if (fmt === 'decimal_meters') return '例如: 1.95'
  return '例如: 170'
})

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([
    api.get('/events/classes'),
    api.get('/events')
  ])
  classes.value = cRes.data
  events.value = eRes.data
})

async function startEntry() {
  const res = await api.get(`/scores/student-list/${selectedClassId.value}`)
  students.value = res.data
  currentIndex.value = 0
  currentValue.value = ''
  currentScore.value = null
  previousScore.value = null
  change.value = null
  isPraise.value = false
  isWarning.value = false
  started.value = true
}

function prevStudent() { if (currentIndex.value > 0) { currentIndex.value--; resetInput() } }
function nextStudent() { if (currentIndex.value < students.value.length - 1) { currentIndex.value++; resetInput() } }

function resetInput() {
  currentValue.value = ''
  currentScore.value = null
  previousScore.value = null
  change.value = null
  isPraise.value = false
  isWarning.value = false
}

function onVoiceResult(text) {
  currentValue.value = text
  onValueChange()
}

async function onValueChange() {
  if (!currentValue.value) { currentScore.value = null; return }
  try {
    const res = await api.post('/scores/batch', {
      scores: [{
        student_id: currentStudent.value.id,
        event_id: selectedEventId.value,
        raw_value: currentValue.value,
        test_date: testDate.value
      }]
    })
    const result = res.data[0]
    currentScore.value = result.earned_score
    previousScore.value = result.previous_score
    change.value = result.change
    isPraise.value = result.is_praise
    isWarning.value = result.is_warning
  } catch {
    currentScore.value = null
  }
}

async function saveAndNext() {
  if (!currentValue.value) { ElMessage.warning('请先输入成绩'); return }
  saving.value = true
  try {
    await api.post('/scores/batch', {
      scores: [{
        student_id: currentStudent.value.id,
        event_id: selectedEventId.value,
        raw_value: currentValue.value,
        test_date: testDate.value
      }]
    })
    ElMessage.success('保存成功')
    if (currentIndex.value < students.value.length - 1) {
      nextStudent()
    } else {
      ElMessage.success('全部录入完成！')
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.student-card { max-width: 400px; margin: 20px auto; text-align: center; }
.student-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.student-info { flex: 1; }
.student-name { font-size: 22px; font-weight: bold; }
.student-id { color: #999; font-size: 14px; }
.progress { color: #ccc; font-size: 12px; margin-top: 4px; }
.input-area { margin: 20px 0; }
.score-input :deep(.el-input__inner) { text-align: center; font-size: 24px; }
.voice-area { margin: 16px 0; }
.score-result { margin: 20px 0; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.earned { font-size: 28px; font-weight: bold; color: #409EFF; }
.change { font-size: 14px; margin-top: 8px; }
.praise { color: #67c23a; font-weight: bold; }
.warning { color: #e6a23c; font-weight: bold; }
.muted { color: #ccc; }
.save-btn { width: 100%; margin-top: 16px; }
.entry-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; font-size: 16px; font-weight: bold; }
</style>

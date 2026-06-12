<template>
  <div class="se-page">
    <!-- Selection step -->
    <div v-if="!started" class="se-select">
      <el-button text @click="$router.push('/admin/dashboard')" class="se-back-top">← 返回仪表盘</el-button>
      <div class="se-select-card">
        <div class="se-icon-wrap">📋</div>
        <h3>成绩录入</h3>
        <p class="se-sub">选择班级和项目，开始逐人录入</p>
        <el-form label-width="70px" class="se-form">
          <el-form-item label="班级">
            <el-select v-model="selectedClassId" placeholder="请选择" size="large" style="width:100%">
              <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目">
            <el-select v-model="selectedEventId" placeholder="请选择" size="large" style="width:100%">
              <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker v-model="testDate" type="date" value-format="YYYY-MM-DD" size="large" style="width:100%" />
          </el-form-item>
          <el-button type="primary" size="large" @click="startEntry" :disabled="!selectedClassId || !selectedEventId" class="se-start-btn">
            开始逐人录入
          </el-button>
          <div style="margin-top:12px;text-align:center">
            <input type="file" ref="batchFile" accept=".xlsx" style="display:none" @change="batchImport" />
            <el-button :disabled="!selectedClassId" @click="$refs.batchFile.click()" style="width:100%">
              📊 批量导入成绩
            </el-button>
            <el-button :disabled="!selectedClassId" @click="downloadTemplate" style="width:100%;margin-top:6px">
              📥 下载导入模板
            </el-button>
            <div style="font-size:11px;color:#999;margin-top:4px">
              Excel格式：学号 | 姓名 | 项目1 | 项目2 ...
            </div>
          </div>
        </el-form>
      </div>
    </div>

    <!-- Entry step -->
    <div v-else class="se-entry">
      <div class="se-topbar">
        <el-button text @click="started = false" class="se-back">← 返回</el-button>
        <span class="se-title">{{ selectedClassLabel }}</span>
        <span class="se-event-tag">{{ selectedEventName }}</span>
      </div>

      <div class="se-card" v-if="currentStudent">
        <div class="se-nav">
          <el-button circle @click="prevStudent" :disabled="currentIndex === 0">◀</el-button>
          <div class="se-student">
            <div class="se-name">{{ currentStudent.name }} ({{ currentStudent.gender === 'M' ? '男' : '女' }})</div>
            <div class="se-id">{{ currentStudent.student_id }}</div>
          </div>
          <el-button circle @click="nextStudent" :disabled="currentIndex >= students.length - 1">▶</el-button>
        </div>
        <div class="se-progress">
          <el-progress :percentage="Math.round((currentIndex + 1) / students.length * 100)" :stroke-width="4" :show-text="false" />
          <span class="se-progress-text">{{ currentIndex + 1 }} / {{ students.length }}</span>
        </div>

        <div class="se-input-area">
          <el-input
            v-model="currentValue"
            :placeholder="placeholder"
            size="large"
            class="se-input"
            @input="onValueChange"
            clearable
          />
          <div class="se-hint">支持: {{ formatHint }}</div>
        </div>

        <el-button type="primary" size="large" @click="saveAndNext" :loading="saving" class="se-save">
          💾 保存并下一个
        </el-button>

        <div class="se-result" v-if="currentScore !== null">
          <div class="se-score">{{ currentScore }} <span>分</span></div>
          <div class="se-change">
            <template v-if="previousScore !== null">
              <span class="se-prev">上次 {{ previousScore }}分</span>
              <span v-if="isPraise" class="se-praise">↑ 进步表扬 ✨</span>
              <span v-else-if="isWarning" class="se-warning">↓ 橙色预警 🟠</span>
              <span v-else-if="change > 0" class="se-up">↑ +{{ change }}</span>
              <span v-else-if="change < 0" class="se-down">↓ {{ change }}</span>
              <span v-else class="se-same">→ 持平</span>
            </template>
            <span v-else class="se-first">首次测试</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

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
  if (fmt === 'time_ms') return "3分30 / 3'30"
  if (fmt === 'decimal_seconds') return '8.1'
  if (fmt === 'decimal_meters') return '1.95'
  return '170'
})

const formatHint = computed(() => {
  if (!selectedEvent.value) return ''
  const fmt = selectedEvent.value.input_format
  if (fmt === 'time_ms') return '3分30、3分30秒、3\'30、3\'30"'
  if (fmt === 'decimal_seconds') return '秒.百分秒，如 8.1、22.51'
  if (fmt === 'decimal_meters') return '十进制米，如 1.95'
  return '整数，如 170'
})

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([api.get('/events/classes'), api.get('/events')])
  classes.value = cRes.data; events.value = eRes.data
})

async function startEntry() {
  const res = await api.get(`/scores/student-list/${selectedClassId.value}`, { params: { event_id: selectedEventId.value } })
  students.value = res.data; currentIndex.value = 0; resetInput(); started.value = true
}

function prevStudent() { if (currentIndex.value > 0) { currentIndex.value--; resetInput() } }
function nextStudent() { if (currentIndex.value < students.value.length - 1) { currentIndex.value++; resetInput() } }

function resetInput() {
  currentValue.value = ''; currentScore.value = null; previousScore.value = null
  change.value = null; isPraise.value = false; isWarning.value = false
}

async function onValueChange() {
  if (!currentValue.value) { currentScore.value = null; return }
  try {
    const res = await api.post('/scores/batch', { scores: [{ student_id: currentStudent.value.id, event_id: selectedEventId.value, raw_value: currentValue.value, test_date: testDate.value }] })
    const r = res.data[0]
    currentScore.value = r.earned_score; previousScore.value = r.previous_score
    change.value = r.change; isPraise.value = r.is_praise; isWarning.value = r.is_warning
  } catch { currentScore.value = null }
}

async function batchImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const loading = ElMessage({ message: '正在导入成绩...', type: 'info', duration: 0 })
  try {
    const form = new FormData()
    form.append('file', file)
    const params = { class_id: selectedClassId.value, test_date: testDate.value }
    const res = await api.post('/scores/batch-import', form, { params })
    loading.close()
    const r = res.data
    let msg = `导入成功：${r.imported} 条成绩`
    if (r.skipped.length) msg += `，${r.skipped.length} 条跳过`
    ElMessage.success({ message: msg, duration: 5000 })
    if (r.skipped.length > 0 && r.skipped.length <= 20) {
      setTimeout(() => {
        ElMessage.warning({ message: r.skipped.join('；'), duration: 8000 })
      }, 500)
    }
    // Clear file input
    e.target.value = ''
  } catch (err) {
    loading.close()
    ElMessage.error(err.response?.data?.detail || '导入失败')
  }
}

async function downloadTemplate() {
  try {
    const res = await api.get('/scores/batch-import-template', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '成绩导入模板.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板已下载')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '下载模板失败')
  }
}

async function saveAndNext() {
  if (!currentValue.value) { ElMessage.warning('请先输入成绩'); return }
  saving.value = true
  try {
    await api.post('/scores/batch', { scores: [{ student_id: currentStudent.value.id, event_id: selectedEventId.value, raw_value: currentValue.value, test_date: testDate.value }] })
    ElMessage.success('保存成功')
    if (currentIndex.value < students.value.length - 1) { nextStudent() } else { ElMessage.success('全部录入完成！') }
  } catch { ElMessage.error('保存失败') } finally { saving.value = false }
}
</script>

<style scoped>
.se-page { max-width: 480px; margin: 0 auto; }
.se-back-top { margin-bottom: 8px; }
.se-select { padding: 20px 12px; }
.se-select-card { background: white; border-radius: 16px; padding: 32px 20px; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }
.se-icon-wrap { font-size: 48px; margin-bottom: 8px; }
.se-select-card h3 { margin: 0 0 4px; font-size: 20px; color: #303133; }
.se-sub { color: #999; font-size: 13px; margin: 0 0 24px; }
.se-form { text-align: left; }
.se-start-btn { width: 100%; height: 44px; font-size: 16px; border-radius: 10px; }
.se-topbar { display: flex; align-items: center; gap: 8px; padding: 8px 0 16px; }
.se-back { font-size: 14px; }
.se-title { font-weight: 600; font-size: 15px; }
.se-event-tag { background: #ecf5ff; color: #409EFF; padding: 2px 10px; border-radius: 99px; font-size: 12px; }
.se-card { background: white; border-radius: 16px; padding: 24px 20px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); text-align: center; }
.se-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.se-student { flex: 1; }
.se-name { font-size: 24px; font-weight: 700; color: #303133; }
.se-id { font-size: 14px; color: #909399; margin-top: 2px; }
.se-progress { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; }
.se-progress-text { font-size: 11px; color: #c0c4cc; white-space: nowrap; }
.se-input-area { margin: 20px 0 8px; }
.se-input :deep(.el-input__inner) { text-align: center; font-size: 28px; height: 56px; border-radius: 12px; border: 2px solid #e4e7ed; }
.se-input :deep(.el-input__inner:focus) { border-color: #409EFF; }
.se-hint { font-size: 11px; color: #c0c4cc; margin-top: 6px; }
.se-result { margin: 16px 0; padding: 20px; background: linear-gradient(135deg, #f0f5ff 0%, #fafbff 100%); border-radius: 14px; }
.se-score { font-size: 40px; font-weight: 800; color: #409EFF; }
.se-score span { font-size: 18px; font-weight: 400; color: #909399; }
.se-change { margin-top: 8px; font-size: 13px; }
.se-prev { color: #909399; margin-right: 8px; }
.se-praise { color: #67c23a; font-weight: 600; }
.se-warning { color: #e6a23c; font-weight: 600; animation: warn-pulse 1.5s ease-in-out infinite; }
@keyframes warn-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
.se-up { color: #67c23a; }
.se-down { color: #f56c6c; }
.se-same { color: #909399; }
.se-first { color: #c0c4cc; }
.se-save { width: 100%; height: 48px; font-size: 16px; border-radius: 12px; }
</style>

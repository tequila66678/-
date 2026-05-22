<template>
  <el-dialog v-model="visible" title="导出成绩" width="95%" :close-on-click-modal="false" @close="reset">
    <el-form label-width="70px" size="default">
      <el-form-item label="范围">
        <el-radio-group v-model="scope">
          <el-radio value="school">全校</el-radio>
          <el-radio value="class">班级</el-radio>
          <el-radio value="student">个人</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="scope === 'class'" label="班级">
        <el-select v-model="classId" placeholder="选择班级" style="width:100%">
          <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="scope === 'student'" label="学生">
        <el-input v-model="studentSearch" placeholder="搜索学号或姓名" @change="searchStudent" />
        <span v-if="foundStudent" style="margin-left:8px;color:#409EFF">{{ foundStudent.name }}({{ foundStudent.student_id }})</span>
      </el-form-item>
      <el-form-item label="项目">
        <el-select v-model="eventIds" multiple placeholder="全部项目" style="width:100%" collapse-tags>
          <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width:100%" />
      </el-form-item>
      <el-form-item label="模式">
        <el-radio-group v-model="mode">
          <el-radio value="all">全部成绩</el-radio>
          <el-radio value="best">最优成绩</el-radio>
          <el-radio value="latest">最近成绩</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="格式">
        <el-radio-group v-model="format">
          <el-radio value="xlsx">Excel (.xlsx)</el-radio>
          <el-radio value="txt">文本 (.txt)</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <div class="ed-preview" v-if="preview.length">
      <div class="ed-preview-title">预览 (共 {{ total }} 条)</div>
      <div class="ed-preview-table">
        <div class="ed-row ed-header">
          <span>学号</span><span>姓名</span><span>项目</span><span>成绩</span><span>得分</span><span>日期</span>
        </div>
        <div v-for="(r, i) in preview" :key="i" class="ed-row">
          <span>{{ r.student_id }}</span><span>{{ r.student_name }}</span>
          <span>{{ r.event_name }}</span><span>{{ r.raw_value }}</span>
          <span>{{ r.earned_score }}</span><span>{{ r.test_date }}</span>
        </div>
      </div>
    </div>

    <div v-if="previewing || downloading" style="text-align:center;padding:20px">
      <el-progress :percentage="exportProgress" :stroke-width="16" :text-inside="true" :status="exportProgress === 100 ? 'success' : ''" />
      <p style="color:#909399;margin-top:8px">{{ downloading ? '正在生成文件...' : '正在查询数据...' }}</p>
    </div>

    <template #footer>
      <el-button @click="doPreview" :loading="previewing">预览</el-button>
      <el-button type="primary" @click="doDownload" :loading="downloading">确认导出</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const props = defineProps({ modelValue: Boolean, classes: Array, events: Array })
const emit = defineEmits(['update:modelValue'])
const visible = ref(false)

const scope = ref('school')
const classId = ref(null)
const studentSearch = ref('')
const foundStudent = ref(null)
const studentId = ref(null)
const eventIds = ref([])
const dateRange = ref(null)
const mode = ref('all')
const format = ref('xlsx')

const preview = ref([])
const total = ref(0)
const previewing = ref(false)
const downloading = ref(false)
const exportProgress = ref(0)

watch(() => props.modelValue, v => { visible.value = v })

function reset() {
  emit('update:modelValue', false)
  scope.value = 'school'; classId.value = null; studentSearch.value = ''; foundStudent.value = null
  studentId.value = null; eventIds.value = []; dateRange.value = null; mode.value = 'all'; format.value = 'xlsx'
  preview.value = []; total.value = 0
}

async function searchStudent() {
  if (!studentSearch.value) return
  const res = await api.get('/students', { params: { search: studentSearch.value, page_size: 5 } })
  if (res.data.length > 0) {
    foundStudent.value = res.data[0]; studentId.value = res.data[0].id
  }
}

async function doPreview() {
  if (scope.value === 'class' && !classId.value) { ElMessage.warning('请选择班级'); return }
  if (scope.value === 'student' && !studentId.value) { ElMessage.warning('请搜索学生'); return }
  previewing.value = true; exportProgress.value = 10
  const timer = setInterval(() => { if (exportProgress.value < 85) exportProgress.value += 15 }, 200)
  try {
    const params = { scope: scope.value, mode: mode.value }
    if (classId.value) params.class_id = classId.value
    if (studentId.value) params.student_id = studentId.value
    if (eventIds.value.length) params.event_ids = eventIds.value.join(',')
    if (dateRange.value) { params.date_from = dateRange.value[0]; params.date_to = dateRange.value[1] }
    const res = await api.post('/scores/export/preview', null, { params })
    preview.value = res.data.rows
    total.value = res.data.total
    exportProgress.value = 100
    ElMessage.success(`查询到 ${total.value} 条记录`)
  } catch { ElMessage.error('预览失败') } finally { clearInterval(timer); previewing.value = false }
}

function doDownload() {
  if (scope.value === 'class' && !classId.value) { ElMessage.warning('请选择班级'); return }
  if (scope.value === 'student' && !studentId.value) { ElMessage.warning('请搜索学生'); return }
  downloading.value = true; exportProgress.value = 50
  const timer = setInterval(() => { if (exportProgress.value < 95) exportProgress.value += 10 }, 150)
  const params = { scope: scope.value, mode: mode.value, format: format.value }
  if (classId.value) params.class_id = classId.value
  if (studentId.value) params.student_id = studentId.value
  if (eventIds.value.length) params.event_ids = eventIds.value.join(',')
  if (dateRange.value) { params.date_from = dateRange.value[0]; params.date_to = dateRange.value[1] }
  const token = localStorage.getItem('admin_token')
  if (token) params.token = token
  const qs = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
  window.open(`/api/scores/export/download?${qs}`)
  setTimeout(() => { exportProgress.value = 100; clearInterval(timer); downloading.value = false }, 1000)
}
</script>

<style scoped>
.ed-preview { margin-top: 12px; }
.ed-preview-title { font-size: 13px; color: #666; margin-bottom: 8px; }
.ed-preview-table { border: 1px solid #eee; border-radius: 8px; overflow: auto; max-height: 300px; }
.ed-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 0.6fr 1.2fr; padding: 6px 8px; font-size: 12px; border-bottom: 1px solid #f0f0f0; }
.ed-header { background: #f5f7fa; font-weight: bold; color: #666; position: sticky; top: 0; }
</style>

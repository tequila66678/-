<template>
  <div class="settings-page">
    <el-button text @click="$router.push('/admin/dashboard')" class="back-btn">← 返回仪表盘</el-button>
    <h3 style="margin:8px 0 12px">开发人员选项</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane v-if="isSuper" label="项目设置" name="events">
        <el-button size="small" @click="showAddEvent = true" style="margin-bottom:8px">新增项目</el-button>
        <div v-for="e in events" :key="e.id" class="event-card">
          <div class="ec-info">
            <div class="ec-name">{{ e.name }}</div>
            <div class="ec-meta">{{ e.gender === 'M' ? '男' : e.gender === 'F' ? '女' : '通用' }} | {{ e.higher_better ? '越大越好' : '越小越好' }} | 单位:{{ e.unit }}</div>
          </div>
          <div class="ec-actions">
            <el-button text type="primary" size="small" @click="editStandards(e)">标准</el-button>
            <el-button text type="danger" size="small" @click="deleteEvent(e)">删除</el-button>
          </div>
        </div>

        <el-dialog v-model="showAddEvent" title="新增项目" width="90%">
          <el-form label-width="60px">
            <el-form-item label="名称"><el-input v-model="newEvent.name" /></el-form-item>
            <el-form-item label="性别">
              <el-select v-model="newEvent.gender" style="width:100%">
                <el-option label="通用" value="both" /><el-option label="男" value="M" /><el-option label="女" value="F" />
              </el-select>
            </el-form-item>
            <el-form-item label="方向">
              <el-select v-model="newEvent.higher_better" style="width:100%">
                <el-option label="越大越好" :value="true" /><el-option label="越小越好" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item label="单位"><el-input v-model="newEvent.unit" /></el-form-item>
            <el-form-item label="格式">
              <el-select v-model="newEvent.input_format" style="width:100%">
                <el-option label="分'秒" value="time_ms" /><el-option label="十进制秒" value="decimal_seconds" />
                <el-option label="十进制米" value="decimal_meters" /><el-option label="整数" value="integer" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addEvent" style="width:100%">确认新增</el-button>
          </el-form>
        </el-dialog>

        <el-dialog v-model="showStandards" title="编辑评分标准" width="90%">
          <div v-for="i in 10" :key="i" style="display:flex;align-items:center;margin-bottom:8px">
            <span style="width:40px;font-size:13px">{{ 11 - i }}分</span>
            <el-input v-model="standardsForm[i - 1]" style="flex:1" size="small" />
          </div>
          <el-button type="primary" @click="saveStandards" style="width:100%">保存</el-button>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="管理员" name="admins">
        <el-button size="small" @click="showAddAdmin = true" style="margin-bottom:8px">新增管理员</el-button>
        <div v-for="a in admins" :key="a.id" class="admin-card">
          <div>
            <div class="ad-name">{{ a.display_name }}</div>
            <div class="ad-role">{{ a.username }} | {{ a.role === 'super' ? '超管' : a.role === 'school_admin' ? '学校管理员' : '老师' }}</div>
          </div>
          <div style="display:flex;gap:4px">
            <el-button v-if="isSuper" text type="primary" size="small" @click="editAdmin(a)">编辑</el-button>
            <el-button text type="danger" size="small" @click="deleteAdmin(a)">删除</el-button>
          </div>
        </div>

        <el-dialog v-model="showAddAdmin" title="新增管理员" width="90%">
          <el-form label-width="60px">
            <el-form-item label="用户名"><el-input v-model="newAdmin.username" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="newAdmin.password" type="password" /></el-form-item>
            <el-form-item label="姓名"><el-input v-model="newAdmin.display_name" /></el-form-item>
            <el-form-item label="角色">
              <el-select v-model="newAdmin.role" style="width:100%">
                <el-option v-if="isSuper" label="超管" value="super" />
                <el-option v-if="isSuper" label="学校管理员" value="school_admin" />
                <el-option label="老师" value="teacher" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="isSuper && newAdmin.role !== 'super'" label="学校">
              <el-select v-model="newAdmin.school_id" style="width:100%" placeholder="选择学校">
                <el-option v-for="s in allSchools" :key="s.id" :value="s.id" :label="s.name" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addAdmin" style="width:100%">确认新增</el-button>
          </el-form>
        </el-dialog>

        <el-dialog v-model="showEditAdmin" title="编辑管理员" width="90%">
          <el-form label-width="60px">
            <el-form-item label="用户名"><el-input :model-value="editAdminForm.username" disabled /></el-form-item>
            <el-form-item label="姓名"><el-input v-model="editAdminForm.display_name" /></el-form-item>
            <el-form-item label="新密码"><el-input v-model="editAdminForm.password" type="password" placeholder="留空不修改" /></el-form-item>
            <el-form-item label="角色">
              <el-select v-model="editAdminForm.role" style="width:100%">
                <el-option label="超管" value="super" />
                <el-option label="学校管理员" value="school_admin" />
                <el-option label="老师" value="teacher" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="editAdminForm.role !== 'super'" label="学校">
              <el-select v-model="editAdminForm.school_id" style="width:100%" placeholder="选择学校">
                <el-option v-for="s in allSchools" :key="s.id" :value="s.id" :label="s.name" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="saveEditAdmin" style="width:100%">保存修改</el-button>
          </el-form>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane v-if="isSuper" label="学校管理" name="schools">
        <el-button size="small" @click="showAddSchool = true" style="margin-bottom:8px">新建学校</el-button>
        <div v-for="s in allSchools" :key="s.id" class="admin-card">
          <div>
            <div class="ad-name">{{ s.name }}</div>
          </div>
          <div style="display:flex;gap:6px">
            <el-button text type="primary" size="small" @click="editSchool(s)">编辑</el-button>
            <el-button text type="danger" size="small" @click="deleteSchool(s)">删除</el-button>
          </div>
        </div>

        <el-dialog v-model="showAddSchool" title="新建学校" width="90%">
          <el-form label-width="60px">
            <el-form-item label="名称"><el-input v-model="newSchoolName" /></el-form-item>
            <el-button type="primary" @click="addSchool" style="width:100%">确认新建</el-button>
          </el-form>
        </el-dialog>

        <el-dialog v-model="showEditSchool" title="编辑学校" width="90%">
          <el-form label-width="60px">
            <el-form-item label="名称"><el-input v-model="editSchoolName" /></el-form-item>
            <el-button type="primary" @click="saveEditSchool" style="width:100%">保存</el-button>
          </el-form>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="系统设置" name="config">
        <el-form label-width="100px" style="max-width:100%">
          <el-form-item label="学校名称">
            <el-input v-model="config.school_name" />
          </el-form-item>
          <el-form-item label="表扬阈值">
            <el-input-number v-model="config.praise_threshold" :min="1" :max="10" size="small" />
          </el-form-item>
          <el-form-item label="预警阈值">
            <el-input-number v-model="config.warning_threshold" :min="1" :max="10" size="small" />
          </el-form-item>
          <el-form-item label="设计者">
            <el-input v-model="config.designer" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveConfig" style="width:100%">保存设置</el-button>
          </el-form-item>
        </el-form>

        <el-divider />
        <h4 style="margin-bottom:8px">数据维护</h4>
        <el-button @click="backupData" style="width:100%;margin-bottom:8px">备份全部数据 (Excel)</el-button>
        <input type="file" ref="restoreFile" accept=".xlsx" style="display:none" @change="restoreData" />
        <el-button @click="$refs.restoreFile.click()" style="width:100%;margin-bottom:8px">导入备份数据</el-button>
        <el-divider />
        <h4 style="color:#e6a23c;margin-bottom:8px">危险操作</h4>
        <el-button type="danger" @click="clearScores" style="width:100%">清空所有成绩数据</el-button>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const adminInfo = JSON.parse(localStorage.getItem('admin_info') || '{}')
const isSuper = adminInfo.role === 'super'

const activeTab = ref(isSuper ? 'events' : 'admins')
const events = ref([])
const admins = ref([])
const config = ref({ school_name: '', praise_threshold: 1, warning_threshold: 2, designer: '' })

const showAddEvent = ref(false)
const newEvent = ref({ name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' })
const showStandards = ref(false)
const editingEventId = ref(null)
const standardsForm = ref(Array(10).fill(''))

const showAddAdmin = ref(false)
const newAdmin = ref({ username: '', password: '', display_name: '', role: 'teacher', school_id: null })
const showEditAdmin = ref(false)
const editAdminForm = ref({ id: null, username: '', display_name: '', password: '', role: 'teacher', school_id: null })
const allSchools = ref([])

onMounted(async () => {
  try {
    const [eRes, aRes, cRes] = await Promise.all([api.get('/events'), api.get('/admins'), api.get('/config')])
    events.value = eRes.data; admins.value = aRes.data
    for (const c of cRes.data) { if (c.key in config.value) config.value[c.key] = c.key.includes('threshold') ? parseInt(c.value) : c.value }
  } catch { /* one or more APIs failed — show what we can */ }
  if (isSuper) {
    try { const sRes = await api.get('/schools'); allSchools.value = sRes.data } catch {}
  }
})

async function addEvent() {
  await api.post('/events', newEvent.value); ElMessage.success('已新增'); showAddEvent.value = false
  newEvent.value = { name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' }
  const res = await api.get('/events'); events.value = res.data
}

async function deleteEvent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name}？`); await api.delete(`/events/${row.id}`)
  const res = await api.get('/events'); events.value = res.data
}

function editStandards(row) {
  editingEventId.value = row.id
  const stds = [...row.standards].sort((a, b) => b.score - a.score)
  standardsForm.value = stds.map(s => s.standard_value); showStandards.value = true
}

async function saveStandards() {
  const payload = []
  for (let i = 0; i < 10; i++) { if (standardsForm.value[i]) payload.push({ gender: 'both', score: 10 - i, standard_value: standardsForm.value[i] }) }
  await api.put(`/events/${editingEventId.value}/standards`, payload); ElMessage.success('已更新'); showStandards.value = false
  const res = await api.get('/events'); events.value = res.data
}

async function addAdmin() {
  await api.post('/admins', newAdmin.value); ElMessage.success('已创建'); showAddAdmin.value = false
  const res = await api.get('/admins'); admins.value = res.data
}

async function deleteAdmin(row) {
  await ElMessageBox.confirm(`确定删除 ${row.display_name}？`); await api.delete(`/admins/${row.id}`)
  const res = await api.get('/admins'); admins.value = res.data
}

function editAdmin(a) {
  editAdminForm.value = { id: a.id, username: a.username, display_name: a.display_name, password: '', role: a.role, school_id: a.school_id }
  showEditAdmin.value = true
}

async function saveEditAdmin() {
  const payload = { display_name: editAdminForm.value.display_name, role: editAdminForm.value.role, school_id: editAdminForm.value.school_id }
  if (editAdminForm.value.password) payload.password = editAdminForm.value.password
  await api.put(`/admins/${editAdminForm.value.id}`, payload)
  ElMessage.success('已更新'); showEditAdmin.value = false
  const res = await api.get('/admins'); admins.value = res.data
}

async function saveConfig() {
  for (const [key, value] of Object.entries(config.value)) { await api.put(`/config/${key}`, { value: String(value) }) }
  ElMessage.success('已保存')
}

function backupData() {
  const token = localStorage.getItem('admin_token')
  window.open(`/api/scores/backup-all?token=${encodeURIComponent(token)}`)
}

async function restoreData(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    await ElMessageBox.confirm(
      '导入备份将覆盖当前所有数据（班级、项目、学生、成绩、管理员、设置），此操作不可恢复！确定继续？',
      '危险操作', { type: 'error', confirmButtonText: '确定导入' }
    )
  } catch { return }
  const form = new FormData()
  form.append('file', file)
  try {
    const res = await api.post('/scores/restore-all', form)
    ElMessage.success(`已恢复：${res.data.classes}个班级, ${res.data.events}个项目, ${res.data.students}名学生, ${res.data.scores}条成绩, ${res.data.admins}个管理员, ${res.data.configs}项设置`)
    setTimeout(() => location.reload(), 1500)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '恢复失败')
  }
}

// School management
const showAddSchool = ref(false)
const showEditSchool = ref(false)
const newSchoolName = ref('')
const editSchoolName = ref('')
const editingSchoolId = ref(null)

async function addSchool() {
  if (!newSchoolName.value.trim()) return
  await api.post('/schools', { name: newSchoolName.value.trim() })
  ElMessage.success('学校已创建（含默认项目+班级）')
  showAddSchool.value = false; newSchoolName.value = ''
  const res = await api.get('/schools'); allSchools.value = res.data
}

function editSchool(s) {
  editingSchoolId.value = s.id
  editSchoolName.value = s.name
  showEditSchool.value = true
}

async function saveEditSchool() {
  await api.put(`/schools/${editingSchoolId.value}`, { name: editSchoolName.value.trim() })
  ElMessage.success('已更新'); showEditSchool.value = false
  const res = await api.get('/schools'); allSchools.value = res.data
}

async function deleteSchool(s) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${s.name}」吗？将级联删除该校所有学生、成绩、项目数据。此操作不可恢复！`,
      '危险操作', { type: 'error', confirmButtonText: '下一步' }
    )
  } catch { return }
  try {
    const { value: password } = await ElMessageBox.prompt('请输入超级管理员密码确认', '身份验证', { inputType: 'password', confirmButtonText: '确认删除' })
    if (!password) return
    await api.delete(`/schools/${s.id}`, { params: { password } })
    ElMessage.success('已删除')
    const res = await api.get('/schools'); allSchools.value = res.data
  } catch (err) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

async function clearScores() {
  try {
    await ElMessageBox.confirm('确定清空所有成绩数据吗？此操作不可恢复！', '危险操作', { type: 'error', confirmButtonText: '下一步' })
  } catch { return }
  try {
    const { value: password } = await ElMessageBox.prompt('请输入超级管理员密码以确认操作', '身份验证', { inputType: 'password', confirmButtonText: '确认清空' })
    if (!password) return
    await api.post('/scores/clear-all', { password })
    ElMessage.success('已清空所有成绩')
  } catch (err) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}
</script>

<style scoped>
.back-btn { margin-bottom: 4px; font-size: 13px; }
.event-card, .admin-card { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; border-radius: 8px; margin-bottom: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.ec-name, .ad-name { font-size: 14px; font-weight: bold; }
.ec-meta, .ad-role { font-size: 11px; color: #999; }
</style>

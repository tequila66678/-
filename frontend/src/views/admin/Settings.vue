<template>
  <div class="settings-page">
    <el-button text @click="$router.push('/admin/dashboard')" class="back-btn">← 返回仪表盘</el-button>
    <h3 style="margin:8px 0 12px">开发人员选项</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="项目设置" name="events">
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
            <div class="ad-role">{{ a.username }} | {{ a.is_super ? '超管' : '老师' }}</div>
          </div>
          <el-button text type="danger" size="small" @click="deleteAdmin(a)">删除</el-button>
        </div>

        <el-dialog v-model="showAddAdmin" title="新增管理员" width="90%">
          <el-form label-width="60px">
            <el-form-item label="用户名"><el-input v-model="newAdmin.username" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="newAdmin.password" type="password" /></el-form-item>
            <el-form-item label="姓名"><el-input v-model="newAdmin.display_name" /></el-form-item>
            <el-form-item label="角色">
              <el-select v-model="newAdmin.is_super" style="width:100%">
                <el-option label="老师" :value="false" /><el-option label="超管" :value="true" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addAdmin" style="width:100%">确认新增</el-button>
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

const activeTab = ref('events')
const events = ref([])
const admins = ref([])
const config = ref({ school_name: '', praise_threshold: 1, warning_threshold: 2, designer: '' })

const showAddEvent = ref(false)
const newEvent = ref({ name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' })
const showStandards = ref(false)
const editingEventId = ref(null)
const standardsForm = ref(Array(10).fill(''))

const showAddAdmin = ref(false)
const newAdmin = ref({ username: '', password: '', display_name: '', is_super: false })

onMounted(async () => {
  const [eRes, aRes, cRes] = await Promise.all([api.get('/events'), api.get('/admins'), api.get('/config')])
  events.value = eRes.data; admins.value = aRes.data
  for (const c of cRes.data) { if (c.key in config.value) config.value[c.key] = c.key.includes('threshold') ? parseInt(c.value) : c.value }
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

async function saveConfig() {
  for (const [key, value] of Object.entries(config.value)) { await api.put(`/config/${key}`, { value: String(value) }) }
  ElMessage.success('已保存')
}

async function clearScores() {
  await ElMessageBox.confirm('确定清空所有成绩数据吗？此操作不可恢复！', '危险操作', { type: 'error', confirmButtonText: '确定清空' })
  await api.delete('/scores/clear-all')
  ElMessage.success('已清空所有成绩')
}
</script>

<style scoped>
.back-btn { margin-bottom: 4px; font-size: 13px; }
.event-card, .admin-card { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; border-radius: 8px; margin-bottom: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.ec-name, .ad-name { font-size: 14px; font-weight: bold; }
.ec-meta, .ad-role { font-size: 11px; color: #999; }
</style>

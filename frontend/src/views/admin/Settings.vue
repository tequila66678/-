<template>
  <div>
    <h3>开发人员选项</h3>
    <el-tabs>
      <el-tab-pane label="运动项目设置">
        <el-table :data="events" border>
          <el-table-column prop="name" label="项目名称" />
          <el-table-column label="性别">
            <template #default="{ row }">{{ row.gender === 'M' ? '男' : row.gender === 'F' ? '女' : '通用' }}</template>
          </el-table-column>
          <el-table-column label="方向">
            <template #default="{ row }">{{ row.higher_better ? '越大越好' : '越小越好' }}</template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button text type="primary" @click="editStandards(row)">编辑标准</el-button>
              <el-button text type="danger" @click="deleteEvent(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button @click="showAddEvent = true" style="margin-top:16px">新增项目</el-button>

        <el-dialog v-model="showAddEvent" title="新增项目" width="400px">
          <el-form label-width="80px">
            <el-form-item label="名称"><el-input v-model="newEvent.name" /></el-form-item>
            <el-form-item label="性别">
              <el-select v-model="newEvent.gender">
                <el-option label="通用" value="both" /><el-option label="男" value="M" /><el-option label="女" value="F" />
              </el-select>
            </el-form-item>
            <el-form-item label="方向">
              <el-select v-model="newEvent.higher_better">
                <el-option label="越大越好" :value="true" /><el-option label="越小越好" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item label="单位"><el-input v-model="newEvent.unit" /></el-form-item>
            <el-form-item label="格式">
              <el-select v-model="newEvent.input_format">
                <el-option label="分'秒" value="time_ms" />
                <el-option label="十进制秒" value="decimal_seconds" />
                <el-option label="十进制米" value="decimal_meters" />
                <el-option label="整数" value="integer" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addEvent">确认新增</el-button>
          </el-form>
        </el-dialog>

        <el-dialog v-model="showStandards" title="编辑评分标准" width="500px">
          <el-form v-for="i in 10" :key="i" label-width="60px" :inline="true">
            <el-form-item :label="`${11 - i}分`">
              <el-input v-model="standardsForm[i - 1]" style="width:200px" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="saveStandards">保存</el-button>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="管理员管理">
        <el-table :data="admins" border>
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="display_name" label="姓名" />
          <el-table-column label="角色">
            <template #default="{ row }">{{ row.is_super ? '超管' : '老师' }}</template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button text type="danger" @click="deleteAdmin(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button @click="showAddAdmin = true" style="margin-top:16px">新增管理员</el-button>
        <el-dialog v-model="showAddAdmin" title="新增管理员" width="400px">
          <el-form label-width="80px">
            <el-form-item label="用户名"><el-input v-model="newAdmin.username" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="newAdmin.password" type="password" /></el-form-item>
            <el-form-item label="姓名"><el-input v-model="newAdmin.display_name" /></el-form-item>
            <el-form-item label="角色">
              <el-select v-model="newAdmin.is_super">
                <el-option label="老师" :value="false" /><el-option label="超管" :value="true" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addAdmin">确认新增</el-button>
          </el-form>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="系统设置">
        <el-form label-width="120px" style="max-width:500px">
          <el-form-item label="学校名称">
            <el-input v-model="config.school_name" />
          </el-form-item>
          <el-form-item label="进步表扬阈值">
            <el-input-number v-model="config.praise_threshold" :min="1" :max="10" />
            <span style="margin-left:8px;color:#999">分值提升≥此值即表扬</span>
          </el-form-item>
          <el-form-item label="橙色预警阈值">
            <el-input-number v-model="config.warning_threshold" :min="1" :max="10" />
            <span style="margin-left:8px;color:#999">分值下降≥此值即预警</span>
          </el-form-item>
          <el-form-item label="设计者">
            <el-input v-model="config.designer" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveConfig">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

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
  const [eRes, aRes, cRes] = await Promise.all([
    api.get('/events'),
    api.get('/admins'),
    api.get('/config')
  ])
  events.value = eRes.data
  admins.value = aRes.data
  for (const c of cRes.data) {
    if (c.key in config.value) config.value[c.key] = c.key.includes('threshold') ? parseInt(c.value) : c.value
  }
})

async function addEvent() {
  await api.post('/events', newEvent.value)
  ElMessage.success('项目已新增')
  showAddEvent.value = false
  newEvent.value = { name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' }
  const res = await api.get('/events')
  events.value = res.data
}

async function deleteEvent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name}？`)
  await api.delete(`/events/${row.id}`)
  const res = await api.get('/events')
  events.value = res.data
}

function editStandards(row) {
  editingEventId.value = row.id
  const stds = [...row.standards].sort((a, b) => b.score - a.score)
  standardsForm.value = stds.map(s => s.standard_value)
  showStandards.value = true
}

async function saveStandards() {
  const payload = []
  for (let i = 0; i < 10; i++) {
    if (standardsForm.value[i]) {
      payload.push({ score: 10 - i, standard_value: standardsForm.value[i] })
    }
  }
  await api.put(`/events/${editingEventId.value}/standards`, payload)
  ElMessage.success('标准已更新')
  showStandards.value = false
  const res = await api.get('/events')
  events.value = res.data
}

async function addAdmin() {
  await api.post('/admins', newAdmin.value)
  ElMessage.success('管理员已创建')
  showAddAdmin.value = false
  const res = await api.get('/admins')
  admins.value = res.data
}

async function deleteAdmin(row) {
  await ElMessageBox.confirm(`确定删除管理员 ${row.display_name}？`)
  await api.delete(`/admins/${row.id}`)
  const res = await api.get('/admins')
  admins.value = res.data
}

async function saveConfig() {
  for (const [key, value] of Object.entries(config.value)) {
    await api.put(`/config/${key}`, { value: String(value) })
  }
  ElMessage.success('配置已保存')
}
</script>

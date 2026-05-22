<template>
  <div class="students-page">
    <el-button text @click="$router.push('/admin/dashboard')" class="back-btn">← 返回仪表盘</el-button>
    <h3 style="margin:8px 0 12px">学生管理</h3>

    <div class="toolbar">
      <el-input v-model="search" placeholder="搜索学号/姓名" clearable @change="loadStudents" class="tb-search" size="default" />
      <el-select v-model="filterClassId" placeholder="班级" clearable @change="loadStudents" class="tb-class" size="default">
        <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
      </el-select>
      <div class="tb-actions">
        <el-button size="small" type="primary" @click="showAdd = true">新增</el-button>
        <el-button size="small" @click="downloadTemplate">模板</el-button>
        <el-button size="small" type="primary" @click="showImport = true">导入</el-button>
        <el-button size="small" @click="showBatchEdit = true">批量</el-button>
        <el-button size="small" type="danger" @click="batchDelete" :disabled="!selectedIds.length">删除({{ selectedIds.length }})</el-button>
      </div>
    </div>

    <!-- Desktop table -->
    <div class="desktop-only">
      <el-table :data="students" border stripe size="small" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="name" label="姓名" width="80" />
        <el-table-column label="性别" width="50">
          <template #default="{ row }">{{ row.gender === 'M' ? '男' : '女' }}</template>
        </el-table-column>
        <el-table-column label="班级">
          <template #default="{ row }">{{ row.class_grade }}{{ row.class_name }}</template>
        </el-table-column>
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="editStudent(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="deleteStudent(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Mobile card list -->
    <div class="mobile-only">
      <div v-for="s in students" :key="s.id" class="student-card">
        <el-checkbox :model-value="selectedIds.includes(s.id)" @change="toggleSelect(s.id)" style="margin-right:8px" />
        <div class="sc-info">
          <div class="sc-name">{{ s.name }} <span class="sc-gender">{{ s.gender === 'M' ? '男' : '女' }}</span></div>
          <div class="sc-id">{{ s.student_id }}</div>
          <div class="sc-class">{{ s.class_grade }}{{ s.class_name }}</div>
        </div>
        <div class="sc-actions">
          <el-button text type="primary" size="small" @click="editStudent(s)">编辑</el-button>
          <el-button text type="danger" size="small" @click="deleteStudent(s)">删除</el-button>
        </div>
      </div>
    </div>

    <el-pagination
      v-model:current-page="page" :page-size="50" :total="total"
      layout="prev, pager, next" small
      @current-change="loadStudents"
      style="margin-top:12px;justify-content:center"
    />

    <el-dialog v-model="showImport" title="批量导入" width="90%" :fullscreen="isMobile" @close="importResult=null; importing=false">
      <div v-if="importing" style="text-align:center;padding:20px">
        <el-progress :percentage="importProgress" :stroke-width="20" :text-inside="true" />
        <p style="color:#909399;margin-top:8px">正在导入...</p>
      </div>
      <el-upload v-else :http-request="handleImport" accept=".xlsx" :show-file-list="false" drag>
        <div>拖拽Excel文件或点击上传</div>
      </el-upload>
      <div v-if="importResult" style="margin-top:12px">
        <p>导入: {{ importResult.imported }} 人</p>
        <p v-for="e in importResult.errors" :key="e" style="color:red;font-size:11px">{{ e }}</p>
      </div>
    </el-dialog>

    <el-dialog v-model="showBatchEdit" title="批量修改" width="90%">
      <el-form label-width="70px">
        <el-form-item label="原班级">
          <el-select v-model="batchFromClass" placeholder="留空=全部" clearable style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="新班级">
          <el-select v-model="batchToClass" placeholder="选择目标" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="batchResetPwd">重置密码（学号后6位）</el-checkbox>
        </el-form-item>
        <el-button type="primary" @click="doBatchUpdate" style="width:100%">确认修改</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="showEdit" title="编辑学生" width="90%">
      <el-form label-width="60px" v-if="editForm">
        <el-form-item label="学号"><el-input v-model="editForm.student_id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="editForm.gender" style="width:100%">
            <el-option label="男" value="M" /><el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="editForm.class_id" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="saveEdit" style="width:100%">保存</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="showAdd" title="新增学生" width="90%">
      <el-form label-width="60px">
        <el-form-item label="学号"><el-input v-model="newStudent.student_id" maxlength="6" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="newStudent.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="newStudent.gender" style="width:100%">
            <el-option label="男" value="M" /><el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="newStudent.class_id" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="addStudent" style="width:100%">确认新增</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const students = ref([])
const classes = ref([])
const search = ref('')
const filterClassId = ref(null)
const page = ref(1)
const total = ref(0)

const showImport = ref(false)
const importing = ref(false)
const importProgress = ref(0)
const importResult = ref(null)
const batchFromClass = ref(null)
const batchToClass = ref(null)
const batchResetPwd = ref(false)
const showEdit = ref(false)
const editForm = ref(null)
const showAdd = ref(false)
const newStudent = ref({ student_id: '', name: '', gender: 'M', class_id: null })
const isMobile = ref(window.innerWidth < 768)

onMounted(async () => {
  const res = await api.get('/events/classes')
  classes.value = res.data
  loadStudents()
})

async function loadStudents() {
  const params = { page: page.value, page_size: 50 }
  if (search.value) params.search = search.value
  if (filterClassId.value) params.class_id = filterClassId.value
  try { const res = await api.get('/students', { params }); students.value = res.data } catch {}
}

function downloadTemplate() { window.open('/api/students/template/download') }

async function handleImport({ file }) {
  importing.value = true; importProgress.value = 0
  const timer = setInterval(() => { if (importProgress.value < 90) importProgress.value += 10 }, 300)
  try {
    const form = new FormData(); form.append('file', file)
    const res = await api.post('/students/batch-import', form)
    importProgress.value = 100
    importResult.value = res.data; loadStudents()
  } finally { clearInterval(timer); importing.value = false }
}

async function doBatchUpdate() {
  await api.put('/students/batch/update', { class_id: batchFromClass.value, new_class_id: batchToClass.value || undefined, reset_password: batchResetPwd.value })
  ElMessage.success('批量修改成功'); showBatchEdit.value = false; loadStudents()
}

function editStudent(row) {
  editForm.value = { id: row.id, student_id: row.student_id, name: row.name, gender: row.gender, class_id: row.class_id }
  showEdit.value = true
}

async function saveEdit() {
  await api.put(`/students/${editForm.value.id}`, { student_id: editForm.value.student_id, name: editForm.value.name, gender: editForm.value.gender, class_id: editForm.value.class_id })
  ElMessage.success('修改成功'); showEdit.value = false; loadStudents()
}

async function addStudent() {
  if (!newStudent.value.class_id) { ElMessage.warning('请选择班级'); return }
  try {
    await api.post('/students', newStudent.value)
    ElMessage.success('已新增')
    showAdd.value = false
    newStudent.value = { student_id: '', name: '', gender: 'M', class_id: null }
    loadStudents()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '添加失败')
  }
}

const selectedIds = ref([])

function onSelectionChange(rows) { selectedIds.value = rows.map(r => r.id) }
function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 名学生？`, '批量删除', { type: 'error' })
  await api.delete('/students/batch-delete', { data: selectedIds.value })
  ElMessage.success('删除成功'); selectedIds.value = []; loadStudents()
}

async function deleteStudent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name} (${row.student_id})？`, '确认删除', { type: 'warning' })
  await api.delete(`/students/${row.id}`); ElMessage.success('删除成功'); loadStudents()
}
</script>

<style scoped>
.back-btn { margin-bottom: 4px; font-size: 13px; }
.toolbar { display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; }
.tb-search { flex: 1; min-width: 120px; }
.tb-class { width: 110px; flex-shrink: 0; }
.tb-actions { display: flex; gap: 4px; }
.student-card { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: white; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.sc-name { font-size: 15px; font-weight: bold; }
.sc-gender { font-size: 12px; color: #999; margin-left: 6px; }
.sc-id { font-size: 12px; color: #666; }
.sc-class { font-size: 12px; color: #999; }
.sc-actions { display: flex; gap: 4px; flex-shrink: 0; }
@media (min-width: 768px) { .mobile-only { display: none; } }
@media (max-width: 767px) { .desktop-only { display: none; } }
</style>

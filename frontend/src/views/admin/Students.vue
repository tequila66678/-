<template>
  <div>
    <h3>学生管理</h3>

    <el-row :gutter="10" style="margin-bottom:16px">
      <el-col :span="6">
        <el-input v-model="search" placeholder="搜索学号/姓名" clearable @change="loadStudents" />
      </el-col>
      <el-col :span="6">
        <el-select v-model="filterClassId" placeholder="筛选班级" clearable @change="loadStudents" style="width:100%">
          <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
        </el-select>
      </el-col>
      <el-col :span="12" style="text-align:right">
        <el-button @click="downloadTemplate">下载导入模板</el-button>
        <el-button type="primary" @click="showImport = true">批量导入</el-button>
        <el-button @click="showBatchEdit = true">批量修改</el-button>
      </el-col>
    </el-row>

    <el-table :data="students" border stripe style="width:100%">
      <el-table-column prop="student_id" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column label="性别" width="60">
        <template #default="{ row }">{{ row.gender === 'M' ? '男' : '女' }}</template>
      </el-table-column>
      <el-table-column label="班级">
        <template #default="{ row }">{{ row.class_grade }}{{ row.class_name }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button text type="primary" @click="editStudent(row)">编辑</el-button>
          <el-button text type="danger" @click="deleteStudent(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="50"
      :total="total"
      layout="prev, pager, next, total"
      @current-change="loadStudents"
      style="margin-top:16px;justify-content:center"
    />

    <el-dialog v-model="showImport" title="批量导入学生" width="500px">
      <el-upload
        :http-request="handleImport"
        accept=".xlsx"
        :show-file-list="false"
        drag
      >
        <div>拖拽Excel文件到此处或点击上传</div>
      </el-upload>
      <div v-if="importResult" style="margin-top:16px">
        <p>导入成功: {{ importResult.imported }} 人</p>
        <p v-for="e in importResult.errors" :key="e" style="color:red;font-size:12px">{{ e }}</p>
      </div>
    </el-dialog>

    <el-dialog v-model="showBatchEdit" title="批量修改" width="400px">
      <el-form label-width="80px">
        <el-form-item label="原班级">
          <el-select v-model="batchFromClass" placeholder="留空=全部" clearable style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="新班级">
          <el-select v-model="batchToClass" placeholder="选择目标班级" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="batchResetPwd">重置密码（学号后6位）</el-checkbox>
        </el-form-item>
        <el-button type="primary" @click="doBatchUpdate">确认修改</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="showEdit" title="编辑学生" width="400px">
      <el-form label-width="80px" v-if="editForm">
        <el-form-item label="学号"><el-input v-model="editForm.student_id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="editForm.gender">
            <el-option label="男" value="M" /><el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="editForm.class_id" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="saveEdit">保存</el-button>
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
const showBatchEdit = ref(false)
const showEdit = ref(false)
const importResult = ref(null)
const batchFromClass = ref(null)
const batchToClass = ref(null)
const batchResetPwd = ref(false)
const editForm = ref(null)

onMounted(async () => {
  const res = await api.get('/events/classes')
  classes.value = res.data
  loadStudents()
})

async function loadStudents() {
  const params = { page: page.value, page_size: 50 }
  if (search.value) params.search = search.value
  if (filterClassId.value) params.class_id = filterClassId.value
  try {
    const res = await api.get('/students', { params })
    students.value = res.data
  } catch {}
}

function downloadTemplate() {
  window.open('/api/students/template/download')
}

async function handleImport({ file }) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/students/batch-import', form)
  importResult.value = res.data
  loadStudents()
}

async function doBatchUpdate() {
  await api.put('/students/batch/update', {
    class_id: batchFromClass.value,
    new_class_id: batchToClass.value || undefined,
    reset_password: batchResetPwd.value
  })
  ElMessage.success('批量修改成功')
  showBatchEdit.value = false
  loadStudents()
}

function editStudent(row) {
  editForm.value = { id: row.id, student_id: row.student_id, name: row.name, gender: row.gender, class_id: row.class_id }
  showEdit.value = true
}

async function saveEdit() {
  await api.put(`/students/${editForm.value.id}`, {
    student_id: editForm.value.student_id,
    name: editForm.value.name,
    gender: editForm.value.gender,
    class_id: editForm.value.class_id
  })
  ElMessage.success('修改成功')
  showEdit.value = false
  loadStudents()
}

async function deleteStudent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name} (${row.student_id})？`, '确认删除', { type: 'warning' })
  await api.delete(`/students/${row.id}`)
  ElMessage.success('删除成功')
  loadStudents()
}
</script>

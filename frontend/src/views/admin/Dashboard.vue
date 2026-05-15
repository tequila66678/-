<template>
  <div>
    <h3>欢迎使用体育成绩管理系统</h3>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>快捷入口</template>
          <el-button type="primary" @click="$router.push('/admin/score-entry')">成绩录入</el-button>
          <el-button @click="$router.push('/admin/students')">学生管理</el-button>
          <el-button @click="$router.push('/admin/statistics')">统计分析</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

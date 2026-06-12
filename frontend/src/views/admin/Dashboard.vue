<template>
  <div class="dashboard">
    <h3>欢迎使用体育成绩管理系统</h3>
    <div class="dash-cards">
      <div class="dash-card" @click="$router.push('/admin/score-entry')">
        <div class="dc-icon">📝</div>
        <div class="dc-title">成绩录入</div>
        <div class="dc-desc">逐人录入 + 语音 + 实时打分</div>
      </div>
      <div class="dash-card" @click="$router.push('/admin/students')">
        <div class="dc-icon">👥</div>
        <div class="dc-title">学生管理</div>
        <div class="dc-desc">导入 / 修改 / 删除</div>
      </div>
      <div class="dash-card" @click="$router.push('/admin/statistics')">
        <div class="dc-icon">📈</div>
        <div class="dc-title">统计分析</div>
        <div class="dc-desc">班级 & 个人统计</div>
      </div>
      <div v-if="adminInfo?.role !== 'teacher'" class="dash-card" @click="$router.push('/admin/settings')">
        <div class="dc-icon">⚙️</div>
        <div class="dc-title">系统设置</div>
        <div class="dc-desc">项目 / 标准 / 管理员</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const adminInfo = ref(null)
onMounted(() => {
  const info = localStorage.getItem('admin_info')
  if (info) adminInfo.value = JSON.parse(info)
})
</script>

<style scoped>
.dashboard { max-width: 600px; }
.dashboard h3 { margin-bottom: 20px; }
.dash-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.dash-card { background: white; border-radius: 14px; padding: 24px 16px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.05); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
.dash-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.dash-card:active { transform: scale(0.97); }
.dc-icon { font-size: 36px; margin-bottom: 8px; }
.dc-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.dc-desc { font-size: 12px; color: #999; }
@media (max-width: 400px) { .dash-cards { grid-template-columns: repeat(2, 1fr); } }
</style>

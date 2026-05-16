<template>
  <el-button
    :type="recording ? 'danger' : 'default'"
    circle
    size="large"
    @click="startRecording"
    :loading="processing"
  >
    {{ recording ? '⏹' : '🎤' }}
  </el-button>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['result'])
const recording = ref(false)
const processing = ref(false)

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const recognition = SpeechRecognition ? new SpeechRecognition() : null

if (recognition) {
  recognition.lang = 'zh-CN'
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript
    const result = convertChineseNumbers(text)
    emit('result', result)
    processing.value = false
  }

  recognition.onerror = (event) => {
    const errors = {
      'not-allowed': '麦克风权限被拒绝，请在浏览器设置中允许麦克风',
      'network': '网络无法连接语音服务，请手动输入成绩',
      'no-speech': '未检测到语音，请靠近麦克风再试',
      'aborted': '录音已取消'
    }
    ElMessage.warning(errors[event.error] || '语音识别失败，请手动输入')
    recording.value = false
    processing.value = false
  }

  recognition.onend = () => {
    recording.value = false
  }
}

function startRecording() {
  if (!recognition) {
    ElMessage.warning('您的浏览器不支持语音识别，请使用Chrome浏览器')
    return
  }
  recording.value = true
  processing.value = true
  recognition.start()
  setTimeout(() => {
    if (recording.value) {
      recognition.stop()
    }
  }, 1500)
}

function convertChineseNumbers(text) {
  const map = {
    '零': '0', '一': '1', '二': '2', '三': '3', '四': '4',
    '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
    '十': '10', '点': '.', '秒': '', '分': "'", '米': '', '个': '', '次': ''
  }
  let result = text
  for (const [cn, num] of Object.entries(map)) {
    result = result.replace(new RegExp(cn, 'g'), num)
  }
  return result.replace(/[^0-9.'\-]/g, '')
}
</script>

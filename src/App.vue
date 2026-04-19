<template>
  <div class="app">
    <div class="animated-bg"></div>
    <div class="animated-bg animated-bg-2"></div>

    <header class="header">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon">🎙️</div>
          <div class="logo-text">
            <h1>SpeechCloak</h1>
            <p class="subtitle">Анонимизация персональных данных в аудиозаписях</p>
          </div>
        </div>
        <div class="header-badge">
          <span class="badge">AI-Powered</span>
          <span class="badge-glow"></span>
        </div>
      </div>
    </header>

    <main class="main">
      <div class="left-panel">
        <div class="card glass-card neon-border">
          <div class="card-header">
            <span class="card-icon">📁</span>
            <span class="card-title">Загрузка аудио</span>
          </div>
          <div
            class="dropzone"
            @dragover.prevent
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
            :class="{ dragging: isDragging }"
          >
            <div class="dropzone-icon">🎵</div>
            <p class="dropzone-text">Перетащите аудиофайл сюда или</p>
            <label class="file-label">
              выберите на компьютере
              <input
                ref="fileInput"
                type="file"
                accept="audio/*"
                @change="handleFileSelect"
                hidden
              />
            </label>
            <p class="hint">MP3, WAV, FLAC до 100 МБ</p>
          </div>
        </div>

        <div class="card glass-card neon-border">
          <div class="card-header">
            <span class="card-icon">🔊</span>
            <span class="card-title">Аудиоплеер</span>
          </div>
          <div class="waveform-container">
            <div class="audio-mode-switcher">
              <button
                class="mode-btn"
                :class="{ active: audioMode === 'original' }"
                @click="switchAudioMode('original')"
                :disabled="!originalAudioUrl"
              >
                🎵 Оригинал
              </button>
              <button
                class="mode-btn"
                :class="{ active: audioMode === 'redacted' }"
                @click="switchAudioMode('redacted')"
                :disabled="!redactedAudioUrl"
              >
                🔒 Очищенный
              </button>
            </div>
            <div ref="waveformContainer" class="waveform-wrapper">
              <div v-if="!currentAudioUrl" class="empty-waveform">
                <div class="empty-icon">🎧</div>
                <p>Загрузите аудио для отображения</p>
              </div>
            </div>
            <div v-if="fileName" class="file-name-display">
              <span class="file-icon">📄</span>
              <span>{{ fileName }}</span>
              <span
                v-if="audioMode === 'redacted' && redactedAudioUrl"
                class="audio-mode-badge"
                >ОЧИЩЕННАЯ ВЕРСИЯ</span
              >
            </div>
            <div class="player-controls">
              <button
                class="play-btn"
                @click="togglePlay"
                :disabled="!currentAudioUrl"
              >
                <span class="play-icon">{{ isPlaying ? '⏸' : '▶' }}</span>
              </button>
              <span class="time-display"
                >{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span
              >
              <div class="progress-bar" @click="seekAudio">
                <div
                  class="progress-fill"
                  :style="{ width: progressPercent + '%' }"
                ></div>
                <div
                  class="progress-handle"
                  :style="{ left: progressPercent + '%' }"
                ></div>
              </div>
              <div class="volume-control">
                <span class="volume-icon">🔊</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  v-model="volume"
                  @input="setVolume"
                  class="volume-slider"
                />
              </div>
            </div>
          </div>
          <div class="action-buttons">
            <button
              class="btn btn-primary"
              :disabled="!originalAudioUrl"
              @click="downloadOriginal"
            >
              ⬇ Скачать оригинал
            </button>
            <button class="btn btn-warning" @click="clearAll">🧹 Очистить</button>
            <button
              class="btn btn-secondary"
              :disabled="!redactedAudioUrl"
              @click="downloadRedacted"
            >
              🔇 Скачать очищенное
            </button>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="card glass-card neon-border">
          <div class="card-header">
            <span class="card-icon">📝</span>
            <span class="card-title">Транскрипт</span>
          </div>
          <div class="transcript-tabs">
            <button
              class="tab"
              :class="{ active: transcriptMode === 'original' }"
              @click="transcriptMode = 'original'"
            >
              📄 Оригинал
            </button>
            <button
              class="tab"
              :class="{ active: transcriptMode === 'redacted' }"
              @click="transcriptMode = 'redacted'"
            >
              🔒 Очищенный
            </button>
          </div>
          <div class="transcript-text" v-if="transcriptMode === 'original'">
            <span
              v-for="(segment, idx) in transcriptSegments"
              :key="idx"
              :class="{ 'redacted-word': segment.isRedacted }"
              @click="segment.isRedacted && seekToTime(segment.start)"
            >
              {{ segment.text }}
            </span>
          </div>
          <div class="transcript-text" v-else>
            {{ redactedTranscript }}
          </div>
        </div>

        <div class="card glass-card neon-border">
          <div class="card-header">
            <span class="card-icon">📊</span>
            <span class="card-title">Отчёт по удалённым данным</span>
            <button
              class="btn-log-download"
              @click="downloadLogs"
              :disabled="events.length === 0"
              title="Скачать логи в JSON"
            >
              📄
            </button>
          </div>
          <div class="stats-grid">
            <div class="stat-item" v-for="stat in typeStats" :key="stat.type">
              <span class="stat-label">{{ stat.label }}</span>
              <span class="stat-value" :class="stat.color">{{ stat.count }}</span>
            </div>
          </div>
          <div v-if="events.length > 0" class="events-section">
            <h3 class="section-subtitle">
              ✂️ Вырезанные фрагменты
              <span class="events-count">{{ events.length }}</span>
            </h3>
            <div class="events-table">
              <div class="table-header">
                <span>Тип</span><span>Значение</span><span>Время</span><span></span>
              </div>
              <div class="table-body">
                <div class="table-row" v-for="(event, idx) in events" :key="idx">
                  <span class="event-type" :data-type="event.type">{{
                    getTypeLabel(event.type)
                  }}</span>
                  <span class="event-value">{{ event.value }}</span>
                  <span class="event-time"
                    >{{ formatTime(event.start) }} - {{ formatTime(event.end) }}</span
                  >
                  <button class="seek-btn" @click="seekToTime(event.start)">▶</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="footer">
      <div v-if="isProcessing" class="status processing">
        <div class="status-spinner"></div>
        <span>Обработка аудио... {{ processingStage }}</span>
      </div>
      <div v-else-if="resultReady" class="status done">
        <span class="status-icon">✅</span>
        <span>Обработка завершена. Найдено ПДн: {{ events.length }}</span>
      </div>
      <div v-else-if="errorMessage" class="status error">
        <span class="status-icon">❌</span>
        <span>Ошибка: {{ errorMessage }}</span>
      </div>
      <div v-else class="status idle">
        <span class="status-icon">⏳</span>
        <span>Ожидание загрузки файла</span>
      </div>
    </footer>

    <div class="floating-credit">
      <span class="credit-text">🌞 Теплокодеры 🌞</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js'
import { api } from './api/client'
import {
  transformPIISpansToEvents,
  buildTranscriptSegments,
} from './utils/transformers'
import type { RedactionEvent, TranscriptSegment } from './types'

const isDragging = ref(false)
const isProcessing = ref(false)
const resultReady = ref(false)
const errorMessage = ref('')
const processingStage = ref('')
const fileInput = ref<HTMLInputElement>()
const waveformContainer = ref<HTMLElement>()
const originalAudioBlob = ref<Blob | null>(null)
const originalAudioUrl = ref<string>('')
const redactedAudioUrl = ref<string>('')
const rawTranscript = ref('')
const redactedTranscript = ref('')
const events = ref<RedactionEvent[]>([])
const transcriptSegments = ref<TranscriptSegment[]>([])
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const fileName = ref<string>('')
const volume = ref(0.75)
const currentTaskId = ref<string>('')
let wavesurfer: WaveSurfer | null = null
let regionsPlugin: any = null
const transcriptMode = ref<'original' | 'redacted'>('original')
const audioMode = ref<'original' | 'redacted'>('original')

const currentAudioUrl = computed(() => {
  return audioMode.value === 'original' ? originalAudioUrl.value : redactedAudioUrl.value
})

// Вспомогательная функция для получения цвета по типу PII
const getColorForType = (type: string): string => {
  const colors: Record<string, string> = {
    PHONE: '#ff6b6b',
    PASSPORT: '#ff6b6b',
    INN: '#ffa502',
    SNILS: '#ffa502',
    EMAIL: '#70a1ff',
    ADDRESS: '#7bed9f',
    PERSON: '#a29bfe',
  }
  return colors[type] || '#667eea'
}

// Функция добавления регионов на волновую форму
const addRedactionRegions = () => {
  if (!wavesurfer || !regionsPlugin) return
  
  // Очищаем предыдущие регионы
  regionsPlugin.clearRegions()
  
  // Если нет событий или режим не оригинал — выходим
  if (events.value.length === 0 || audioMode.value !== 'original') return
  
  // Добавляем регионы для каждого события
  events.value.forEach(event => {
    try {
      regionsPlugin.addRegion({
        start: event.start,
        end: event.end,
        color: getColorForType(event.type) + '40', // 40 = 25% прозрачности в hex
        drag: false,
        resize: false,
        id: `pii-${event.type}-${event.start}`
      })
    } catch (e) {
      console.warn('Failed to add region:', e)
    }
  })
}

onMounted(() => {
  if (!waveformContainer.value) return
  
  // Создаем плагин регионов
  regionsPlugin = RegionsPlugin.create()
  
  wavesurfer = WaveSurfer.create({
    container: waveformContainer.value,
    waveColor: '#c0c0c0',
    progressColor: '#667eea',
    cursorColor: '#764ba2',
    barWidth: 2,
    height: 100,
    normalize: true,
    barRadius: 3,
    plugins: [regionsPlugin]
  })
  
  wavesurfer.setVolume(volume.value)
  
  wavesurfer.on('ready', () => {
    duration.value = wavesurfer!.getDuration()
    // Добавляем регионы после загрузки аудио
    addRedactionRegions()
  })
  
  wavesurfer.on('audioprocess', () => {
    currentTime.value = wavesurfer!.getCurrentTime()
  })
  wavesurfer.on('play', () => {
    isPlaying.value = true
  })
  wavesurfer.on('pause', () => {
    isPlaying.value = false
  })
  wavesurfer.on('finish', () => {
    isPlaying.value = false
  })
})

onBeforeUnmount(() => {
  if (originalAudioUrl.value) URL.revokeObjectURL(originalAudioUrl.value)
  if (redactedAudioUrl.value) URL.revokeObjectURL(redactedAudioUrl.value)
  wavesurfer?.destroy()
})

watch(currentAudioUrl, async (newUrl) => {
  if (newUrl && wavesurfer) {
    await wavesurfer.load(newUrl)
  }
})

const progressPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const typeStats = computed(() => {
  const counts: Record<string, number> = {}
  events.value.forEach((e) => {
    counts[e.type] = (counts[e.type] || 0) + 1
  })
  return [
    { type: 'PHONE', label: '📞 Телефоны', count: counts.PHONE || 0, color: 'red' },
    {
      type: 'PASSPORT',
      label: '📄 Паспорт',
      count: counts.PASSPORT || 0,
      color: 'red',
    },
    { type: 'INN', label: '🔢 ИНН', count: counts.INN || 0, color: 'orange' },
    { type: 'SNILS', label: '🔢 СНИЛС', count: counts.SNILS || 0, color: 'orange' },
    { type: 'EMAIL', label: '📧 Email', count: counts.EMAIL || 0, color: 'blue' },
    {
      type: 'ADDRESS',
      label: '🏠 Адреса',
      count: counts.ADDRESS || 0,
      color: 'green',
    },
    {
      type: 'PERSON',
      label: '👤 ФИО',
      count: counts.PERSON || 0,
      color: 'purple',
    },
  ]
})

const triggerFileInput = () => fileInput.value?.click()

const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file?.type.startsWith('audio/')) processFile(file)
}

const handleFileSelect = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) processFile(file)
}

const processFile = async (file: File) => {
  clearAll()

  isProcessing.value = true
  resultReady.value = false
  errorMessage.value = ''
  fileName.value = file.name

  // Сохраняем оригинальный файл
  originalAudioBlob.value = file
  originalAudioUrl.value = URL.createObjectURL(file)
  audioMode.value = 'original'

  try {
    processingStage.value = 'Загрузка файла...'

    // 1. Отправляем файл на сервер
    const uploadResponse = await api.uploadAudio(file)
    currentTaskId.value = uploadResponse.task_id

    processingStage.value = 'Файл загружен, идёт обработка...'

    // 2. Полинг статуса задачи
    const finalStatus = await api.pollTaskStatus(
      currentTaskId.value,
      (status) => {
        // Обновляем этап обработки на основе логов
        if (status.logs && status.logs.length > 0) {
          const lastLog = status.logs[status.logs.length - 1]
          if (lastLog) {
            processingStage.value = `${lastLog.stage}: ${lastLog.message}`
          }
        }
      },
      1000,
      300 // 5 минут максимум
    )

    // 3. Обрабатываем результат
    if (finalStatus.status === 'error') {
      throw new Error(finalStatus.error_message || 'Ошибка обработки')
    }

    // 4. Получаем URL для очищенного аудио
    redactedAudioUrl.value = api.getResultFileUrl(currentTaskId.value)

    // 5. Заполняем данные транскрипта и событий
    rawTranscript.value = finalStatus.transcript || ''
    redactedTranscript.value = finalStatus.redacted_text || ''
    events.value = transformPIISpansToEvents(finalStatus.pii_spans)
    transcriptSegments.value = buildTranscriptSegments(
      rawTranscript.value,
      events.value
    )

    processingStage.value = ''
    isProcessing.value = false
    resultReady.value = true
    
    // Добавляем регионы после загрузки данных
    setTimeout(() => addRedactionRegions(), 100)
  } catch (error) {
    isProcessing.value = false
    errorMessage.value = error instanceof Error ? error.message : 'Неизвестная ошибка'
    console.error('Processing error:', error)
  }
}

const switchAudioMode = (mode: 'original' | 'redacted') => {
  if (mode === 'original' && !originalAudioUrl.value) return
  if (mode === 'redacted' && !redactedAudioUrl.value) return

  const wasPlaying = isPlaying.value
  const currentPosition = currentTime.value

  audioMode.value = mode

  setTimeout(() => {
    if (wavesurfer && currentPosition > 0) {
      const dur = wavesurfer.getDuration()
      if (dur > 0) {
        const seekPos = Math.min(currentPosition / dur, 1)
        wavesurfer.seekTo(seekPos)
        if (wasPlaying) {
          wavesurfer.play()
        }
      }
    }
    
    // Обновляем регионы при переключении режима
    if (mode === 'original') {
      addRedactionRegions()
    } else {
      regionsPlugin?.clearRegions()
    }
  }, 100)
}

const togglePlay = () => {
  if (!currentAudioUrl.value) return
  wavesurfer?.playPause()
}

const seekAudio = (e: MouseEvent) => {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  wavesurfer?.seekTo(percent)
}

const seekToTime = (time: number) => {
  if (!wavesurfer) return
  const dur = wavesurfer.getDuration()
  if (dur > 0) wavesurfer.seekTo(time / dur)
}

const setVolume = () => {
  wavesurfer?.setVolume(volume.value)
}

const downloadOriginal = () => {
  if (originalAudioBlob.value) {
    const url = URL.createObjectURL(originalAudioBlob.value)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName.value || 'original_audio.wav'
    a.click()
    URL.revokeObjectURL(url)
  }
}

const downloadRedacted = () => {
  if (redactedAudioUrl.value) {
    const a = document.createElement('a')
    a.href = redactedAudioUrl.value
    a.download = `redacted_${fileName.value || 'audio.wav'}`
    a.click()
  }
}

const downloadLogs = async () => {
  if (!currentTaskId.value) return

  try {
    const logs = await api.getTaskLogs(currentTaskId.value)
    const logData = {
      taskId: currentTaskId.value,
      generated: new Date().toISOString(),
      fileName: fileName.value,
      totalEvents: events.value.length,
      events: events.value,
      serverLogs: logs,
    }
    const blob = new Blob([JSON.stringify(logData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `redaction_log_${currentTaskId.value}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download logs:', error)
  }
}

const clearAll = () => {
  wavesurfer?.stop()
  wavesurfer?.empty()
  regionsPlugin?.clearRegions()

  if (originalAudioUrl.value) {
    URL.revokeObjectURL(originalAudioUrl.value)
    originalAudioUrl.value = ''
  }
  if (redactedAudioUrl.value) {
    URL.revokeObjectURL(redactedAudioUrl.value)
    redactedAudioUrl.value = ''
  }

  originalAudioBlob.value = null
  fileName.value = ''
  rawTranscript.value = ''
  redactedTranscript.value = ''
  events.value = []
  transcriptSegments.value = []
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0
  volume.value = 0.75
  resultReady.value = false
  isProcessing.value = false
  errorMessage.value = ''
  processingStage.value = ''
  currentTaskId.value = ''
  audioMode.value = 'original'

  if (fileInput.value) fileInput.value.value = ''

  transcriptMode.value = 'original'
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    PHONE: '📞 Телефон',
    PASSPORT: '📄 Паспорт',
    INN: '🔢 ИНН',
    SNILS: '🔢 СНИЛС',
    EMAIL: '📧 Email',
    ADDRESS: '🏠 Адрес',
    PERSON: '👤 ФИО',
  }
  return labels[type] || type
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  min-height: 100vh;
  background: #0f0c29;
  overflow-x: hidden;
}

#app {
  width: 100%;
  min-height: 100vh;
  background: #0f0c29;
}
</style>

<style scoped>
.status.error {
  color: #ff6b6b;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  font-family: 'Segoe UI', 'Poppins', Tahoma, Geneva, Verdana, sans-serif;
  position: relative;
  overflow-x: hidden;
}

.animated-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.15) 0%, transparent 50%);
  animation: float 20s ease-in-out infinite;
  pointer-events: none;
  z-index: 0;
}

.animated-bg-2 {
  background: radial-gradient(circle at 80% 30%, rgba(118, 75, 162, 0.15) 0%, transparent 50%);
  animation: float 15s ease-in-out infinite reverse;
}

@keyframes float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.5;
  }
  50% {
    transform: translate(5%, 5%) scale(1.1);
    opacity: 0.8;
  }
}

.header {
  background: rgba(10, 10, 20, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(102, 126, 234, 0.3);
  padding: 20px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
}
.logo-icon {
  font-size: 40px;
  animation: pulse 2s infinite;
  filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5));
}

.logo-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.header-badge {
  position: relative;
}
.badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 18px;
  border-radius: 30px;
  font-size: 13px;
  font-weight: 700;
  position: relative;
  z-index: 2;
  box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
}

.badge-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
  border-radius: 32px;
  filter: blur(8px);
  opacity: 0.6;
  z-index: 1;
  animation: glowPulse 2s infinite;
}

@keyframes glowPulse {
  0%,
  100% {
    opacity: 0.4;
    filter: blur(6px);
  }
  50% {
    opacity: 0.8;
    filter: blur(12px);
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 32px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
  position: relative;
  z-index: 1;
}

.glass-card {
  background: rgba(15, 15, 30, 0.6);
  border-radius: 28px;
  padding: 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.neon-border {
  position: relative;
}
.neon-border::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, #667eea, #764ba2, #f093fb, #667eea);
  border-radius: 30px;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.neon-border:hover::before {
  opacity: 1;
  animation: borderRotate 3s linear infinite;
}

@keyframes borderRotate {
  0% {
    background: linear-gradient(0deg, #667eea, #764ba2, #f093fb);
  }
  100% {
    background: linear-gradient(360deg, #667eea, #764ba2, #f093fb);
  }
}

.glass-card:hover {
  transform: translateY(-8px) scale(1.01);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 30px rgba(102, 126, 234, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.3);
}

.card-icon {
  font-size: 28px;
  filter: drop-shadow(0 0 5px rgba(102, 126, 234, 0.5));
}

.card-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #fff, #ddd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  flex: 1;
}

.dropzone {
  border: 2px solid rgba(102, 126, 234, 0.4);
  border-radius: 24px;
  padding: 48px 24px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background: rgba(102, 126, 234, 0.05);
}

.dropzone:hover,
.dropzone.dragging {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.15);
  transform: scale(1.02);
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
}

.dropzone-icon {
  font-size: 72px;
  margin-bottom: 16px;
  animation: bounce 2s infinite;
  filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5));
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.dropzone-text {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 12px;
}
.file-label {
  color: #a4b3ff;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  border-bottom: 2px solid #667eea;
  transition: all 0.2s;
}

.file-label:hover {
  color: #ffffff;
  border-bottom-color: #ffffff;
  letter-spacing: 0.5px;
}

.hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 12px;
}

.audio-mode-switcher {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  background: rgba(0, 0, 0, 0.2);
  padding: 6px;
  border-radius: 16px;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.mode-btn {
  flex: 1;
  padding: 10px 16px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  position: relative;
  overflow: hidden;
}

.mode-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s;
}

.mode-btn:hover:not(:disabled)::before {
  left: 100%;
}

.mode-btn:hover:not(:disabled) {
  background: rgba(102, 126, 234, 0.2);
  color: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.mode-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.4);
}

.mode-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.audio-mode-badge {
  margin-left: 12px;
  padding: 2px 10px;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  border-radius: 20px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.waveform-wrapper {
  width: 100%;
  height: 100px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.empty-waveform {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.6);
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
  opacity: 0.7;
}

.file-name-display {
  margin-top: 12px;
  padding: 8px 16px;
  background: rgba(102, 126, 234, 0.15);
  border-radius: 12px;
  font-size: 13px;
  color: #a4b3ff;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.play-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
}

.play-btn:hover:not(:disabled) {
  transform: scale(1.1);
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
}

.play-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.play-icon {
  font-size: 22px;
}
.time-display {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-family: monospace;
  font-weight: 500;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  cursor: pointer;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  transition: width 0.1s linear;
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
}

.progress-handle {
  width: 14px;
  height: 14px;
  background: white;
  border: 2px solid #667eea;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.8);
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 8px;
}
.volume-icon {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
}
.volume-slider {
  width: 80px;
  height: 4px;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
.btn {
  flex: 1;
  padding: 12px 20px;
  border-radius: 16px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.btn:hover::before {
  left: 100%;
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.btn-warning {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.4);
}

.btn-warning:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 152, 0, 0.6);
}

.transcript-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.tab {
  flex: 1;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 14px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tab:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.4);
}

.transcript-text {
  line-height: 1.8;
  max-height: 250px;
  overflow-y: auto;
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.redacted-word {
  background: linear-gradient(135deg, rgba(255, 235, 59, 0.4) 0%, rgba(255, 193, 7, 0.4) 100%);
  padding: 2px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  color: white;
  border: 1px solid rgba(255, 235, 59, 0.6);
}

.redacted-word:hover {
  transform: scale(1.03);
  background: rgba(255, 193, 7, 0.6);
  box-shadow: 0 0 15px rgba(255, 193, 7, 0.4);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  transition: all 0.3s ease;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.stat-item:hover {
  transform: translateY(-2px);
  background: rgba(102, 126, 234, 0.2);
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
}

.stat-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  font-weight: 500;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  filter: drop-shadow(0 0 10px currentColor);
}
.stat-value.red {
  color: #ff6b6b;
}
.stat-value.orange {
  color: #ffa502;
}
.stat-value.blue {
  color: #70a1ff;
}
.stat-value.green {
  color: #7bed9f;
}

.events-section {
  margin-top: 8px;
}
.section-subtitle {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  gap: 8px;
}

.events-count {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
}

.events-table {
  max-height: 250px;
  overflow-y: auto;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.table-header {
  display: grid;
  grid-template-columns: 100px 1fr 130px 40px;
  padding: 12px 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
  background: rgba(102, 126, 234, 0.15);
  border-radius: 12px;
  margin-bottom: 4px;
}

.table-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.table-row {
  display: grid;
  grid-template-columns: 100px 1fr 130px 40px;
  padding: 10px 16px;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  align-items: center;
  transition: all 0.2s;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.table-row:hover {
  background: rgba(102, 126, 234, 0.15);
  transform: translateX(4px);
}

.event-type {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  display: inline-block;
  width: fit-content;
}

.event-type[data-type='PHONE'],
.event-type[data-type='PASSPORT'] {
  background: rgba(255, 107, 107, 0.3);
  color: #ffb3b3;
}
.event-type[data-type='INN'],
.event-type[data-type='SNILS'] {
  background: rgba(255, 165, 2, 0.3);
  color: #ffd280;
}
.event-type[data-type='EMAIL'] {
  background: rgba(112, 161, 255, 0.3);
  color: #b3d0ff;
}
.event-type[data-type='ADDRESS'] {
  background: rgba(123, 237, 159, 0.3);
  color: #c6ffd3;
}

.event-value {
  color: rgba(255, 255, 255, 0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-time {
  color: rgba(255, 255, 255, 0.6);
  font-family: monospace;
  font-size: 11px;
}

.seek-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s;
}

.seek-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
}

.btn-log-download {
  background: rgba(102, 126, 234, 0.2);
  border: none;
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
}

.btn-log-download:hover:not(:disabled) {
  background: rgba(102, 126, 234, 0.4);
  transform: scale(1.05);
}

.btn-log-download:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.footer {
  margin-top: auto;
  padding: 16px 32px;
  background: rgba(10, 10, 20, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(102, 126, 234, 0.3);
}

.status {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  max-width: 1600px;
  margin: 0 auto;
  color: rgba(255, 255, 255, 0.9);
}

.status-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.status-icon {
  font-size: 18px;
}
.status.processing {
  color: #667eea;
}
.status.done {
  color: #7bed9f;
}
.status.idle {
  color: rgba(255, 255, 255, 0.7);
}
.status.error {
  color: #ff6b6b;
}

.floating-credit {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}
.credit-text {
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 8px 16px;
  border-radius: 40px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 1px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  display: inline-block;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.credit-text:hover {
  transform: scale(1.05);
  background: rgba(0, 0, 0, 0.85);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .main {
    grid-template-columns: 1fr;
    padding: 20px;
    gap: 16px;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .table-header,
  .table-row {
    grid-template-columns: 80px 1fr 100px 40px;
  }
  .player-controls {
    flex-wrap: wrap;
  }
  .volume-control {
    margin-left: auto;
  }
  .action-buttons {
    flex-direction: column;
  }
  .btn {
    width: 100%;
  }
  .floating-credit {
    bottom: 10px;
    right: 10px;
  }
  .credit-text {
    font-size: 10px;
    padding: 5px 12px;
  }
  .audio-mode-switcher {
    flex-direction: column;
  }
}
</style>
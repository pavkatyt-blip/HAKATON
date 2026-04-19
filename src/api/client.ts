// src/api/client.ts

// Определяем базовый URL для API
const getApiBase = (): string => {
  // Приоритет: переменная окружения Vite
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // Локальная разработка — Go бэкенд
  return 'http://localhost:8080'  
}

const API_BASE = getApiBase()

// Для отладки — выводим в консоль при разработке
if (import.meta.env.DEV) {
  console.log('🌐 API Base URL:', API_BASE)
}

export interface TaskStatusResponse {
  task_id: string
  status: 'processing' | 'done' | 'error'
  error_message?: string
  file_url?: string
  logs?: Array<{
    time: string
    level: string
    stage: string
    message: string
  }>
  transcript?: string
  redacted_text?: string
  pii_spans?: Array<{
    type: string
    start_time: number
    end_time: number
    text: string
    replacement: string
  }>
  stats: {
    phones: number
    passports: number
    inn: number
    snils: number
    emails: number
    addresses: number
    persons: number
  }
}

export interface TaskCreatedResponse {
  task_id: string
  status: string
}

export const api = {
  async uploadAudio(file: File): Promise<TaskCreatedResponse> {
    const formData = new FormData()
    formData.append('audio', file)  // ← Go ждёт поле 'audio'

    const url = `${API_BASE}/anonymize`
    console.log('📤 Uploading to:', url)  // ← отладка

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  },

  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await fetch(`${API_BASE}/tasks/${taskId}`)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to get task status' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  },

  getResultFileUrl(taskId: string): string {
    return `${API_BASE}/files/${taskId}`
  },

  async getTaskLogs(taskId: string): Promise<Array<{
    time: string
    level: string
    stage: string
    message: string
  }>> {
    const response = await fetch(`${API_BASE}/tasks/${taskId}/logs`)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to get task logs' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  },

  async pollTaskStatus(
    taskId: string,
    onProgress?: (status: TaskStatusResponse) => void,
    interval = 1000,
    maxAttempts = 300
  ): Promise<TaskStatusResponse> {
    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getTaskStatus(taskId)
      onProgress?.(status)

      if (status.status === 'done' || status.status === 'error') {
        return status
      }

      await new Promise(resolve => setTimeout(resolve, interval))
    }

    throw new Error('Task processing timeout')
  },
}
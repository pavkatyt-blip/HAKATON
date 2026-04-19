// src/utils/transformers.ts
import type { TaskStatusResponse } from '../api/client'
import type { RedactionEvent, TranscriptSegment } from '../types'

// Преобразование PII-спанов из ответа API в события
export function transformPIISpansToEvents(
  piiSpans: TaskStatusResponse['pii_spans']
): RedactionEvent[] {
  if (!piiSpans) return []

  return piiSpans.map((span) => ({
    type: span.type as RedactionEvent['type'],
    value: span.text,
    start: span.start_time,
    end: span.end_time,
  }))
}

// Построение сегментов транскрипта с разметкой
export function buildTranscriptSegments(
  transcript: string,
  events: RedactionEvent[]
): TranscriptSegment[] {
  if (!transcript) return []

  // Сортируем события по времени начала
  const sortedEvents = [...events].sort((a, b) => a.start - b.start)

  const segments: TranscriptSegment[] = []
  let lastEnd = 0

  // Упрощённый подход — делим текст по событиям
  // В реальности лучше использовать позиции символов, но для MVP подойдёт
  const words = transcript.split(/(\s+)/)

  for (const word of words) {
    if (!word.trim()) {
      segments.push({
        text: word,
        start: lastEnd,
        end: lastEnd,
        isRedacted: false,
      })
      continue
    }

    // Проверяем, содержится ли слово в каком-либо событии
    const matchingEvent = sortedEvents.find(
      (e) => e.value.toLowerCase().includes(word.toLowerCase().replace(/[.,!?;:]/g, ''))
    )

    segments.push({
      text: word,
      start: matchingEvent?.start || lastEnd,
      end: matchingEvent?.end || lastEnd,
      isRedacted: !!matchingEvent,
    })

    if (!matchingEvent) {
      lastEnd = lastEnd
    }
  }

  return segments
}

// Форматирование статистики
export function formatStats(stats: TaskStatusResponse['stats']) {
  return {
    phones: stats?.phones || 0,
    passports: stats?.passports || 0,
    inn: stats?.inn || 0,
    snils: stats?.snils || 0,
    emails: stats?.emails || 0,
    addresses: stats?.addresses || 0,
    persons: stats?.persons || 0,
  }
}
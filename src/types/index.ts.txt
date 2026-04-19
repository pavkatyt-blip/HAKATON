// src/types/index.ts
export interface RedactionEvent {
  type: 'PHONE' | 'PASSPORT' | 'INN' | 'SNILS' | 'EMAIL' | 'ADDRESS' | 'PERSON'
  value: string
  start: number
  end: number
}

export interface TranscriptSegment {
  text: string
  start: number
  end: number
  isRedacted: boolean
}
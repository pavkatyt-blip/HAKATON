package task

import (
	"sync"
)

type PIISpan struct {
	Type        string  `json:"type"`
	StartTime   float64 `json:"start_time"`
	EndTime     float64 `json:"end_time"`
	Text        string  `json:"text"`
	Replacement string  `json:"replacement"`
}

type Task struct {
	ID             string
	Status         string
	ResultFilePath string
	ErrorMessage   string
	Logs           []Log

	Transcript   string
	RedactedText string
	PIISpans     []PIISpan
	Stats        PIIStats
}

type TaskStore struct {
	mu    sync.RWMutex
	tasks map[string]*Task
}

func NewTaskStore() *TaskStore {
	return &TaskStore{
		tasks: make(map[string]*Task),
	}
}

func (s *TaskStore) Create(task *Task) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.tasks[task.ID] = task
}

func (s *TaskStore) Get(id string) (*Task, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	task, ok := s.tasks[id]
	return task, ok
}

func (s *TaskStore) SetResult(id, resultFilePath string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	task, ok := s.tasks[id]
	if !ok {
		return
	}
	task.Status = "done"
	task.ResultFilePath = resultFilePath
}

func (s *TaskStore) SetResultData(
	id,
	resultFilePath,
	transcript,
	redactedText string,
	piiSpans []PIISpan,
) {
	s.mu.Lock()
	defer s.mu.Unlock()

	task, ok := s.tasks[id]
	if !ok {
		return
	}

	task.Status = "done"
	task.ResultFilePath = resultFilePath
	task.Transcript = transcript
	task.RedactedText = redactedText
	task.PIISpans = piiSpans
	task.Stats = BuildPIIStats(piiSpans)
}

func (s *TaskStore) StatusError(id, errorMessage string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	task, ok := s.tasks[id]
	if !ok {
		return
	}
	task.Status = "error"
	task.ErrorMessage = errorMessage
}

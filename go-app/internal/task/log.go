package task

import (
	"time"
)

type Log struct {
	Time    string `json:"time"`
	Level   string `json:"level"`
	Stage   string `json:"stage"`
	Message string `json:"message"`
}

func (s *TaskStore) AddLog(taskID, level, stage, message string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	task, ok := s.tasks[taskID]
	if !ok {
		return
	}

	task.Logs = append(task.Logs, Log{
		Time:    time.Now().Format(time.RFC3339),
		Level:   level,
		Stage:   stage,
		Message: message,
	})
}

func (s *TaskStore) AddExternalLog(taskID, rawTime, level, stage, message string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	task, ok := s.tasks[taskID]
	if !ok {
		return
	}

	task.Logs = append(task.Logs, Log{
		Time:    rawTime,
		Level:   level,
		Stage:   stage,
		Message: message,
	})
}

func (s *TaskStore) GetLogs(taskID string) ([]Log, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	task, ok := s.tasks[taskID]
	if !ok {
		return nil, false
	}

	return task.Logs, true
}

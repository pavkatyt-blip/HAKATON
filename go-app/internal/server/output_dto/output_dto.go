package output_dto

import "anonymization_of_voice_messages/internal/task"

type TaskStatusDTO struct {
	ID     string `json:"task_id"`
	Status string `json:"status"`
}

func NewTaskStatusDTO(taskID, status string) TaskStatusDTO {
	return TaskStatusDTO{
		ID:     taskID,
		Status: status,
	}
}

type TaskDTO struct {
	ID           string     `json:"task_id"`
	Status       string     `json:"status"`
	ErrorMessage string     `json:"error_message,omitempty"`
	FileURL      string     `json:"file_url,omitempty"`
	Logs         []task.Log `json:"logs,omitempty"`

	Transcript   string         `json:"transcript,omitempty"`
	RedactedText string         `json:"redacted_text,omitempty"`
	PIISpans     []task.PIISpan `json:"pii_spans,omitempty"`
	Stats        task.PIIStats  `json:"stats"`
}

func NewTaskDTO(taskObj *task.Task) TaskDTO {
	fileURL := ""
	if taskObj.Status == "done" {
		fileURL = "/files/" + taskObj.ID
	}

	return TaskDTO{
		ID:           taskObj.ID,
		Status:       taskObj.Status,
		ErrorMessage: taskObj.ErrorMessage,
		FileURL:      fileURL,
		Logs:         taskObj.Logs,
		Transcript:   taskObj.Transcript,
		RedactedText: taskObj.RedactedText,
		PIISpans:     taskObj.PIISpans,
		Stats:        taskObj.Stats,
	}
}

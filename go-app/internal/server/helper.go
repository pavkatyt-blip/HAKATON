package server

import (
	"anonymization_of_voice_messages/internal/file"
	"anonymization_of_voice_messages/internal/python_client"
	"anonymization_of_voice_messages/internal/task"
	"os"

	"go.uber.org/zap"
)

func (h *HTTPHandlers) logTaskInfo(taskID, stage, message string, fields ...zap.Field) {
	h.Logger.Info(message, append([]zap.Field{
		zap.String("task_id", taskID),
		zap.String("stage", stage),
	}, fields...)...)

	h.TaskStore.AddLog(taskID, "info", stage, message)
}

func (h *HTTPHandlers) logTaskError(taskID, stage, message string, err error, fields ...zap.Field) {
	allFields := append([]zap.Field{
		zap.String("task_id", taskID),
		zap.String("stage", stage),
		zap.Error(err),
	}, fields...)

	h.Logger.Error(message, allFields...)
	h.TaskStore.AddLog(taskID, "error", stage, message+": "+err.Error())
}

func (h *HTTPHandlers) processTask(taskID, tmpFile string) {
	defer os.Remove(tmpFile)

	h.logTaskInfo(taskID, "convert", "wav conversion started")

	wavPath, err := file.ConvertToWav(tmpFile)
	if err != nil {
		h.TaskStore.StatusError(taskID, err.Error())
		h.logTaskError(taskID, "convert", "wav conversion failed", err)
		return
	}
	h.logTaskInfo(taskID, "convert", "wav conversion completed", zap.String("wav_path", wavPath))

	defer os.Remove(wavPath)

	h.logTaskInfo(taskID, "python", "sending file to python")
	result, err := python_client.SendFileToPython(taskID, wavPath)
	if err != nil {
		h.TaskStore.StatusError(taskID, err.Error())
		h.logTaskError(taskID, "python", "python processing failed", err)
		return
	}

	h.logTaskInfo(
		taskID,
		"python",
		"python processing completed",
		zap.String("result_file", result.ResultWavPath),
		zap.String("result_json", result.ResultJSONPath),
	)

	piiSpans := make([]task.PIISpan, 0, len(result.Meta.PIISpans))
	for _, span := range result.Meta.PIISpans {
		piiSpans = append(piiSpans, task.PIISpan{
			Type:        span.Type,
			StartTime:   span.StartTime,
			EndTime:     span.EndTime,
			Text:        span.Text,
			Replacement: span.Replacement,
		})
	}

	h.TaskStore.SetResultData(
		taskID,
		result.ResultWavPath,
		result.Meta.Transcript,
		result.Meta.RedactedText,
		piiSpans,
	)

	for _, l := range result.Meta.Logs {
		level := l.Level
		if level == "" {
			level = "info"
		}
		stage := l.Stage
		if stage == "" {
			stage = "python"
		}
		message := l.Message
		if message == "" {
			message = "python stage completed"
		}

		h.TaskStore.AddExternalLog(
			taskID,
			l.Time,
			level,
			stage,
			message,
		)
	}

	h.logTaskInfo(taskID, "result", "task completed", zap.String("result_file", result.ResultWavPath))
}

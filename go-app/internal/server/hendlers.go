package server

import (
	self_error "anonymization_of_voice_messages/internal/errors"
	"anonymization_of_voice_messages/internal/file"
	"anonymization_of_voice_messages/internal/server/output_dto"
	"anonymization_of_voice_messages/internal/task"
	"encoding/json"
	"errors"
	"net/http"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
	"go.uber.org/zap"
)

type HTTPHandlers struct {
	TaskStore *task.TaskStore
	Logger    *zap.Logger
}

func NewHTTPHandlers(taskStore *task.TaskStore, logger *zap.Logger) *HTTPHandlers {
	return &HTTPHandlers{
		TaskStore: taskStore,
		Logger:    logger,
	}
}

func (h *HTTPHandlers) UploadAudio(w http.ResponseWriter, r *http.Request) {
	taskID := uuid.NewString()

	h.TaskStore.Create(&task.Task{
		ID:     taskID,
		Status: "processing",
	})
	h.logTaskInfo(taskID, "task", "task created")

	tmpFile, err := file.SaveFile(r)
	if err != nil {
		h.TaskStore.StatusError(taskID, err.Error())
		h.logTaskError(taskID, "upload", "failed to save uploaded file", err)

		errDTO := NewErrorDTO(err.Error())

		if errors.Is(err, self_error.ErrInvalidMultipartForm) || errors.Is(err, self_error.ErrFileRequired) {
			http.Error(w, errDTO.ToString(), http.StatusBadRequest)
		} else {
			http.Error(w, errDTO.ToString(), http.StatusInternalServerError)
		}
		return
	}

	h.logTaskInfo(taskID, "upload", "file uploaded", zap.String("path", tmpFile))

	taskStatusDTO := output_dto.NewTaskStatusDTO(taskID, "processing")
	b, err := json.MarshalIndent(taskStatusDTO, "", "  ")
	if err != nil {
		h.logTaskError(taskID, "response", "failed to encode task status dto", err)
		http.Error(w, NewErrorDTO(self_error.ErrEncodeTask.Error()).ToString(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	if _, err = w.Write(b); err != nil {
		h.logTaskError(taskID, "response", "failed to write accepted response", err)
		return
	}

	go h.processTask(taskID, tmpFile)
}

func (h *HTTPHandlers) GetTaskStatus(w http.ResponseWriter, r *http.Request) {
	taskID := mux.Vars(r)["id"]

	taskObj, ok := h.TaskStore.Get(taskID)
	if !ok {
		http.Error(w, NewErrorDTO(self_error.ErrTaskNotFound.Error()).ToString(), http.StatusNotFound)
		return
	}

	taskDTO := output_dto.NewTaskDTO(taskObj)

	b, err := json.MarshalIndent(taskDTO, "", "  ")
	if err != nil {
		h.logTaskError(taskID, "response", "failed to encode task dto", err)
		http.Error(w, NewErrorDTO(self_error.ErrEncodeTask.Error()).ToString(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if _, err := w.Write(b); err != nil {
		h.logTaskError(taskID, "response", "failed to write task status response", err)
	}
}

func (h *HTTPHandlers) GetResultFile(w http.ResponseWriter, r *http.Request) {
	taskID := mux.Vars(r)["id"]

	taskObj, ok := h.TaskStore.Get(taskID)
	if !ok {
		http.Error(w, NewErrorDTO(self_error.ErrTaskNotFound.Error()).ToString(), http.StatusNotFound)
		return
	}

	if taskObj.Status == "error" {
		http.Error(w, NewErrorDTO(taskObj.ErrorMessage).ToString(), http.StatusInternalServerError)
		return
	}

	if taskObj.Status != "done" {
		http.Error(w, NewErrorDTO(self_error.ErrFileNotReady.Error()).ToString(), http.StatusAccepted)
		return
	}

	if taskObj.ResultFilePath == "" {
		http.Error(w, NewErrorDTO(self_error.ErrResultPath.Error()).ToString(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "audio/wav")
	w.Header().Set("Content-Disposition", `attachment; filename="`+taskObj.ID+`.wav"`)

	http.ServeFile(w, r, taskObj.ResultFilePath)
}

func (h *HTTPHandlers) GetTaskLog(w http.ResponseWriter, r *http.Request) {
	taskID := mux.Vars(r)["id"]

	logs, ok := h.TaskStore.GetLogs(taskID)
	if !ok {
		http.Error(w, NewErrorDTO(self_error.ErrTaskNotFound.Error()).ToString(), http.StatusNotFound)
		return
	}

	b, err := json.MarshalIndent(logs, "", "  ")
	if err != nil {
		h.logTaskError(taskID, "response", "failed to encode task logs", err)
		http.Error(w, NewErrorDTO(self_error.ErrEncodeTask.Error()).ToString(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if _, err := w.Write(b); err != nil {
		h.logTaskError(taskID, "response", "failed to write task logs response", err)
	}
}

func (h *HTTPHandlers) Health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if _, err := w.Write([]byte(`{"status":"ok"}`)); err != nil {
		h.Logger.Error("failed to write health response", zap.Error(err))
	}
}

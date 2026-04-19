package self_error

import "errors"

var (
	ErrInvalidMultipartForm = errors.New("invalid multipart form")
	ErrFileRequired         = errors.New("file is required")
	ErrCreateTempFile       = errors.New("failed to create temp file")
	ErrSaveFile             = errors.New("failed to save file")
	ErrTaskNotFound         = errors.New("task not found")
	ErrEncodeTask           = errors.New("failed to encode task")
	ErrWriteTask            = errors.New("failed to write task status response:")
	ErrFileNotReady         = errors.New("file is not ready yet")
	ErrResultPath           = errors.New("result file path is empty")
	ErrInternalStatus       = errors.New("internal error")
)

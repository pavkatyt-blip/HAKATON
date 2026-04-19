package server

import (
	"encoding/json"
	"time"
)

type ErrorDTO struct {
	Message string    `json:"message"`
	Time    time.Time `json:"time"`
}

func NewErrorDTO(message string) ErrorDTO {
	return ErrorDTO{
		Message: message,
		Time:    time.Now(),
	}
}

func (e ErrorDTO) ToString() string {
	b, err := json.MarshalIndent(e, "", "	")
	if err != nil {
		return `{"message":"internal error"}`
	}

	return string(b)
}

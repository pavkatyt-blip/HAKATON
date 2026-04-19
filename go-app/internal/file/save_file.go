package file

import (
	self_error "anonymization_of_voice_messages/internal/errors"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
)

func SaveFile(r *http.Request) (string, error) {
	err := r.ParseMultipartForm(32 << 20)
	if err != nil {
		return "", self_error.ErrInvalidMultipartForm
	}

	file, header, err := r.FormFile("audio")
	if err != nil {
		return "", self_error.ErrFileRequired
	}
	defer file.Close()

	ext := filepath.Ext(header.Filename)
	if ext == "" {
		ext = ".bin"
	}
	tmpFile, err := os.CreateTemp("", "upload-*"+ext)
	if err != nil {
		return "", self_error.ErrCreateTempFile
	}
	defer tmpFile.Close()

	_, err = io.Copy(tmpFile, file)
	if err != nil {
		return "", self_error.ErrSaveFile
	}

	log.Println("uploaded:", header.Filename, "saved to:", tmpFile.Name())

	return tmpFile.Name(), nil
}

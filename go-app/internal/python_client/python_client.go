package python_client

import (
	"anonymization_of_voice_messages/internal/python_client/input_dto"
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func getPythonURL() string {
	url := os.Getenv("PYTHON_URL")
	if url == "" {
		url = "http://python-app:8000/anonymize"
	}
	return url
}

func SendFileToPython(requestID, wavPath string) (input_dto.ProcessResult, error) {
	file, err := os.Open(wavPath)
	if err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("open wav file: %w", err)

	}
	defer file.Close()

	var body bytes.Buffer
	writer := multipart.NewWriter(&body)

	part, err := writer.CreateFormFile("file", filepath.Base(wavPath))
	if err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("create multipart file: %w", err)
	}

	if _, err := io.Copy(part, file); err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("copy file to multipart: %w", err)
	}

	if err := writer.WriteField("request_id", requestID); err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("write request_id field: %w", err)
	}

	if err := writer.WriteField("language", "ru"); err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("write language field: %w", err)
	}

	if err := writer.Close(); err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("close multipart writer: %w", err)
	}
	client := &http.Client{
		Timeout: 20 * time.Minute,
	}

	req, err := http.NewRequest(http.MethodPost, getPythonURL(), &body)
	if err != nil {
		return input_dto.ProcessResult{}, err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := client.Do(req)
	if err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("send request to python: %w", err)
	}

	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("read python response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return input_dto.ProcessResult{}, fmt.Errorf("python service returned %d: %s", resp.StatusCode, string(respBody))
	}

	contentType := resp.Header.Get("Content-Type")
	if !strings.Contains(contentType, "application/zip") {
		return input_dto.ProcessResult{}, fmt.Errorf("unexpected python content-type: %s", contentType)
	}

	resultDir := filepath.Join("./storage/results", requestID)
	if err := os.MkdirAll(resultDir, 0o755); err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("create result dir: %w", err)
	}

	zipPath := filepath.Join(resultDir, requestID+"_result.zip")
	if err := os.WriteFile(zipPath, respBody, 0o644); err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("save zip file: %w", err)
	}

	zr, err := zip.NewReader(bytes.NewReader(respBody), int64(len(respBody)))
	if err != nil {
		return input_dto.ProcessResult{}, fmt.Errorf("open zip response: %w", err)
	}

	var resultWavPath string
	var resultJSONPath string
	var meta input_dto.PythonResult

	for _, zf := range zr.File {
		targetPath := filepath.Join(resultDir, zf.Name)

		if !isSafeZipPath(resultDir, targetPath) {
			return input_dto.ProcessResult{}, fmt.Errorf("unsafe zip path: %s", zf.Name)
		}

		if zf.FileInfo().IsDir() {
			if err := os.MkdirAll(targetPath, 0o755); err != nil {
				return input_dto.ProcessResult{}, fmt.Errorf("create zip dir: %w", err)
			}
			continue
		}

		if err := os.MkdirAll(filepath.Dir(targetPath), 0o755); err != nil {
			return input_dto.ProcessResult{}, fmt.Errorf("create parent dir: %w", err)
		}

		rc, err := zf.Open()
		if err != nil {
			return input_dto.ProcessResult{}, fmt.Errorf("open zip entry %s: %w", zf.Name, err)
		}

		data, err := io.ReadAll(rc)
		rc.Close()
		if err != nil {
			return input_dto.ProcessResult{}, fmt.Errorf("read zip entry %s: %w", zf.Name, err)
		}

		if err := os.WriteFile(targetPath, data, 0o644); err != nil {
			return input_dto.ProcessResult{}, fmt.Errorf("write extracted file %s: %w", zf.Name, err)
		}

		base := filepath.Base(zf.Name)
		switch base {
		case "redacted.wav":
			resultWavPath = targetPath
		case "result.json":
			resultJSONPath = targetPath
			if err := json.Unmarshal(data, &meta); err != nil {
				return input_dto.ProcessResult{}, fmt.Errorf("parse result.json: %w", err)
			}
		}
	}

	if resultWavPath == "" {
		return input_dto.ProcessResult{}, fmt.Errorf("redacted.wav not found in python zip response")
	}

	return input_dto.ProcessResult{
		ResultWavPath:  resultWavPath,
		ResultJSONPath: resultJSONPath,
		Meta:           meta,
	}, nil
}

func isSafeZipPath(baseDir, targetPath string) bool {
	baseAbs, err := filepath.Abs(baseDir)
	if err != nil {
		return false
	}
	targetAbs, err := filepath.Abs(targetPath)
	if err != nil {
		return false
	}

	rel, err := filepath.Rel(baseAbs, targetAbs)
	if err != nil {
		return false
	}

	return rel != ".." && !strings.HasPrefix(rel, ".."+string(os.PathSeparator))
}

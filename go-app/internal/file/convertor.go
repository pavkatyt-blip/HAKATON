package file

import (
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
)

func ConvertToWav(inputPath string) (string, error) {
	ext := filepath.Ext(inputPath)
	base := strings.TrimSuffix(inputPath, ext)
	outputPath := base + ".wav"

	cmd := exec.Command(
		"ffmpeg",
		"-y",
		"-i", inputPath,
		"-ar", "16000",
		"-ac", "1",
		"-c:a", "pcm_s16le",
		outputPath,
	)

	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("convert to wav: %w; ffmpeg output: %s", err, string(output))
	}

	return outputPath, nil
}

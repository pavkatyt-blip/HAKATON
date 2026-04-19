package input_dto

type PythonLog struct {
	Time    string `json:"time,omitempty"`
	Level   string `json:"level,omitempty"`
	Stage   string `json:"stage,omitempty"`
	Message string `json:"message,omitempty"`
}

type PythonPIISpan struct {
	Type        string  `json:"type"`
	StartTime   float64 `json:"start_time"`
	EndTime     float64 `json:"end_time"`
	Text        string  `json:"text"`
	Replacement string  `json:"replacement"`
}

type PythonResult struct {
	RequestID    string          `json:"request_id,omitempty"`
	Transcript   string          `json:"transcript,omitempty"`
	RedactedText string          `json:"redacted_text,omitempty"`
	PIISpans     []PythonPIISpan `json:"pii_spans,omitempty"`
	Logs         []PythonLog     `json:"logs,omitempty"`
}

type ProcessResult struct {
	ResultWavPath  string
	ResultJSONPath string
	Meta           PythonResult
}

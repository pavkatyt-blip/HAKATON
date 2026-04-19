package server

import (
	"errors"
	"net/http"
	"os"
	"time"

	"github.com/gorilla/mux"
	"go.uber.org/zap"
)

type HTTPServer struct {
	handlers *HTTPHandlers
	server   *http.Server
}

func NewHTTPServer(handlers *HTTPHandlers) *HTTPServer {
	return &HTTPServer{
		handlers: handlers,
	}
}

func (s *HTTPServer) Run() error {
	router := mux.NewRouter()

	router.Path("/anonymize").Methods(http.MethodPost).HandlerFunc(s.handlers.UploadAudio)
	router.Path("/tasks/{id}").Methods(http.MethodGet).HandlerFunc(s.handlers.GetTaskStatus)
	router.Path("/files/{id}").Methods(http.MethodGet).HandlerFunc(s.handlers.GetResultFile)
	router.Path("/tasks/{id}/logs").Methods(http.MethodGet).HandlerFunc(s.handlers.GetTaskLog)
	router.Path("/health").Methods(http.MethodGet).HandlerFunc(s.handlers.Health)

	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}
	s.server = &http.Server{
		Addr:    ":" + port,
		Handler: cors(logging(router, s.handlers.Logger)),
	}

	err := s.server.ListenAndServe()
	if errors.Is(err, http.ErrServerClosed) {
		return nil
	}

	return err
}

func cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		w.Header().Set("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func logging(next http.Handler, logger *zap.Logger) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		next.ServeHTTP(w, r)

		logger.Info("http request",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.Duration("duration", time.Since(start)),
		)
	})
}

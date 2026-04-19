package main

import (
	"anonymization_of_voice_messages/internal/server"
	"anonymization_of_voice_messages/internal/task"
	"log"
	"os"

	"go.uber.org/zap"
)

func main() {
	logger, err := zap.NewDevelopment()
	if err != nil {
		log.Fatalf("fialed to init logger: %v", err)
	}
	defer logger.Sync()

	taskStore := task.NewTaskStore()

	handlers := server.NewHTTPHandlers(taskStore, logger)

	httpServer := server.NewHTTPServer(handlers)

	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}

	logger.Info("starting server", zap.String("addr", ":"+port))

	if err := httpServer.Run(); err != nil {
		logger.Fatal("server stopped with error", zap.Error(err))
	}
}

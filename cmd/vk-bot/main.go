package main

import (
	"context"
	"errors"
	"log/slog"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"vk_bot/internal/app"
	"vk_bot/internal/config"
)

func main() {
	credsPath := config.DefaultCredsPath
	_ = os.MkdirAll(filepath.Dir(credsPath), 0o755)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	if err := app.Run(ctx, credsPath, logger); err != nil && !errors.Is(err, context.Canceled) {
		logger.Error("application stopped", "error", err)
		os.Exit(1)
	}

	logger.Info("application stopped gracefully")
}

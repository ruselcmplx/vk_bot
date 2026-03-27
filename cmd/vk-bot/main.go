package main

import (
	"context"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"vk_bot/internal/app"
	"vk_bot/internal/config"
)

const (
	instanceLockAddr     = "127.0.0.1:49122"
	instanceControlAddr  = "127.0.0.1:49123"
	lockAcquireTimeout   = 8 * time.Second
	lockAcquireRetryStep = 250 * time.Millisecond
)

func main() {
	credsPath := config.DefaultCredsPath
	_ = os.MkdirAll(filepath.Dir(credsPath), 0o755)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	lock, err := acquireInstanceLock()
	if err != nil {
		logger.Warn("instance lock is busy, requesting previous process shutdown", "error", err)
		if reqErr := requestShutdownExistingInstance(); reqErr != nil {
			logger.Error("cannot request shutdown of previous instance", "error", reqErr)
			os.Exit(1)
		}
		lock, err = waitForInstanceLock(lockAcquireTimeout, lockAcquireRetryStep)
		if err != nil {
			logger.Error("failed to acquire instance lock after shutdown request", "error", err)
			os.Exit(1)
		}
	}
	defer lock.Close()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	stopControl, err := startControlServer(cancel, logger)
	if err != nil {
		logger.Warn("cannot start control server", "error", err)
	} else {
		defer stopControl()
	}

	if err := app.Run(ctx, credsPath, logger); err != nil && !errors.Is(err, context.Canceled) {
		logger.Error("application stopped", "error", err)
		os.Exit(1)
	}

	logger.Info("application stopped gracefully")
}

func acquireInstanceLock() (net.Listener, error) {
	return net.Listen("tcp", instanceLockAddr)
}

func waitForInstanceLock(timeout time.Duration, step time.Duration) (net.Listener, error) {
	deadline := time.Now().Add(timeout)
	var lastErr error
	for time.Now().Before(deadline) {
		lock, err := acquireInstanceLock()
		if err == nil {
			return lock, nil
		}
		lastErr = err
		time.Sleep(step)
	}
	return nil, lastErr
}

func requestShutdownExistingInstance() error {
	client := &http.Client{Timeout: 2 * time.Second}
	req, err := http.NewRequest(http.MethodPost, "http://"+instanceControlAddr+"/shutdown", nil)
	if err != nil {
		return err
	}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return errors.New("shutdown endpoint returned non-2xx")
	}
	return nil
}

func startControlServer(cancel context.CancelFunc, logger *slog.Logger) (func(), error) {
	mux := http.NewServeMux()
	mux.HandleFunc("/shutdown", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		go cancel()
		w.WriteHeader(http.StatusAccepted)
		_, _ = w.Write([]byte("shutting down"))
	})

	srv := &http.Server{
		Addr:    instanceControlAddr,
		Handler: mux,
	}
	ln, err := net.Listen("tcp", instanceControlAddr)
	if err != nil {
		return nil, err
	}
	go func() {
		if serveErr := srv.Serve(ln); serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) {
			logger.Warn("control server stopped with error", "error", serveErr)
		}
	}()
	return func() {
		ctx, cancelShutdown := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancelShutdown()
		_ = srv.Shutdown(ctx)
	}, nil
}

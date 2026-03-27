package app

import (
	"context"
	"log/slog"
	"os"
	"time"

	"vk_bot/internal/bot"
	"vk_bot/internal/config"
	"vk_bot/internal/storage"
	vkclient "vk_bot/internal/vk"
)

func Run(ctx context.Context, credsPath string, logger *slog.Logger) error {
	for {
		logger.Info("app cycle start", "pid", os.Getpid(), "creds_path", credsPath)
		runtimeCfg, hash, err := config.LoadRuntimeFromCreds(credsPath)
		if err != nil {
			logger.Error("cannot load config", "error", err)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(10 * time.Second):
				continue
			}
		}

		store := storage.New(runtimeCfg.PhrasesPath, runtimeCfg.NounsPath)
		logger.Info("runtime config loaded",
			"group_id", runtimeCfg.GroupID,
			"bot_name", runtimeCfg.Name,
			"phrases_path", runtimeCfg.PhrasesPath,
			"nouns_path", runtimeCfg.NounsPath,
			"reload_interval", runtimeCfg.ReloadInterval,
		)
		client, err := vkclient.New(runtimeCfg.VKToken, runtimeCfg.GroupID)
		if err != nil {
			logger.Error("cannot init vk client", "error", err)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(10 * time.Second):
				continue
			}
		}

		b, err := bot.New(bot.Config{Name: runtimeCfg.Name}, store, client, logger)
		if err != nil {
			logger.Error("cannot init bot", "error", err)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(10 * time.Second):
				continue
			}
		}

		runCtx, cancel := context.WithCancel(ctx)
		errCh := make(chan error, 1)
		go func() {
			errCh <- b.Listen(runCtx)
		}()

		ticker := time.NewTicker(runtimeCfg.ReloadInterval)
		restart := false
		listenerDone := false
		for !restart {
			select {
			case <-ctx.Done():
				restart = true
			case err := <-errCh:
				listenerDone = true
				if err != nil {
					logger.Error("listener error", "error", err)
				}
				restart = true
			case <-ticker.C:
				_, nextHash, err := config.LoadRuntimeFromCreds(credsPath)
				if err != nil {
					logger.Error("reload read error", "error", err)
					continue
				}
				if nextHash != hash {
					logger.Info("config changed, reloading")
					restart = true
				}
			}
		}

		ticker.Stop()
		cancel()
		client.Shutdown()
		if !listenerDone {
			<-errCh
		}
		if ctx.Err() != nil {
			return ctx.Err()
		}
		time.Sleep(1 * time.Second)
	}
}

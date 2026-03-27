package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"vk_bot/internal/config"
	"vk_bot/internal/imagegen"
)

func main() {
	var prompt string
	var outPath string

	flag.StringVar(&prompt, "prompt", "A tiny red robot drinking coffee, pixel art", "image generation prompt")
	flag.StringVar(&outPath, "out", "./tmp/imagegen-smoke.png", "output file path")
	flag.Parse()

	runtimeCfg, _, err := config.LoadRuntimeFromCreds(config.DefaultCredsPath)
	if err != nil {
		panic(fmt.Errorf("load config: %w", err))
	}

	gen, err := imagegen.NewHuggingFace(runtimeCfg.HFToken, runtimeCfg.HFImageModel)
	if err != nil {
		panic(fmt.Errorf("init image generator: %w", err))
	}

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()

	data, err := gen.Generate(ctx, prompt)
	if err != nil {
		panic(fmt.Errorf("generate image: %w", err))
	}

	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		panic(fmt.Errorf("create output dir: %w", err))
	}
	if err := os.WriteFile(outPath, data, 0o644); err != nil {
		panic(fmt.Errorf("write output file: %w", err))
	}

	fmt.Printf("Model: %s\n", gen.Model())
	fmt.Printf("Saved: %s (%d bytes)\n", outPath, len(data))
}

package imagegen

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const (
	hfRouterBaseURL = "https://router.huggingface.co"
	defaultModel    = "black-forest-labs/FLUX.1-dev"
)

type Generator struct {
	token      string
	model      string
	httpClient *http.Client
}

func NewHuggingFace(token string, model string) (*Generator, error) {
	token = strings.TrimSpace(token)
	if token == "" {
		return nil, errors.New("HF_TOKEN is empty")
	}

	model = strings.TrimSpace(model)
	if model == "" {
		model = defaultModel
	}

	return &Generator{
		token: token,
		model: model,
		httpClient: &http.Client{
			Timeout: 120 * time.Second,
		},
	}, nil
}

func (g *Generator) Model() string {
	return g.model
}

func (g *Generator) Generate(ctx context.Context, prompt string) ([]byte, error) {
	prompt = strings.TrimSpace(prompt)
	if prompt == "" {
		return nil, errors.New("prompt is empty")
	}

	body, err := json.Marshal(map[string]string{
		"inputs": prompt,
	})
	if err != nil {
		return nil, err
	}

	endpoint := fmt.Sprintf("%s/hf-inference/models/%s", hfRouterBaseURL, url.PathEscape(g.model))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+g.token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := g.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		msg := strings.TrimSpace(string(data))
		if len(msg) > 512 {
			msg = msg[:512]
		}
		return nil, fmt.Errorf("hf inference error: status=%d body=%s", resp.StatusCode, msg)
	}
	if len(data) == 0 {
		return nil, errors.New("empty image response")
	}
	return data, nil
}

func HelpText(model string) string {
	return fmt.Sprintf("Использование: <имя_бота> нарисуй <описание>\nТекущая модель: %s", model)
}

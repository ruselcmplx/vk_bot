package bot

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"testing"

	"vk_bot/internal/vk"
)

func TestTrackAndMaybeReplyShitpostThreshold(t *testing.T) {
	b := &Bot{
		phrases:     []string{"reply"},
		shitposters: map[int]*shitposter{},
		logger:      slog.New(slog.NewTextHandler(io.Discard, nil)),
	}

	if got := b.trackAndMaybeReplyShitpost(10, 1000, 1); got != "" {
		t.Fatalf("unexpected: %q", got)
	}
	for i := 0; i < 7; i++ {
		if got := b.trackAndMaybeReplyShitpost(10, 1000+int64(i+1), 1); got != "" {
			t.Fatalf("unexpected early reply: %q", got)
		}
	}

	if got := b.trackAndMaybeReplyShitpost(10, 1010, 1); got != "reply" {
		t.Fatalf("expected reply, got %q", got)
	}
}

type fakeImageGen struct {
	model string
	data  []byte
	err   error
}

func (f fakeImageGen) Model() string { return f.model }
func (f fakeImageGen) Generate(_ context.Context, _ string) ([]byte, error) {
	if f.err != nil {
		return nil, f.err
	}
	return f.data, nil
}

type fakeVKClient struct {
	sentMessages []string
	sentPhotos   int
}

func (f *fakeVKClient) Listen(_ context.Context, _ func(vk.Message)) error { return nil }
func (f *fakeVKClient) SendMessage(_ int, msg string) error {
	f.sentMessages = append(f.sentMessages, msg)
	return nil
}
func (f *fakeVKClient) SendPhoto(_ int, _ []byte, _ string) error {
	f.sentPhotos++
	return nil
}
func (f *fakeVKClient) SetActivity(_ int, _ string) error      { return nil }
func (f *fakeVKClient) GetUserFirstName(_ int) (string, error) { return "", nil }
func (f *fakeVKClient) Shutdown()                              {}

func testBotWithClient(image fakeImageGen) (*Bot, *fakeVKClient) {
	client := &fakeVKClient{}
	b := &Bot{
		cfg:    Config{Name: "синдром"},
		logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		image:  image,
		client: client,
	}
	return b, client
}

func TestHandleDrawCommand_Usage(t *testing.T) {
	b, client := testBotWithClient(fakeImageGen{model: "test-model"})
	b.handleDrawCommand(1, []string{"синдром", "нарисуй"})
	if len(client.sentMessages) == 0 {
		t.Fatalf("expected usage message to be sent")
	}
}

func TestHandleDrawCommand_Success(t *testing.T) {
	b, client := testBotWithClient(fakeImageGen{model: "test-model", data: []byte{1, 2, 3}})
	b.handleDrawCommand(1, []string{"синдром", "нарисуй", "кот", "в", "шляпе"})
	if client.sentPhotos != 1 {
		t.Fatalf("expected one sent photo, got %d", client.sentPhotos)
	}
}

func TestHandleDrawCommand_Error(t *testing.T) {
	b, client := testBotWithClient(fakeImageGen{model: "test-model", err: errors.New("boom")})
	b.handleDrawCommand(1, []string{"синдром", "нарисуй", "кот"})
	if len(client.sentMessages) == 0 {
		t.Fatalf("expected error message to be sent")
	}
}

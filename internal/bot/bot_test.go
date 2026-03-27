package bot

import (
	"io"
	"log/slog"
	"testing"
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

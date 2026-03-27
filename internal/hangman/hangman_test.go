package hangman

import (
	"math/rand"
	"strings"
	"testing"
)

func TestJoinRunesSpaced(t *testing.T) {
	got := JoinRunesSpaced([]rune("абв"))
	if got != "а б в" {
		t.Fatalf("unexpected: %q", got)
	}
}

func TestNewInitialMasking(t *testing.T) {
	rand.Seed(1)
	g, err := New(123, []string{"слово"})
	if err != nil {
		t.Fatalf("New error: %v", err)
	}
	if g.PlayerID != 123 {
		t.Fatalf("PlayerID: %d", g.PlayerID)
	}
	if got, want := JoinRunesSpaced(g.ShownWord), "с _ _ _ о"; got != want {
		t.Fatalf("ShownWord: got %q want %q", got, want)
	}
}

func TestGuessWin(t *testing.T) {
	g, err := New(1, []string{"тест"})
	if err != nil {
		t.Fatal(err)
	}
	win, _ := g.Guess("е")
	if win {
		t.Fatalf("should not win yet")
	}
	win, msg := g.Guess("с")
	if !win || !strings.Contains(msg, "Ты победил") {
		t.Fatalf("expected win message, got: %q", msg)
	}
}

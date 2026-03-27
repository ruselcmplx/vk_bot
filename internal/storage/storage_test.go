package storage

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadPhrasesTrimsAndSkipsEmpty(t *testing.T) {
	dir := t.TempDir()
	phrasesPath := filepath.Join(dir, "phrases.txt")
	if err := os.WriteFile(phrasesPath, []byte("\n  привет \n\nпока\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	s := New(phrasesPath, filepath.Join(dir, "nouns.txt"))
	got, err := s.LoadPhrases()
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 2 || got[0] != "привет" || got[1] != "пока" {
		t.Fatalf("unexpected phrases: %#v", got)
	}
}

func TestAppendPhraseThenLoad(t *testing.T) {
	dir := t.TempDir()
	s := New(filepath.Join(dir, "phrases.txt"), filepath.Join(dir, "nouns.txt"))
	if err := s.AppendPhrase("one"); err != nil {
		t.Fatal(err)
	}
	if err := s.AppendPhrase("two"); err != nil {
		t.Fatal(err)
	}
	got, err := s.LoadPhrases()
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 2 || got[0] != "one" || got[1] != "two" {
		t.Fatalf("unexpected phrases: %#v", got)
	}
}

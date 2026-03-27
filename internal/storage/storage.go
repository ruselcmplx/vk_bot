package storage

import (
	"os"
	"strings"
)

type Store struct {
	PhrasesPath string
	NounsPath   string
}

func New(phrasesPath, nounsPath string) *Store {
	return &Store{
		PhrasesPath: phrasesPath,
		NounsPath:   nounsPath,
	}
}

func (s *Store) LoadPhrases() ([]string, error) {
	data, err := os.ReadFile(s.PhrasesPath)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(string(data), "\n")
	result := make([]string, 0, len(lines))
	for _, l := range lines {
		l = strings.TrimSpace(l)
		if l != "" {
			result = append(result, l)
		}
	}
	return result, nil
}

func (s *Store) LoadNouns() ([]string, error) {
	data, err := os.ReadFile(s.NounsPath)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(string(data), "\n")
	out := make([]string, 0, len(lines))
	for _, l := range lines {
		l = strings.TrimSpace(l)
		if l != "" {
			out = append(out, strings.ToLower(l))
		}
	}
	return out, nil
}

func (s *Store) AppendPhrase(phrase string) error {
	file, err := os.OpenFile(s.PhrasesPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer file.Close()
	_, err = file.WriteString(phrase + "\n")
	return err
}

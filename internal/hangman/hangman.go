package hangman

import (
	"errors"
	"fmt"
	"math/rand"
	"strings"
)

var pics = []string{
	"  +------+\n  |  |\n  |\n  |\n  |\n  |\n=========",
	"  +------+\n  |  |\n    O\n  |\n  |\n  |\n=========",
	"  +------+\n  |  |\n    O\n    |\n  |\n  |\n=========",
	"  +------+\n  |  |\n    O\n   /|\n  |\n  |\n=========",
	"  +------+\n  |  |\n    O\n   /|\\\n  |\n  |\n=========",
	"  +------+\n  |  |\n    O\n   /|\\\n   /\n  |\n=========",
	"  +------+\n  |  |\n    O\n   /|\\\n   / \\\n  |\n=========",
}

type Game struct {
	PlayerID    int
	Mistakes    int
	Win         bool
	HangmanPic  string
	UsedLetters map[string]struct{}
	Word        []rune
	ShownWord   []rune
}

func New(playerID int, nouns []string) (*Game, error) {
	if len(nouns) == 0 {
		return nil, errors.New("nouns file is empty")
	}

	word := []rune(nouns[rand.Intn(len(nouns))])
	if len(word) < 2 {
		return nil, fmt.Errorf("word %q is too short", string(word))
	}

	shown := make([]rune, len(word))
	shown[0] = word[0]
	for i := 1; i < len(word)-1; i++ {
		shown[i] = '_'
	}
	shown[len(word)-1] = word[len(word)-1]

	return &Game{
		PlayerID:    playerID,
		HangmanPic:  pics[0],
		UsedLetters: map[string]struct{}{},
		Word:        word,
		ShownWord:   shown,
	}, nil
}

func (g *Game) Guess(letter string) (bool, string) {
	if _, ok := g.UsedLetters[letter]; !ok {
		g.UsedLetters[letter] = struct{}{}
	}

	letterRune := []rune(letter)
	if len(letterRune) != 1 {
		return g.Win, "Введите одну букву"
	}

	found := false
	for i := 1; i < len(g.Word)-1; i++ {
		if string(g.Word[i]) == letter {
			g.ShownWord[i] = g.Word[i]
			found = true
		}
	}

	if found {
		hasUnderscore := false
		for _, ch := range g.ShownWord {
			if ch == '_' {
				hasUnderscore = true
				break
			}
		}
		if !hasUnderscore {
			g.Win = true
			return true, fmt.Sprintf("Ты победил!\nСлово %s", string(g.Word))
		}
		return false, JoinRunesSpaced(g.ShownWord)
	}

	if g.Mistakes < 5 {
		g.Mistakes++
		g.HangmanPic = pics[g.Mistakes]
		letters := make([]string, 0, len(g.UsedLetters))
		for l := range g.UsedLetters {
			letters = append(letters, l)
		}
		return false, fmt.Sprintf(
			"%s\nНет совпадений, использованные буквы: %s\n%s",
			g.HangmanPic,
			strings.Join(letters, ", "),
			JoinRunesSpaced(g.ShownWord),
		)
	}

	g.Mistakes++
	idx := g.Mistakes
	if idx >= len(pics) {
		idx = len(pics) - 1
	}
	g.HangmanPic = pics[idx]
	return false, fmt.Sprintf("%s\nТы проиграл\nСлово %s", g.HangmanPic, string(g.Word))
}

func JoinRunesSpaced(chars []rune) string {
	parts := make([]string, 0, len(chars))
	for _, c := range chars {
		parts = append(parts, string(c))
	}
	return strings.Join(parts, " ")
}

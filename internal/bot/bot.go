package bot

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"
	"os"
	"strings"
	"sync"
	"time"

	"vk_bot/internal/hangman"
	"vk_bot/internal/storage"
	"vk_bot/internal/vk"
)

type Config struct {
	Name string
}

type shitposter struct {
	UserID         int
	ShitpostCount  int
	FirstMessageAt int64
}

type Bot struct {
	cfg    Config
	store  *storage.Store
	client vk.Client
	logger *slog.Logger

	phrasesMu sync.RWMutex
	phrases   []string

	stateMu     sync.Mutex
	shitposters map[int]*shitposter
	game        *hangman.Game
	startedAt   time.Time
}

func New(cfg Config, store *storage.Store, client vk.Client, logger *slog.Logger) (*Bot, error) {
	phrases, err := store.LoadPhrases()
	if err != nil {
		return nil, err
	}
	return &Bot{
		cfg:         cfg,
		store:       store,
		client:      client,
		logger:      logger,
		phrases:     phrases,
		shitposters: map[int]*shitposter{},
		startedAt:   time.Now(),
	}, nil
}

func (b *Bot) Listen(ctx context.Context) error {
	b.logger.Info("bot listener started", "pid", os.Getpid(), "bot_name", b.cfg.Name, "phrases_loaded", len(b.phrases))
	return b.client.Listen(ctx, func(msg vk.Message) {
		b.handleMessage(msg.Text, msg.PeerID, msg.FromID, msg.Date)
	})
}

func (b *Bot) sendMessage(peerID int, msg string) {
	if strings.TrimSpace(msg) == "" {
		return
	}
	_ = b.client.SetActivity(peerID, "typing")
	time.Sleep(1 * time.Second)
	b.logger.Info("sending message", "peer_id", peerID, "message", msg)
	if err := b.client.SendMessage(peerID, msg); err != nil {
		b.logger.Error("send message error", "error", err)
	}
}

func (b *Bot) randomPhrase() string {
	b.phrasesMu.RLock()
	defer b.phrasesMu.RUnlock()
	if len(b.phrases) == 0 {
		return ""
	}
	return b.phrases[rand.Intn(len(b.phrases))]
}

func (b *Bot) addPhrase(authorID int, text []string) string {
	if len(text) < 3 {
		return ""
	}
	phrase := strings.TrimSpace(strings.Join(text[2:], " "))
	if phrase == "" {
		return ""
	}

	phraseLower := strings.ToLower(phrase)
	if strings.Contains(phraseLower, strings.ToLower(b.cfg.Name)) || strings.Contains(phraseLower, "@") {
		return ""
	}

	if err := b.store.AppendPhrase(phrase); err != nil {
		b.logger.Error("cannot append phrase", "error", err)
		return ""
	}

	b.phrasesMu.Lock()
	b.phrases = append(b.phrases, phrase)
	b.phrasesMu.Unlock()

	return fmt.Sprintf("[id%d|Филтан], я добавил: %q", authorID, phrase)
}

func (b *Bot) handleMessage(text string, chatID int, userID int, msgTime int64) {
	parts := strings.Fields(text)
	b.logger.Info("incoming message",
		"from_id", userID,
		"chat_id", chatID,
		"date_unix", msgTime,
		"text", text,
		"parts_count", len(parts),
	)
	if chatID == 0 || userID == 0 {
		b.logger.Warn("invalid message ids", "chat_id", chatID, "user_id", userID)
		return
	}

	if len(parts) > 0 && strings.Contains(strings.ToLower(parts[0]), strings.ToLower(b.cfg.Name)) {
		b.logger.Info("message addressed to bot", "from_id", userID, "chat_id", chatID, "parts", parts)
		if len(parts) == 1 {
			b.logger.Info("bot mention with single token, responding with random phrase", "from_id", userID, "chat_id", chatID)
			b.sendMessage(chatID, b.randomPhrase())
			return
		}
		switch {
		case strings.Contains(strings.ToLower(parts[1]), "добавь"):
			b.logger.Info("add phrase command", "from_id", userID, "chat_id", chatID)
			confirmation := b.addPhrase(userID, parts)
			if confirmation == "" {
				confirmation = b.randomPhrase()
			}
			b.sendMessage(chatID, confirmation)
		case strings.Contains(strings.ToLower(parts[1]), "виселица"):
			b.logger.Info("hangman start command", "from_id", userID, "chat_id", chatID)
			b.sendMessage(chatID, b.handleHangmanStart(userID))
		default:
			b.logger.Info("generic bot command fallback", "from_id", userID, "chat_id", chatID)
			b.sendMessage(chatID, b.randomPhrase())
		}
		return
	}

	if b.handleHangmanGuess(userID, parts, chatID) {
		return
	}

	phraseToSend := b.trackAndMaybeReplyShitpost(userID, msgTime, chatID)
	if phraseToSend != "" {
		b.sendMessage(chatID, phraseToSend)
	}
}

func (b *Bot) handleHangmanStart(userID int) string {
	b.stateMu.Lock()
	defer b.stateMu.Unlock()

	if b.game != nil {
		name, _ := b.client.GetUserFirstName(b.game.PlayerID)
		if name != "" {
			return fmt.Sprintf("%s, уже играет", name)
		}
		return "Кто-то уже играет"
	}

	nouns, err := b.store.LoadNouns()
	if err != nil {
		b.logger.Error("cannot load nouns", "error", err)
		return "Не получилось начать игру"
	}
	game, err := hangman.New(userID, nouns)
	if err != nil {
		b.logger.Error("new hangman error", "error", err)
		return "Не получилось начать игру"
	}

	b.game = game
	name, _ := b.client.GetUserFirstName(userID)
	if name == "" {
		name = "Ты"
	}
	return fmt.Sprintf("%s, ты в игре, слово %s", name, hangman.JoinRunesSpaced(game.ShownWord))
}

func (b *Bot) handleHangmanGuess(userID int, parts []string, chatID int) bool {
	if len(parts) != 1 || parts[0] == "" {
		return false
	}

	letter := strings.ToLower(strings.TrimSpace(parts[0]))
	if len([]rune(letter)) != 1 {
		return false
	}

	var (
		shouldHandle bool
		response     string
	)

	b.stateMu.Lock()
	if b.game != nil && b.game.PlayerID == userID {
		shouldHandle = true
		win, resp := b.game.Guess(letter)
		response = resp
		if win || strings.Contains(resp, "Ты проиграл") {
			b.game = nil
		}
	}
	b.stateMu.Unlock()

	if shouldHandle {
		b.sendMessage(chatID, response)
	}
	return shouldHandle
}

func (b *Bot) trackAndMaybeReplyShitpost(userID int, msgTime int64, chatID int) string {
	b.stateMu.Lock()
	defer b.stateMu.Unlock()

	user, ok := b.shitposters[userID]
	if !ok {
		b.shitposters[userID] = &shitposter{
			UserID:         userID,
			FirstMessageAt: msgTime,
		}
		return ""
	}

	if msgTime-user.FirstMessageAt > 180 {
		user.FirstMessageAt = msgTime
		user.ShitpostCount = 0
		b.logger.Info("shitpost window reset", "user_id", userID, "chat_id", chatID, "first_message_at", msgTime)
	}

	var phrase string
	if user.ShitpostCount >= 7 {
		phrase = b.randomPhrase()
		b.logger.Info("shitpost threshold reached", "user_id", user.UserID, "chat_id", chatID, "count_before_reset", user.ShitpostCount)
		user.ShitpostCount = 0
	}
	user.ShitpostCount++
	b.logger.Info("shitpost counter", "user_id", user.UserID, "chat_id", chatID, "count", user.ShitpostCount, "window_start", user.FirstMessageAt)
	return phrase
}

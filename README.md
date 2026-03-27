# VK Bot (Go)

## Что делает бот

- отвечает на обращения в чате VK по имени бота;
- команда `добавь` добавляет новую фразу в `phrases.txt`;
- команда `виселица` запускает игру;
- команда `нарисуй <описание>` генерирует изображение через Hugging Face Inference Providers;
- авто-ответ при "шитпосте" (много сообщений за короткое время).

## Требования

- Go 1.25+
- Токен сообщества VK (group token) с правами на сообщения

## Архитектура

- `cmd/vk-bot`: entrypoint приложения
- `internal/app`: orchestration, hot-reload, lifecycle
- `internal/config`: загрузка `creds.json` + hot reload
- `internal/vk`: адаптер над `vksdk`
- `internal/bot`: доменная логика обработки сообщений
- `internal/hangman`: логика игры
- `internal/storage`: чтение/запись файлов фраз и слов

## Конфигурация

Поддерживается только **горячая конфигурация через файлы** (удобно для контейнера):

- `config/creds.json` — параметры подключения к VK и имя бота
- `config/phrases.txt` — фразы (обновляются через команду `добавь`)
- `config/nouns.txt` — слова для виселицы

### Формат `creds.json`

По умолчанию ожидается `./config/creds.json`:

```json
{
  "vk_token": "group_token",
  "group_id": "group_id",
  "name": "синдром",
  "HF_TOKEN": "hf_xxx",
  "hf_image_model": "black-forest-labs/FLUX.1-dev"
}
```

- `HF_TOKEN` — токен Hugging Face для Inference Providers
- `hf_image_model` — модель для команды `нарисуй` (если пусто, используется `black-forest-labs/FLUX.1-dev`)

## Локальный запуск

```bash
go mod tidy
go run ./cmd/vk-bot
```

## Docker

```bash
docker compose up --build -d
```

Контейнер ожидает, что `./config` смонтирован в `/app/config`.

## Hot reload

Приложение периодически перечитывает `config/creds.json`.
Если изменяются `vk_token`, `group_id` или `name`, бот автоматически перезапускает longpoll без ручного рестарта контейнера.

## Тесты

```bash
go test ./...
```

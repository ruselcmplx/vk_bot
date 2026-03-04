# VK Bot - Modernized Python 3.10 Setup

## Local run

1. Create and activate a virtual environment (Python 3.10):

   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate  # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Prepare the `mnt` directory in the project root with:

   - `creds.json` - contains VK token, group_id, name, HF token, etc.
   - `phrases.txt` - list of bot phrases (one per line).
   - `nouns.txt` - list of nouns for the hangman game (one per line).

4. Run the bot:

   ```bash
   python bot.py
   ```

## Docker

1. Build the image (Python 3.10-slim base):

   ```bash
   docker build -t vk-bot .
   ```

2. Run the container, mounting `mnt` from the host:

   ```bash
   docker run --rm \
     -v ${PWD}/mnt:/app/mnt \
     vk-bot
   ```

   On Windows PowerShell, use:

   ```powershell
   docker run --rm `
     -v ${PWD}/mnt:/app/mnt `
     vk-bot
   ```

The container expects `creds.json`, `phrases.txt` and `nouns.txt` to be available in `/app/mnt`.

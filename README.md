# Telegram Bot

A feature-rich Telegram bot built with Python 3.13 and [aiogram 3](https://docs.aiogram.dev/).

## Features

- **Weather (`/weather [city]`)**: Get the current weather for a specific city or by sharing your location. Powered by OpenWeatherMap.
- **Forecast (`/forecast [city]`)**: Get a 5-day weather forecast (with 3-hour intervals for the first 24 hours). 
- **Time (`/time [city]`)**: Look up the current local time and timezone for any given city, or check the server's local time.
- **Log Viewer (`/log`)**: Displays the last 30 interactions from the bot's log file for quick monitoring without server access.
- **Inline Queries**: Type `@<YourBotName> [city]` in any chat to instantly get the weather for that city. Includes auto-completion if `cities.txt` is populated.
- **System Top (`/top`)**: Shows server resource usage utilizing the standard linux `top` command.
- **Random Photos (`/photo`)**: Sends a randomly selected photo from the local `photos/` directory.
- **Group Management**: The bot automatically greets new members when they join a group.
- **Auto-Replies**: The bot listens for specific keywords (e.g., "hello", "pricing", "support") and responds automatically.
- **Logging**: Includes `InteractionLoggingMiddleware` to log all bot interactions (messages, inline queries) to `commands.log`.

## Requirements

- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) (Package Manager)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenWeatherMap API Key

## Setup & Installation

1. **Clone the repository** (or navigate to your project directory):
   ```bash
   cd telegram-bot
   ```

2. **Install dependencies**:
   The project uses `uv` for dependency management. To install the required packages (as listed in `pyproject.toml`):
   ```bash
   uv sync
   ```

3. **Environment Variables**:
   Copy the example environment file and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and configure:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   WEATHER_API_KEY=your_openweathermap_api_key_here
   ```

4. **Prepare Assets (Optional)**:
   - Create a `photos/` directory and add `.jpg` or `.png` files to use the `/photo` command.
   - Create a `cities.txt` file (one city per line) to enable inline search autocompletion.

## Usage

Once everything is set up, start the bot by running:

```bash
uv run python bot.py
```
*(Or simply `python bot.py` if your virtual environment is activated)*

## Testing

The project uses `pytest` and `pytest-asyncio` for unit testing. The tests are located in the `tests/` directory.

To run the entire test suite:
```bash
uv run pytest
```

To run a specific test file:
```bash
uv run pytest tests/test_start.py
```

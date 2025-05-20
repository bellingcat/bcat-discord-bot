# Discord Bot with Static Site Generator

A Discord bot that collects forum threads with the 'Featured' tag and generates a static HTML page. The static site can be viewed locally or served from any static file hosting.

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   DISCORD_GUILD_ID=your_guild_id
   DISCORD_FORUM_CHANNEL_IDS=forum_channel_id1,forum_channel_id2
   DISCORD_FEATURED_TAG_NAME=Featured
   ```

## Running the Bot

To run the Discord bot and generate the static site:

```
python bot.py
```

This will:

1. Connect to Discord
2. Fetch threads with the 'Featured' tag from the specified forum channels
3. Generate a static HTML site in the `dist` directory

## Automated Execution

The bot can be set up to run periodically (e.g., every 5 minutes) using a task scheduler:

1. Fetch the latest featured threads from Discord
2. Generate a fresh static HTML site

## Project Structure

- `bot.py` - Discord bot that fetches forum threads with the 'Featured' tag and generates a static site
- `templates/` - HTML templates used for static site generation
- `static/` - CSS, JavaScript, and font files for the static site
- `dist/` - Output directory for the generated static site

## Features

- Fetches forum threads with the 'Featured' tag
- Generates a clean, modern static interface showing the featured discussions
- Displays thread titles and content
- Shows message and reaction counts with proper Discord-style icons
- Provides links back to the original Discord threads
- Responsive design for all screen sizes
- No server required - pure static HTML/CSS/JS

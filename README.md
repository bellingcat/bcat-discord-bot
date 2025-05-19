# Discord Bot with Web Interface

A Discord bot that collects messages from channels and displays them in a web interface similar to a discussion board. The web interface can be embedded in a WordPress site via an iframe.

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
   DISCORD_CHANNEL_IDS=channel_id1,channel_id2,channel_id3
   ```

## Running the Bot

To run the Discord bot:

```
python bot.py
```

This will connect to Discord and start collecting messages from the specified channels.

## Running the Web Interface

To run the web interface locally:

```
python web_interface.py
```

This will start a Flask server on http://localhost:5000

## Deploying to AWS

To deploy the web interface to AWS S3 for WordPress embedding:

1. Make sure you have AWS credentials configured
2. Run the deployment script:
   ```
   python deploy.py --bucket your-bucket-name --region your-aws-region
   ```
3. The script will output an iframe code to embed in your WordPress site

## Project Structure

- `bot.py` - Discord bot that collects messages
- `web_interface.py` - Flask app that serves the web interface
- `deploy.py` - Script to deploy to AWS S3
- `templates/` - HTML templates
- `static/` - CSS and JavaScript files
- `data/` - Message storage

## Features

- Collects messages from Discord channels
- Displays messages in a clean, modern interface
- Groups messages by channel
- Shows message counts and reactions
- Responsive design for all screen sizes
- One-command deployment to AWS S3
- Easy WordPress embedding via iframe

# Discord Bot with Web Interface

A Discord bot that collects forum threads with the 'Featured' tag and displays them in a web interface similar to a discussion board. The web interface can be embedded in a WordPress site via an iframe.

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

To run the Discord bot:

```
python bot.py
```

This will connect to Discord and start monitoring the specified forum channels for threads with the 'Featured' tag.

## Running the Web Interface

To run the web interface locally:

```
python web_interface.py
```

This will start a Flask server on http://localhost:3010

## Deploying to AWS

To deploy the web interface to AWS S3 for WordPress embedding:

1. Make sure you have AWS credentials configured
2. Run the deployment script:
   ```
   python deploy.py --bucket your-bucket-name --region your-aws-region
   ```
3. The script will output an iframe code to embed in your WordPress site

## Project Structure

- `bot.py` - Discord bot that monitors forum threads with the 'Featured' tag
- `web_interface.py` - Flask app that serves the web interface
- `deploy.py` - Script to deploy to AWS S3
- `templates/` - HTML templates
- `static/` - CSS and JavaScript files
- `data/` - Message storage

## Features

- Monitors forum threads with the 'Featured' tag
- Automatically updates when tags are applied to threads
- Displays the 4 most recent featured threads in a clean, modern interface
- Shows thread titles and content
- Responsive design for all screen sizes
- One-command deployment to AWS S3
- Easy WordPress embedding via iframe

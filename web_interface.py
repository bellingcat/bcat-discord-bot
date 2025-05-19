import os
import json
from flask import Flask, render_template, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# Message storage
MESSAGES_FILE = 'data/messages.json'

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return {"channels": {}}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/discussions')
def get_discussions():
    """API endpoint to get discussion data"""
    messages_data = load_messages()
    
    # Get Discord guild ID from environment
    guild_id = os.getenv('DISCORD_GUILD_ID', '')
    
    # Format the data for the frontend
    discussions = []
    
    # Collect all messages across all channels
    all_messages = []
    for channel_id, channel_data in messages_data["channels"].items():
        for message in channel_data["messages"]:
            all_messages.append({
                "message": message,
                "channel_id": channel_id,
                "channel_name": channel_data["name"],
                "category": channel_data["category"]
            })
    
    # Sort all messages by timestamp (newest first)
    all_messages.sort(key=lambda x: x["message"]["timestamp"], reverse=True)
    
    # Create discussions from the most recent messages
    for item in all_messages:
        message = item["message"]
        channel_id = item["channel_id"]
        channel_name = item["channel_name"]
        category = item["category"]
        
        # Build Discord channel URL
        discord_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message['id']}"
        
        # Get the message timestamp
        timestamp = message["timestamp"]
        # Convert to human-readable time ago
        time_ago = "1h ago"  # Simplified for now
        
        # Extract tags
        tags = []
        if category and category != "None":
            tags.append(category)
        
        # Look for hashtags in content
        content = message.get("content", "")
        hashtags = [word[1:] for word in content.split() if word.startswith("#")]
        tags.extend(hashtags)
        
        # If no tags found, add a default one
        if not tags:
            tags.append("Discussion")
        
        # Create discussion object
        discussion = {
            "id": message["id"],
            "title": f"Discussion in #{channel_name}",
            "content": content,
            "message_count": 1,  # Simplified since we're now storing individual messages
            "reaction_count": len(message.get("reactions", [])),
            "time_ago": time_ago,
            "discord_url": discord_url,
            "tags": tags
        }
        
        discussions.append(discussion)
    
    # Limit to the 4 most recent discussions
    discussions = discussions[:4]
    
    return jsonify({"discussions": discussions})

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/fonts', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=3010) 
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
    
    
    guild_id = os.getenv('DISCORD_GUILD_ID', '')
    
    
    discussions = []
    
    
    all_messages = []
    for channel_id, channel_data in messages_data["channels"].items():
        for message in channel_data["messages"]:
            all_messages.append({
                "message": message,
                "channel_id": channel_id,
                "channel_name": channel_data["name"],
                "category": channel_data["category"]
            })
    
    
    all_messages.sort(key=lambda x: x["message"]["timestamp"], reverse=True)
    
    
    for item in all_messages:
        message = item["message"]
        channel_id = item["channel_id"]
        channel_name = item["channel_name"]
        category = item["category"]
        
    
        discord_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message['id']}"
        
    
        timestamp = message["timestamp"]
    
        time_ago = timestamp
        
        def iso_to_human_readable(iso_string):
            # Parse the ISO 8601 datetime string
            dt = datetime.fromisoformat(iso_string)
            # Format to a human-readable string
            return dt.strftime('%A, %d %B %Y at %H:%M:%S')


        time_ago = iso_to_human_readable(timestamp)
        
        tags = []
        if category and category != "None":
            tags.append(category)
        
        
        content = message.get("content", "")
        hashtags = [word[1:] for word in content.split() if word.startswith("#")]
        tags.extend(hashtags)
        
        
        if not tags:
            tags.append("Discussion")
        
        # Set the title (use thread_name if available, otherwise default to channel name)
        title = message.get("thread_name", f"Discussion in #{channel_name}")
        
        
        discussion = {
            "id": message["id"],
            "title": title,
            "content": content,
            "message_count": 1,  
            "reaction_count": len(message.get("reactions", [])),
            "time_ago": time_ago,
            "discord_url": discord_url,
            "tags": tags
        }
        
        discussions.append(discussion)
    
    
    discussions = discussions[:4]
    
    return jsonify({"discussions": discussions})

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/fonts', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=3010) 
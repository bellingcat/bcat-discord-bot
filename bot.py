import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))
FORUM_CHANNEL_IDS = [int(id) for id in os.getenv('DISCORD_FORUM_CHANNEL_IDS', '').split(',') if id]
FEATURED_TAG_NAME = os.getenv('DISCORD_FEATURED_TAG_NAME', 'Featured')

# Message storage
MESSAGES_FILE = 'data/messages.json'
os.makedirs('data', exist_ok=True)

# Initialize Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load existing messages or create empty structure
def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return {"channels": {}}

# Save messages to file
def save_messages(messages_data):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages_data, f, indent=2)

# Check if a thread has the Featured tag
def has_featured_tag(thread):
    """Check if a thread has the Featured tag"""
    if not hasattr(thread, 'applied_tags'):
        return False
    
    for tag in thread.applied_tags:
        if hasattr(tag, 'name') and tag.name == FEATURED_TAG_NAME:
            return True
        
        if isinstance(tag, str) and tag == FEATURED_TAG_NAME:
            return True
        
        if hasattr(thread.parent, 'available_tags'):
            for available_tag in thread.parent.available_tags:
                if available_tag.id == tag and available_tag.name == FEATURED_TAG_NAME:
                    return True
    
    return False

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        print(f'Connected to guild: {guild.name}')
        print(f'Monitoring forum channels: {FORUM_CHANNEL_IDS}')
    else:
        print(f'Could not find guild with ID: {GUILD_ID}')

@bot.event
async def on_thread_create(thread):
    if thread.parent_id not in FORUM_CHANNEL_IDS:
        return
    
    if not has_featured_tag(thread):
        return
    
    async for message in thread.history(limit=1, oldest_first=True):
        initial_message = message
        break
    else:
        return
    
    message_data = {
        "id": str(initial_message.id),
        "content": initial_message.content,
        "thread_name": thread.name,
        "author": {
            "id": str(initial_message.author.id),
            "name": initial_message.author.name,
            "display_name": initial_message.author.display_name
        },
        "channel_id": str(thread.parent_id),
        "channel_name": thread.parent.name if thread.parent else "Unknown",
        "timestamp": initial_message.created_at.isoformat(),
        "reactions": [{"emoji": str(reaction.emoji), "count": reaction.count} for reaction in initial_message.reactions],
        "attachments": [attachment.url for attachment in initial_message.attachments]
    }
    
    add_message_to_storage(message_data)
    print(f"Added new thread {thread.name} to messages because it has the Featured tag")

@bot.event
async def on_thread_update(before, after):
    if after.parent_id not in FORUM_CHANNEL_IDS:
        return
    
    if not has_featured_tag(after):
        return
    
    async for message in after.history(limit=1, oldest_first=True):
        initial_message = message
        break
    else:
        return
    
    message_data = {
        "id": str(initial_message.id),
        "content": initial_message.content,
        "thread_name": after.name,
        "author": {
            "id": str(initial_message.author.id),
            "name": initial_message.author.name,
            "display_name": initial_message.author.display_name
        },
        "channel_id": str(after.parent_id),
        "channel_name": after.parent.name if after.parent else "Unknown",
        "timestamp": initial_message.created_at.isoformat(),
        "reactions": [{"emoji": str(reaction.emoji), "count": reaction.count} for reaction in initial_message.reactions],
        "attachments": [attachment.url for attachment in initial_message.attachments]
    }
    
    add_message_to_storage(message_data)
    print(f"Added thread {after.name} to messages as it has the Featured tag")

def add_message_to_storage(message_data):
    messages_data = load_messages()
    
    if "channels" not in messages_data:
        messages_data["channels"] = {}
    
    if "channel_id" not in message_data:
        print(f"Error: Message is missing channel_id field. Skipping message {message_data.get('id', 'unknown')}.")
        return
        
    channel_id = message_data["channel_id"]
    if channel_id not in messages_data["channels"]:
        messages_data["channels"][channel_id] = {
            "name": message_data["channel_name"],
            "category": str(message_data.get("category", "None")),
            "messages": []
        }
    
    messages_data["channels"][channel_id]["messages"].append(message_data)
    
    all_messages = []
    for channel_id, channel in messages_data["channels"].items():
        channel_name = channel.get("name", "Unknown")
        messages_with_metadata = []
        
        for msg in channel["messages"]:
            if "channel_id" not in msg:
                msg["channel_id"] = channel_id
            if "channel_name" not in msg:
                msg["channel_name"] = channel_name
            
            messages_with_metadata.append((msg, channel_name))
        
        all_messages.extend(messages_with_metadata)
    
    all_messages.sort(key=lambda x: x[0]["timestamp"], reverse=True)
    
    if len(all_messages) > 4:
        new_channels = {}
        
        for msg, channel_name in all_messages[:4]:
            channel_id = msg["channel_id"]
            
            if channel_id not in new_channels:
                new_channels[channel_id] = {
                    "name": msg["channel_name"],
                    "category": messages_data["channels"].get(channel_id, {}).get("category", "None"),
                    "messages": []
                }
            
            new_channels[channel_id]["messages"].append(msg)
        
        messages_data["channels"] = new_channels
    
    save_messages(messages_data)
    print(f"Saved message. Storage now contains {sum(len(c['messages']) for c in messages_data['channels'].values())} messages total.")

@bot.command(name='status')
async def status(ctx):
    messages_data = load_messages()
    channel_count = len(messages_data["channels"])
    message_count = sum(len(channel["messages"]) for channel in messages_data["channels"].values())
    
    await ctx.send(f"Bot is running! Monitoring {len(FORUM_CHANNEL_IDS)} forum channels with {message_count} messages stored.")

# Run the bot
if __name__ == "__main__":
    print("Starting Discord bot...")
    bot.run(TOKEN) 
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
from datetime import datetime
import asyncio
import shutil
import sys
import re

load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))
FORUM_CHANNEL_IDS = [int(id) for id in os.getenv('DISCORD_FORUM_CHANNEL_IDS', '').split(',') if id]
FEATURED_TAG_NAME = os.getenv('DISCORD_FEATURED_TAG_NAME', 'Featured')

OUTPUT_DIR = 'dist'
os.makedirs(OUTPUT_DIR, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
featured_threads = []


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

def get_tags(thread):
    """Get the tags of a thread"""
    if not hasattr(thread, 'applied_tags'):
        return []
    
    tags = []
    for tag in thread.applied_tags:
        if hasattr(tag, 'name'):
            tags.append(tag.name)
        elif isinstance(tag, str):
            tags.append(tag)
    
    return [t for t in tags if t != FEATURED_TAG_NAME]  # Exclude the Featured tag itself

def expand_channel_mentions(text, guild):
    """Replace occurrences of <#channel_id> with #channel-name in the provided text."""
    if not text:
        return text

    def replace_match(match):
        try:
            channel_id = int(match.group(1))
        except Exception:
            return match.group(0)

        channel = guild.get_channel(channel_id) if guild else None
        return f"#{channel.name}" if channel and hasattr(channel, 'name') else match.group(0)

    return re.sub(r'<#(\d+)>', replace_match, text)

async def process_thread(thread):
    if not has_featured_tag(thread):
        return None

    try:
        
        async for message in thread.history(limit=1, oldest_first=True):
            initial_message = message
            break
        else:
            return None


        # fetch last message
        last_message = await thread.fetch_message(thread.last_message_id)

        # Expand channel mention IDs in content
        expanded_content = expand_channel_mentions(initial_message.content, getattr(thread, 'guild', None))

        # Collect channel mentions as readable names
        try:
            channel_mentions = [f"#{c.name}" for c in getattr(initial_message, 'channel_mentions', []) if hasattr(c, 'name')]
        except Exception:
            channel_mentions = []

        message_data = {
            "id": str(initial_message.id),
            "content": expanded_content,
            "thread_name": thread.name,
            "author": {
                "id": str(initial_message.author.id),
                "name": initial_message.author.name,
                "display_name": initial_message.author.display_name
            },
            "channel_id": str(thread.parent_id),
            "channel_name": thread.parent.name if thread.parent else "Unknown",
            "timestamp": initial_message.created_at.isoformat(),
            "latest_timestamp": last_message.created_at.isoformat(),
            "reactions": [{"emoji": str(reaction.emoji), "count": reaction.count} for reaction in initial_message.reactions],
            "attachments": [attachment.url for attachment in initial_message.attachments],
            "message_count": thread.message_count+1,
            "tags": get_tags(thread),
            "channel_mentions": channel_mentions,
        }
        
        return message_data
    except Exception as e:
        print(f"Error processing thread {thread.name}: {e}")
        return None

def generate_static_site(messages_data):
    try:
        if os.path.exists('static'):
            if os.path.exists(f'{OUTPUT_DIR}/static'):
                shutil.rmtree(f'{OUTPUT_DIR}/static')
            shutil.copytree('static', f'{OUTPUT_DIR}/static')
        
        
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
                
        all_messages.sort(key=lambda x: x["message"].get("latest_timestamp", x["message"]["timestamp"]), reverse=True)
        all_messages = all_messages[:4]  # Keep only 4 most recent
        
        for item in all_messages:
            message = item["message"]
            channel_id = item["channel_id"]
            channel_name = item["channel_name"]
            category = item["category"]
            
            discord_url = f"https://discord.com/channels/{guild_id}/{channel_id}/threads/{message['id']}"
            
            tags = item["message"].get("tags", [])
            if category and category != "None":
                tags.append(category)            
            
            content = message.get("content", "")
            
            if not tags:
                tags.append("Discussion")
            
            
            display_timestamp = message.get("latest_timestamp", message["timestamp"])
            
            def iso_to_human_readable(iso_string):
                dt = datetime.fromisoformat(iso_string)
                return dt.strftime('%B %d %Y at %H:%M:%S')

            time_ago = iso_to_human_readable(display_timestamp)
            
            discussion = {
                "id": message["id"],
                "title": message.get("thread_name", f"Discussion in #{channel_name}"),
                "content": content,
                "channel": channel_name,
                "message_count": item["message"]["message_count"],
                "reaction_count": len(message.get("reactions", [])),
                "timestamp": message["timestamp"],
                "latest_timestamp": message.get("latest_timestamp", message["timestamp"]),
                "time_ago": time_ago,
                "discord_url": discord_url,
                "tags": tags
            }
            
            discussions.append(discussion)
        
        
        discussions_html = ""
        
        for discussion in discussions:
            
            tags_html = ""
            for tag in discussion["tags"]:
                tags_html += f'<span class="tag">{tag}</span>'
            
            
            card_html = f"""
            <div class="discussion-card">
                <div class="card-header">
                    <div class="tags">
                        {tags_html}
                    </div>
                    <h2 class="title"><a href="{discussion["discord_url"]}" target="_blank">{discussion["title"]}</a></h2>
                </div>
                <div class="card-body">
                    <p class="content">{discussion["content"]}</p>
                </div>
                <div class="card-footer">
                    <div class="meta">
                        <span class="messages">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
                            </svg>
                            {discussion["message_count"]}
                        </span>
                        <span class="reactions">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16zm4-9h-3V8a1 1 0 00-2 0v3H8a1 1 0 000 2h3v3a1 1 0 002 0v-3h3a1 1 0 000-2z"/>
                            </svg>
                            {discussion["reaction_count"]}
                        </span>
                    </div>
                    <div class="time">{discussion["time_ago"]}</div>
                </div>
            </div>
            """
            
            discussions_html += card_html
        
        
        if not discussions_html:
            discussions_html = '<p class="no-discussions">No featured discussions found.</p>'
        
        
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recent community discussions on Discord</title>
    <link rel="stylesheet" href="static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <div class="header-left">
                <div class="header-discord-icon">
                    <svg width="28" height="28" viewBox="0 0 71 55" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M60.1045 4.8978C55.5792 2.8214 50.7265 1.2916 45.6527 0.41542C45.5603 0.39851 45.468 0.440769 45.4204 0.525289C44.7963 1.6353 44.105 3.0834 43.6209 4.2216C38.1637 3.4046 32.7345 3.4046 27.3892 4.2216C26.905 3.0581 26.1886 1.6353 25.5617 0.525289C25.5141 0.443589 25.4218 0.40133 25.3294 0.41542C20.2584 1.2888 15.4057 2.8186 10.8776 4.8978C10.8384 4.9147 10.8048 4.9429 10.7825 4.9795C1.57795 18.7309 -0.943561 32.1443 0.293408 45.3914C0.299005 45.4562 0.335386 45.5182 0.385761 45.5576C6.45866 50.0174 12.3413 52.7249 18.1147 54.5195C18.2071 54.5477 18.305 54.5139 18.3638 54.4378C19.7295 52.5728 20.9469 50.6063 21.9907 48.5383C22.0523 48.4172 21.9935 48.2735 21.8676 48.2256C19.9366 47.4931 18.0979 46.6 16.3292 45.5858C16.1893 45.5041 16.1781 45.304 16.3068 45.2082C16.679 44.9293 17.0513 44.6391 17.4067 44.3461C17.471 44.2926 17.5606 44.2813 17.6362 44.3151C29.2558 49.6202 41.8354 49.6202 53.3179 44.3151C53.3935 44.2785 53.4831 44.2898 53.5502 44.3433C53.9057 44.6363 54.2779 44.9293 54.6529 45.2082C54.7816 45.304 54.7732 45.5041 54.6333 45.5858C52.8646 46.6197 51.0259 47.4931 49.0921 48.2228C48.9662 48.2707 48.9102 48.4172 48.9718 48.5383C50.038 50.6034 51.2554 52.5699 52.5959 54.435C52.6519 54.5139 52.7526 54.5477 52.845 54.5195C58.6464 52.7249 64.529 50.0174 70.6019 45.5576C70.6551 45.5182 70.6887 45.459 70.6943 45.3942C72.1747 30.0791 68.2147 16.7757 60.1968 4.9823C60.1772 4.9429 60.1437 4.9147 60.1045 4.8978ZM23.7259 37.3253C20.2276 37.3253 17.3451 34.1136 17.3451 30.1693C17.3451 26.225 20.1717 23.0133 23.7259 23.0133C27.308 23.0133 30.1626 26.2532 30.1066 30.1693C30.1066 34.1136 27.28 37.3253 23.7259 37.3253ZM47.3178 37.3253C43.8196 37.3253 40.9371 34.1136 40.9371 30.1693C40.9371 26.225 43.7636 23.0133 47.3178 23.0133C50.9 23.0133 53.7545 26.2532 53.6986 30.1693C53.6986 34.1136 50.9 37.3253 47.3178 37.3253Z" fill="white"/>
                    </svg>
                </div>
                <h1>Recent community discussions on Discord</h1>
            </div>
        </header>
        <div class="discussions-grid">
            {discussions_html}
        </div>
    </div>
</body>
</html>
"""
        
        # Write the index.html file
        with open(f'{OUTPUT_DIR}/index.html', 'w') as f:
            f.write(index_html)
            
        print(f"Successfully generated static site in {OUTPUT_DIR} directory")
        
    except Exception as e:
        print(f"Error generating static site: {e}")

@bot.event
async def on_ready():
    try:
        print(f'{bot.user.name} has connected to Discord!')
        print(bot.guilds)
        guild = discord.utils.get(bot.guilds, id=GUILD_ID)
        if guild:
            print(f'Connected to guild: {guild.name}')
            print(f'Fetching featured threads from forum channels: {FORUM_CHANNEL_IDS}')
            
            messages_data = {"channels": {}}
            featured_threads = []
            batch_threads = []      

            for forum_id in FORUM_CHANNEL_IDS:
                try:
                    forum_channel = guild.get_channel(forum_id)
                    if not forum_channel:
                        print(f"Could not find forum channel with ID: {forum_id}")
                        channel_batch_info[forum_id]['has_more'] = False
                        continue
                                            
                    
                    if hasattr(forum_channel, 'threads'):
                        active_batch = forum_channel.threads
                        batch_threads.extend([(thread, forum_channel.name) for thread in active_batch])
                    
                
                except Exception as e:
                    print(f"Error processing forum channel {forum_id}: {e}")
                    channel_batch_info[forum_id]['has_more'] = False

            for thread, channel_name in batch_threads:
                thread_data = await process_thread(thread)
                if thread_data:
                    featured_threads.append((thread_data, channel_name))
                    print(f"Added thread {thread.name} as it has the Featured tag")
                    
            print(f"Found {len(featured_threads)} featured threads")
            
            for thread_data, channel_name in featured_threads:
                channel_id = thread_data["channel_id"]
                
                if channel_id not in messages_data["channels"]:
                    messages_data["channels"][channel_id] = {
                        "name": thread_data["channel_name"],
                        "category": "None",
                        "messages": []
                    }
                
                messages_data["channels"][channel_id]["messages"].append(thread_data)
            
            generate_static_site(messages_data)
        else:
            print(f"Could not find guild with ID: {GUILD_ID}")
    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        print("Shutting down bot")
        await bot.close()

async def main():
    # Use context manager to ensure the underlying HTTP connector is closed cleanly
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    print("Starting Discord bot to fetch featured threads...")
    asyncio.run(main()) 
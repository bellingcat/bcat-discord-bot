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
CHANNEL_IDS = [int(id) for id in os.getenv('DISCORD_CHANNEL_IDS', '').split(',') if id]
MODERATOR_IDS = [int(id) for id in os.getenv('DISCORD_MODERATOR_IDS', '').split(',') if id]
APPROVAL_CHANNEL_ID = int(os.getenv('DISCORD_APPROVAL_CHANNEL_ID', 0))

# Message storage
MESSAGES_FILE = 'data/messages.json'
PENDING_FILE = 'data/pending_messages.json'
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

# Load pending messages
def load_pending():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r') as f:
            return json.load(f)
    return {"pending": []}

# Save messages to file
def save_messages(messages_data):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages_data, f, indent=2)

# Save pending messages to file
def save_pending(pending_data):
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending_data, f, indent=2)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        print(f'Connected to guild: {guild.name}')
    else:
        print(f'Could not find guild with ID: {GUILD_ID}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if this is a moderator response to an approval request
    if message.channel.id == APPROVAL_CHANNEL_ID and message.reference:
        await handle_approval_response(message)
        return
    
    # Only process messages from specified channels
    if not CHANNEL_IDS or message.channel.id in CHANNEL_IDS:
        # Create message data
        message_data = {
            "id": str(message.id),
            "content": message.content,
            "author": {
                "id": str(message.author.id),
                "name": message.author.name,
                "display_name": message.author.display_name
            },
            "channel_id": str(message.channel.id),
            "channel_name": message.channel.name,
            "timestamp": message.created_at.isoformat(),
            "reactions": [{"emoji": str(reaction.emoji), "count": reaction.count} for reaction in message.reactions],
            "attachments": [attachment.url for attachment in message.attachments]
        }
        
        # Send to approval channel
        if APPROVAL_CHANNEL_ID:
            approval_channel = bot.get_channel(APPROVAL_CHANNEL_ID)
            if approval_channel:
                # Create embed for approval
                embed = discord.Embed(
                    title="New message for approval",
                    description=f"**Content:** {message.content[:1000]}{'...' if len(message.content) > 1000 else ''}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Author", value=message.author.display_name)
                embed.add_field(name="Channel", value=f"#{message.channel.name}")
                embed.set_footer(text=f"Reply with 'y' to approve or 'n' to reject | ID: {message.id}")
                
                # Add to pending queue
                pending_data = load_pending()
                pending_data["pending"].append({
                    "message_id": str(message.id),
                    "message_data": message_data
                })
                save_pending(pending_data)
                
                await approval_channel.send(embed=embed)
                print(f"Sent message {message.id} for approval")
            else:
                print(f"Could not find approval channel with ID: {APPROVAL_CHANNEL_ID}")
        else:
            print("No approval channel set, adding message directly")
            add_message_to_storage(message_data)
    
    # Process commands
    await bot.process_commands(message)

async def handle_approval_response(message):
    # Get the original message ID from the referenced message
    if not message.reference or not message.reference.message_id:
        return
    
    original_msg = await message.channel.fetch_message(message.reference.message_id)
    if not original_msg or not original_msg.embeds:
        return
    
    # Extract message ID from footer
    footer_text = original_msg.embeds[0].footer.text
    message_id = footer_text.split("ID: ")[1] if "ID: " in footer_text else None
    
    if not message_id:
        return
    
    # Check if this is an approval (y) or rejection (n)
    response = message.content.lower().strip()
    if response not in ['y', 'n']:
        return
    
    # Load pending messages
    pending_data = load_pending()
    
    # Find the message in pending
    message_index = None
    pending_message = None
    for i, pending_msg in enumerate(pending_data["pending"]):
        if pending_msg["message_id"] == message_id:
            message_index = i
            pending_message = pending_msg
            break
    
    if message_index is None:
        await message.channel.send("Could not find this message in pending queue.")
        return
    
    # Remove from pending
    pending_data["pending"].pop(message_index)
    save_pending(pending_data)
    
    if response == 'y':
        # Approve: add to messages
        add_message_to_storage(pending_message["message_data"])
        await message.channel.send(f"✅ Message approved and added to website.")
        print(f"Approved message {message_id}")
    else:
        await message.channel.send(f"❌ Message rejected and discarded.")
        print(f"Rejected message {message_id}")

def add_message_to_storage(message_data):
    # Load existing messages
    messages_data = load_messages()
    
    # Ensure the channels structure exists
    if "channels" not in messages_data:
        messages_data["channels"] = {}
    
    # Check if channel_id is missing (older message format)
    if "channel_id" not in message_data:
        # Error handling - we need to skip this message as we can't determine where to store it
        print(f"Error: Message is missing channel_id field. Skipping message {message_data.get('id', 'unknown')}.")
        return
        
    # Create channel entry if it doesn't exist
    channel_id = message_data["channel_id"]
    if channel_id not in messages_data["channels"]:
        messages_data["channels"][channel_id] = {
            "name": message_data["channel_name"],
            "category": str(message_data.get("category", "None")),
            "messages": []
        }
    
    # Add message to storage
    messages_data["channels"][channel_id]["messages"].append(message_data)
    
    # Get all messages from all channels
    all_messages = []
    for channel_id, channel in messages_data["channels"].items():
        channel_name = channel.get("name", "Unknown")
        messages_with_metadata = []
        
        # Process each message in the channel to ensure it has required fields
        for msg in channel["messages"]:
            # Ensure message has channel_id and channel_name
            if "channel_id" not in msg:
                msg["channel_id"] = channel_id
            if "channel_name" not in msg:
                msg["channel_name"] = channel_name
            
            # Add to the collection with channel name
            messages_with_metadata.append((msg, channel_name))
        
        # Add this channel's messages to the overall list
        all_messages.extend(messages_with_metadata)
    
    # Sort all messages by timestamp (newest first)
    all_messages.sort(key=lambda x: x[0]["timestamp"], reverse=True)
    
    # Keep only the 4 most recent messages
    if len(all_messages) > 4:
        # Reset the structure
        new_channels = {}
        
        # Keep only the 4 most recent messages
        for msg, channel_name in all_messages[:4]:
            # Ensure the message has channel_id
            channel_id = msg["channel_id"]
            
            # Create channel if it doesn't exist in new structure
            if channel_id not in new_channels:
                new_channels[channel_id] = {
                    "name": msg["channel_name"],
                    "category": messages_data["channels"].get(channel_id, {}).get("category", "None"),
                    "messages": []
                }
            
            # Add the message to the channel
            new_channels[channel_id]["messages"].append(msg)
        
        # Replace the channels with the new structure
        messages_data["channels"] = new_channels
    
    # Save updated messages
    save_messages(messages_data)
    print(f"Saved message. Storage now contains {sum(len(c['messages']) for c in messages_data['channels'].values())} messages total.")

@bot.command(name='status')
async def status(ctx):
    """Reports the bot's status and message count"""
    messages_data = load_messages()
    channel_count = len(messages_data["channels"])
    message_count = sum(len(channel["messages"]) for channel in messages_data["channels"].values())
    
    # Get pending count
    pending_data = load_pending()
    pending_count = len(pending_data["pending"])
    
    await ctx.send(f"Bot is running! Monitoring {channel_count} channels with {message_count} messages stored. {pending_count} messages pending approval.")

@bot.command(name='approveall')
async def approve_all(ctx):
    """Approve all pending messages (moderators only)"""
    # Check if the user is a moderator
    if ctx.author.id not in MODERATOR_IDS:
        await ctx.send("You don't have permission to use this command.")
        return
    
    pending_data = load_pending()
    count = len(pending_data["pending"])
    
    if count == 0:
        await ctx.send("No pending messages to approve.")
        return
    
    # Approve all pending messages
    for pending_msg in pending_data["pending"]:
        add_message_to_storage(pending_msg["message_data"])
    
    # Clear pending queue
    pending_data["pending"] = []
    save_pending(pending_data)
    
    await ctx.send(f"✅ Approved all {count} pending messages.")

# Run the bot
if __name__ == "__main__":
    print("Starting Discord bot...")
    bot.run(TOKEN) 
import json
import discord
from discord import app_commands
from typing import Optional
from trackers import SessionTracker


with open("config.json") as f:
    config = json.load(f)
    BOT_TOKEN = config["token"]
    SERVER_ID = int(config["guildId"])

intents = discord.Intents.default()
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

session_tracker = None

# /session_start
@tree.command(
    name="session_begin",
    description="Start the session and activate the trackers",
    guild=discord.Object(id=SERVER_ID)
)
@app_commands.describe(starting_fear="Initial number of Fear tokens")
async def session_begin(interaction: discord.Interaction, starting_fear: Optional[int]=None):
    global session_tracker
    if session_tracker is None:
        if starting_fear is None or isinstance(starting_fear, int) and starting_fear >= 0:
            session_tracker = SessionTracker(starting_fear=(starting_fear or 2))
            await session_tracker.message_init(interaction=interaction)
        else:
            await interaction.response.send_message(content="starting_fear must be a positive integer", ephemeral=True)
    else:
        await interaction.response.send_message(content="Session already ongoing, end it before starting another", ephemeral=True)

# /session_end
@tree.command(
    name="session_end",
    description="End an ongoing session",
    guild=discord.Object(id=SERVER_ID)
)
async def session_end(interaction: discord.Interaction):
    global session_tracker
    if session_tracker is not None:
        await session_tracker.end_session()
        session_tracker = None
        await interaction.response.send_message(content="Session ended", ephemeral=True)
    else:
        await interaction.response.send_message(content="No ongoing session", ephemeral=True)
                                
# update trackers when reacted to
@client.event
async def on_reaction_add(reaction, user):
    global session_tracker
    if session_tracker is not None:
        if reaction.message.id == session_tracker.get_id() and user.id != client.user.id:
            await session_tracker.reaction_added(reaction=reaction, user=user)
        elif session_tracker.in_combat() and reaction.message.id == session_tracker.get_combat_id() and user.id != client.user.id:
            await session_tracker.combat_tracker.reaction_added(reaction=reaction, user=user)
        if not session_tracker.active:
            session_tracker = None

# update trackers when reaction is removed
@client.event
async def on_reaction_remove(reaction, user):
    global session_tracker
    if session_tracker is not None:
        if reaction.message.id == session_tracker.get_id() and user.id != client.user.id:
            await session_tracker.reaction_removed(reaction=reaction, user=user)

# sync commands to discord
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print("Trackerheart is ready to go!")

client.run(BOT_TOKEN)
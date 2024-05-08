import discord
from discord import app_commands
from typing import Optional
from trackers import SessionTracker

BOT_TOKEN = "MTIzNzI0MjM1MzMwODI3NDgzMA.Gn5pPB.TYOqRtUmMVG6-lF3vIsHJ0R2Y41psLi0_z6K4k"
SERVER_ID = 1237261986916597772

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

trackers = []
session_tracker = None

# sync commands to discord
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print("Trackerheart is ready to go!")

'''
# /action_tracker
@tree.command(
    name="action_tracker",
    description="Begin tracking Action Tokens",
    guild=discord.Object(id=SERVER_ID)
)
@app_commands.describe(starting_val="Initial number of tokens in the tracker")
async def action_tracker(interaction: discord.Interaction, starting_val: Optional[int]=None):
    tracker = ActionTracker(starting_val=(starting_val or 0))
    await tracker.message_init(interaction=interaction)
    trackers.append(tracker)

# /fear_tracker
@tree.command(
    name="fear_tracker",
    description="Begin tracking Fear Tokens",
    guild=discord.Object(id=SERVER_ID)
)
@app_commands.describe(starting_val="Initial number of tokens in the tracker")
async def fear_tracker(interaction: discord.Interaction, starting_val: Optional[int]=None):
    tracker = FearTracker(starting_val=(starting_val or 0))
    await tracker.message_init(interaction=interaction)
    trackers.append(tracker)
'''

# /session_start
@tree.command(
    name="session_start",
    description="Start the session and activate the trackers",
    guild=discord.Object(id=SERVER_ID)
)
@app_commands.describe(starting_fear="Initial number of Fear tokens")
async def session_start(interaction: discord.Interaction, starting_fear: Optional[int]=None):
    global session_tracker
    if session_tracker is None:
        session_tracker = SessionTracker(starting_fear=(starting_fear or 0))
        await session_tracker.message_init(interaction=interaction)
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
    else:
        await interaction.response.send_message(content="No ongoing session", ephemeral=True)
                                
# update trackers when reacted to
@client.event
async def on_reaction_add(reaction, user):
    '''
    global trackers
    for tracker in trackers:
        if reaction.message.id == tracker.get_id() and user.id != client.user.id:
            await tracker.reaction_added(reaction=reaction, user=user)
    trackers = [tracker for tracker in trackers if tracker.active]
    '''
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

client.run(BOT_TOKEN)
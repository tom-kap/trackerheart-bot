import json
import discord
import re # regex
from discord.ext import tasks
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


# /timer_start
@tree.command(
    name="create_timer",
    description="Create a timer",
    guild=discord.Object(id=SERVER_ID)
)
@app_commands.describe(timer_name="name of timer")
@app_commands.describe(starting_time="Initial number of timer tokens")
async def create_timer(interaction: discord.Interaction, timer_name: Optional[str]=None, starting_time: Optional[int]=0):
    global session_tracker
    if session_tracker is None:
         await interaction.response.send_message(content="You must start a session first", ephemeral=True)
    elif timer_name is None:
        await interaction.response.send_message(content="Please provide a timer name.", ephemeral=True)
    elif (isinstance(starting_time, int) and starting_time >= 0):
            await session_tracker.create_timer(timer_name,starting_time, interaction)
    else:
        await interaction.response.send_message(content="starting_time must be a positive integer", ephemeral=True)


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
    try:
        global session_tracker
        if session_tracker is not None:
            if reaction.message.id == session_tracker.get_id() and user.id != client.user.id:
                await session_tracker.reaction_added(reaction=reaction, user=user)
            elif session_tracker.in_combat() and reaction.message.id == session_tracker.get_combat_id() and user.id != client.user.id:
                await session_tracker.combat_tracker.reaction_added(reaction=reaction, user=user)
            elif session_tracker.in_timer() and session_tracker.is_timer_id(reaction.message.id) and user.id != client.user.id:
                timer_tracker = session_tracker.get_timer_tracker(reaction.message.id)
                await timer_tracker.reaction_added(reaction=reaction, user=user)
            if not session_tracker.active:
                session_tracker = None
    
    except discord.errors.HTTPException as e:
        # Sometimes communcation with discord through the webhook(s) fails. 
        print(f"Caught an HTTP exception: Status code {e.status}")
        print(f"Error text: {e.text}")
        
    
# update trackers when reaction is removed
@client.event
async def on_reaction_remove(reaction, user):
    try:
        global session_tracker
        if session_tracker is not None:
            if reaction.message.id == session_tracker.get_id() and user.id != client.user.id:
                await session_tracker.reaction_removed(reaction=reaction, user=user)
    except discord.errors.HTTPException as e:
        # Sometimes communcation with discord through the webhook(s) fails. 
        print(f"Caught an HTTP exception: Status code {e.status}")
        print(f"Error text: {e.text}")
        
    
# sync commands to discord
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print("Trackerheart is ready to go!")
    if not heartbeat.is_running():
        print("Calling heartbeat starter")
        await heartbeat.start()


@tasks.loop(minutes=1)
async def heartbeat():
    # You can perform any activity here to ensure the bot stays active.
    await client.change_presence(activity=discord.Game(name="Daggerheart"))

@heartbeat.before_loop
async def before_heartbeat():
    await client.wait_until_ready()
    print('Heartbeat task is starting...')


client.run(BOT_TOKEN)
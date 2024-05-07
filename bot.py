import discord
from discord import app_commands

BOT_TOKEN = "MTIzNzI0MjM1MzMwODI3NDgzMA.Gn5pPB.TYOqRtUmMVG6-lF3vIsHJ0R2Y41psLi0_z6K4k"
SERVER_ID = 1237261986916597772

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

actions = 0
fear = 0

# /track 
@tree.command(
    name="track",
    description="Begin tracking Fear or Action Tokens",
    guild=discord.Object(id=SERVER_ID)
)
async def track(interaction: discord.Interaction):
    title = f"Action Tracker: {actions}"
    tracker = " ".join([":zap:"]*actions)
    embed = discord.Embed(title=title)
    embed.add_field(name="\u200b", value = tracker)
    await interaction.response.send_message("Tracker will go here", embed=embed)

# sync commands to discord
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print("Trackerheart is ready to go!")

client.run(BOT_TOKEN)
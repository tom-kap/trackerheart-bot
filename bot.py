import discord
from discord import app_commands
from typing import Optional

BOT_TOKEN = "MTIzNzI0MjM1MzMwODI3NDgzMA.Gn5pPB.TYOqRtUmMVG6-lF3vIsHJ0R2Y41psLi0_z6K4k"
SERVER_ID = 1237261986916597772

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# TRACKER CLASSES
class TrackerModel:
    def __init__(self, type, emoji, starting_val: int =0):
        self.type = type
        self.emoji = emoji    
        self.tracker = starting_val

    def tick_up(self):
        self.tracker = self.tracker + 1
    
    def tick_down(self):
        self.tracker = max(self.tracker - 1, 0)

    def set(self, amount: int):
        self.tracker = max(amount, 0)

    def gen_embed(self):
        embed = discord.Embed(title=f"{self.type} Tracker: {self.tracker}")
        embed.add_field(name="\u200b", value = " ".join([self.emoji]*self.tracker))
        return embed


class ActionTracker():
    reactions = {
        "up": "⬆️",
        "down": "⬇️",
        "close": "❌"
    }

    def __init__(self, starting_val: int=0):
        self.model = TrackerModel(type="Action", emoji="⚡", starting_val=starting_val)
        self.ended = False

    async def message_init(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.model.gen_embed())
        self.message = await interaction.original_response()
        await self.message.add_reaction(self.reactions["up"])
        await self.message.add_reaction(self.reactions["down"])
        await self.message.add_reaction(self.reactions["close"])
    
    async def update(self):
        if  self.message:
            embed = self.model.gen_embed()
            if self.ended:
                embed.add_field(name="\u200b", value = "Tracker ended")
            await self.message.edit(embed=embed)
        else:
            raise RuntimeError("Message was not initialized. Please call message_init() immediately after creating a tracker!")
    
    async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
        emoji = reaction.emoji
        if emoji == self.reactions.get("up"):
            self.model.tick_up()
            await reaction.remove(user)
        elif emoji == self.reactions.get("down"):
                self.model.tick_down()
                await reaction.remove(user)
        elif emoji == self.reactions.get("close"):
                self.ended = True
                await self.message.clear_reactions()
        await self.update()
                
    def get_id(self):
        if (self.message):
            return self.message.id
        else:
            raise RuntimeError("Message was not initialized. Please call message_init() immediately after creating a tracker!")


trackers = []

# sync commands to discord
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print("Trackerheart is ready to go!")

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
                            
# update trackers when reacted to
@client.event
async def on_reaction_add(reaction, user):
    global trackers
    for tracker in trackers:
        if reaction.message.id == tracker.get_id() and user.id != client.user.id:
            await tracker.reaction_added(reaction=reaction, user=user)
    trackers = [tracker for tracker in trackers if not tracker.ended]
    
client.run(BOT_TOKEN)
import discord
from discord import app_commands
from typing import Optional
from abc import ABC, abstractmethod

BOT_TOKEN = "MTIzNzI0MjM1MzMwODI3NDgzMA.Gn5pPB.TYOqRtUmMVG6-lF3vIsHJ0R2Y41psLi0_z6K4k"
SERVER_ID = 1237261986916597772

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# TRACKER CLASSES
class TrackerModel:
    def __init__(self, starting_val: int =0):  
        self.tracker = starting_val

    def tick_up(self, amount=1):
        self.tracker = self.tracker + amount
    
    def tick_down(self, amount=1):
        self.tracker = max(self.tracker - amount, 0)


class Tracker(ABC):
    # name: str; specifies the name of this tracker type (e.g Action Tracker)
    @property
    @abstractmethod
    def name(self):
        pass

    # emojis: Dict[str, str]; maps different functions to emojis
    # must include emojis for 'token', 'add', 'remove', and 'end'
    @property
    @abstractmethod
    def emojis(self):
        pass
    
    # initialize variables
    def __init__(self, starting_val: int=0):
        self.model = TrackerModel(starting_val=starting_val)
        self.ended = False

    # initializes and sends out the tracker message
    # must be called after initializing
    async def message_init(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.gen_embed())
        self.message = await interaction.original_response()
        await self.message.add_reaction(self.emojis["add"])
        await self.message.add_reaction(self.emojis["remove"])
        await self.message.add_reaction(self.emojis["end"])

    # update tracker message with new embed
    async def update(self):
        if  self.message:
            embed = self.gen_embed()
            if self.ended:
                embed.add_field(name="\u200b", value = "Tracker ended")
            await self.message.edit(embed=embed)
        else:
            self.ended = True
            raise RuntimeError("Message deleted or not initialized. Please call message_init() immediately after creating a tracker!")
    
    # updates model based on discord reactions
    async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
        if not self.ended:
            emoji = reaction.emoji
            if emoji == self.emojis["add"]:
                self.model.tick_up()
                await reaction.remove(user)
            elif emoji == self.emojis["remove"]:
                    self.model.tick_down()
                    await reaction.remove(user)
            elif emoji == self.emojis["end"]:
                    self.ended = True
                    await self.message.clear_reactions()
            await self.update()

    # get tracker message id
    def get_id(self):
        if (self.message):
            return self.message.id
        else:
            self.ended = True
            raise RuntimeError("Message was deleted or not initialized. Please call message_init() immediately after creating a tracker!")
    
    # creates an embed representing the current state of the tracker
    def gen_embed(self):
        embed = discord.Embed(title=f"{self.name} ({self.model.tracker})")
        embed.add_field(name="\u200b", value = " ".join([self.emojis["token"]]*self.model.tracker))
        return embed


class ActionTracker(Tracker):
    name = "Action Tracker"
    
    emojis = {
        "token": "⚡",
        "add": "⬆️",
        "remove": "⬇️",
        "add2": "⏫",
        "remove2": "⏬",
        "end": "❌"
    }

    # initializes and sends out the tracker message
    # must be called after initializing
    async def message_init(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.gen_embed())
        self.message = await interaction.original_response()
        await self.message.add_reaction(self.emojis["add"])
        await self.message.add_reaction(self.emojis["remove"])
        await self.message.add_reaction(self.emojis["add2"])
        await self.message.add_reaction(self.emojis["remove2"])
        await self.message.add_reaction(self.emojis["end"])

    # updates model based on discord reactions
    async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
        if not self.ended:
            emoji = reaction.emoji
            if emoji == self.emojis["add2"]:
                self.model.tick_up(amount=2)
                await reaction.remove(user)
            elif emoji == self.emojis["remove2"]:
                self.model.tick_down(amount=2)
                await reaction.remove(user)
            await super().reaction_added(reaction, user)
            
    
class FearTracker(Tracker):
    name = "Fear Tokens"
    
    emojis = {
        "token": "💀",
        "add": "⬆️",
        "remove": "⬇️",
        "end": "❌"
    }

    # creates an embed representing the current state of the tracker
    def gen_embed(self):
        embed = super().gen_embed()
        embed.add_field(
            name="Spending Fear",
            value="When you spend fear, you can:\n* Interrupt the PCs during combat to take an action.\n* Add two tokens to the action tracker.\n* Use an adversary's fear move.\n* Use an environment move.",
            inline=False
        )
        return embed
                

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
                            
# update trackers when reacted to
@client.event
async def on_reaction_add(reaction, user):
    global trackers
    for tracker in trackers:
        if reaction.message.id == tracker.get_id() and user.id != client.user.id:
            await tracker.reaction_added(reaction=reaction, user=user)
    trackers = [tracker for tracker in trackers if not tracker.ended]
    
client.run(BOT_TOKEN)
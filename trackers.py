import discord
from abc import ABC, abstractmethod

# TRACKER CLASSES
class TrackerModel:
    def __init__(self, starting_val: int =0):  
        self.num_tokens = starting_val

    def tick_up(self, amount=1):
        self.num_tokens = self.num_tokens + amount
    
    def tick_down(self, amount=1):
        self.num_tokens = max(self.num_tokens - amount, 0)

    def reset(self):
        self.num_tokens = 0


class Tracker(ABC):
    # name: str; specifies the name of this tracker type (e.g Action Tracker)
    @property
    @abstractmethod
    def name(self):
        pass

    # token: str; the emoji that represents the token
    @property
    @abstractmethod
    def token (self):
        pass

    # buttons: Dict[str, str]; maps different functions to emojis
    # must include emojis for 'add', 'remove', and 'end'
    @property
    @abstractmethod
    def buttons (self):
        pass
    
    # initialize variables
    def __init__(self, starting_val: int=0):
        self.model = TrackerModel(starting_val=starting_val)
        self.active = False
        self.reactions = False

    # initializes and sends out the tracker message
    # must be called after initializing
    async def message_init(self, interaction: discord.Interaction, start_active=True):
        await interaction.response.send_message(embed=self.gen_embed())
        self.message = await interaction.original_response()
        self.active = start_active
        if self.active:
            await self.set_reactions()
        
    # set reactions on message
    async def set_reactions(self):
        for button in self.buttons:
            await self.message.add_reaction(self.buttons[button])
        self.reactions = True

    async def reset_reactions(self):
        await self.message.clear_reactions()
        self.reactions = False


    # update tracker message with new embed
    async def update(self):
        if self.message is not None:
            embed = self.gen_embed()
            await self.message.edit(embed=embed)
            if self.active and not self.reactions:
                await self.set_reactions()
            elif not self.active and self.reactions:
                await self.reset_reactions()
        else:
            self.session.active = False

    # get tracker message id
    def get_id(self):
        if (self.message):
            return self.message.id
        else:
            raise RuntimeError("Message was deleted or not initialized. Please call message_init() immediately after creating a tracker!")
    
    # creates an embed representing the current state of the tracker
    def gen_embed(self, colour=discord.Colour.default):
        embed = discord.Embed(title=f"{self.name} ({self.model.num_tokens})", colour=colour)
        embed.add_field(name="\u200b", value = " ".join([self.token]*self.model.num_tokens))
        return embed


class ActionTracker(Tracker):
    name = "Action Tracker"
    
    token = "⚡"

    buttons  = {
        "add": "⬆️",
        "remove": "⬇️",
        "add2": "⏫",
        "remove2": "⏬",
        "end": "❌"
    }

    # updates model based on discord reactions
    async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
        if self.active:
            emoji = reaction.emoji
            if emoji == self.buttons["add2"]:
                self.model.tick_up(amount=2)
                await reaction.remove(user)
            elif emoji == self.buttons["remove2"]:
                self.model.tick_down(amount=2)
                await reaction.remove(user)
            elif emoji == self.buttons["add"]:
                self.model.tick_up()
                await reaction.remove(user)
            elif emoji == self.buttons["remove"]:
                    self.model.tick_down()
                    await reaction.remove(user)
            elif emoji == self.buttons["end"]:
                    self.active = False
        await self.update()
            
    
class FearTracker(Tracker):
    name = "Fear Tokens"
    
    token = "💀"

    buttons = {
        "add": "⬆️",
        "remove": "⬇️",
        "end": "❌"
    }

    # updates model based on discord reactions
    async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
        if self.active:
            emoji = reaction.emoji
            if emoji == self.buttons["add"]:
                self.model.tick_up()
                await reaction.remove(user)
            elif emoji == self.buttons["remove"]:
                    self.model.tick_down()
                    await reaction.remove(user)
            elif emoji == self.buttons["end"]:
                    self.active = False
        await self.update()

    # creates an embed representing the current state of the tracker
    def gen_embed(self):
        embed = super().gen_embed()
        embed.add_field(
            name="Spending Fear",
            value="When you spend fear, you can:\n* Interrupt the PCs during combat to take an action.\n* Add two tokens to the action tracker.\n* Use an adversary's fear move.\n* Use an environment move.",
            inline=False
        )
        return embed


class SessionTracker(Tracker):
    class CombatTracker(Tracker):
        name = "Action Tracker"
        
        token = "⚡"

        buttons = {
            "add": "⬆️",
            "remove": "⬇️",
            "add2": "⚡",
            "remove2": "💀"
        }

        # initialize variables
        def __init__(self, session, starting_val=0):
            self.session = session 
            self.prev_num_tokens: int = None
            super().__init__(starting_val=starting_val)

        async def message_init(self, channel: discord.TextChannel):
            self.message = await channel.send(embed = self.gen_embed())
            self.active = True

        # updates model based on discord reactions
        async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
            if self.active:
                emoji = reaction.emoji
                if emoji == self.buttons["add2"]:
                    if self.session.model.num_tokens >= 1:
                        self.model.tick_up(amount=2)
                        self.session.model.tick_down()
                        await self.session.update()
                    await reaction.remove(user)
                elif emoji == self.buttons["remove2"]:
                    if self.model.num_tokens >= 2:
                        self.model.tick_down(amount=2)
                        self.session.model.tick_up()
                        await self.session.update()
                    await reaction.remove(user)
                elif emoji == self.buttons["add"]:
                    self.model.tick_up()
                    await reaction.remove(user)
                elif emoji == self.buttons["remove"]:
                        self.model.tick_down()
                        await reaction.remove(user)
            await self.update()

        # start combat
        async def start_combat(self):
            if not self.active:
                self.active = True
            await self.update()

        # end combat
        async def end_combat(self):
            if self.active:
                self.active = False
                self.session.model.tick_up(self.model.num_tokens // 2)
                self.prev_num_tokens = self.model.num_tokens
                self.model.reset()
            
            await self.update()

        # creates an embed representing the current state of the tracker
        def gen_embed(self):
            colour = discord.Colour.red()
            if self.active:
                return super().gen_embed(colour=colour)
            else:
                embed = discord.Embed(title=f"{self.name}", colour=colour)
                if self.prev_num_tokens is not None:
                    embed.add_field(name="Out of Combat", value=f"Last combat ended with {self.prev_num_tokens} action tokens left on the tracker.")
                else:
                    embed.add_field(name="Out of Combat", value="\u200b")
                return embed

    

    name = "Fear Tokens"

    token = "💀"

    buttons = {
        "add": "⬆️",
        "remove": "⬇️",
        "combat": "⚔️"
    }

    # initialize variables
    def __init__(self, starting_fear=0):
        super().__init__(starting_val=starting_fear)
    
    # initializes and sends out the tracker message
    # must be called after initializing
    async def message_init(self, interaction: discord.Interaction):
        self.active = True
        await interaction.response.send_message(embed=self.gen_embed())
        self.message = await interaction.original_response()

        self.combat_tracker = SessionTracker.CombatTracker(session=self)
        await self.combat_tracker.message_init(channel=self.message.channel)

        await self.set_reactions()

    # updates model based on discord reactions
    async def reaction_added(self, reaction: discord.Reaction, user: discord.User):
        if self.active:
            emoji = reaction.emoji
            if emoji == self.buttons["add"]:
                self.model.tick_up()
                await reaction.remove(user)
            elif emoji == self.buttons["remove"]:
                self.model.tick_down()
                await reaction.remove(user)
            elif emoji == self.buttons["combat"]:
                await self.combat_tracker.start_combat()
        await self.update()
            
    # updates model when a reaction is removed
    async def reaction_removed(self, reaction: discord.Reaction, user: discord.User):
        if self.active:
            emoji = reaction.emoji
            if emoji == self.buttons["combat"]:
                await self.combat_tracker.end_combat()
        await self.update()

    async def end_session(self):
        await self.combat_tracker.end_combat()
        self.active = False

    def in_combat(self):
        return self.combat_tracker.active

    def get_combat_id(self):
        return self.combat_tracker.get_id()
        
    # creates an embed representing the current state of the tracker
    def gen_embed(self):
        embed = super().gen_embed(colour=discord.Colour.blurple())
        if not self.active:
            embed.add_field(name="\u200b", value="Session over", inline=False)
        return embed

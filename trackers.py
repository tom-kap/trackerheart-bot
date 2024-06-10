import discord
from abc import ABC, abstractmethod

# TRACKER CLASSES
class TrackerModel:
    def __init__(self, starting_val=0, max_val=100):  
        self.num_tokens = min(starting_val, max_val)
        self.max = max_val
    def tick_up(self, amount=1):
        self.num_tokens = min(self.max, self.num_tokens + amount)
    
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
    def __init__(self, starting_val=0, max_val=100):
        self.model = TrackerModel(starting_val=starting_val, max_val=max_val)
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


class SessionTracker(Tracker):
    class TimerTracker(Tracker):
        name = "Timer"
        
        token = "⏳"
        # t1 = timer1, idea is to allow multiple timers i.e. an enemy battle timer & a long rest project timer.
        buttons = {
            "add": "⬆️",
            "remove": "⬇️",
            "add5": "⏏️",
            "clear": "0️⃣",
            "loop": "🔁",
            "stop": "⏹️"
        }
        # init vars
        def __init__(self, session,tname,stime=0):
            self.session = session 
            self.name = tname
            self.tokens = stime
            self.init_tokens = stime
            # for compadability with abstract class
            self.prev_num_tokens: int = None
            super().__init__(starting_val=stime)


        async def message_init(self, interaction: discord.Interaction):
            self.active = True
            await interaction.response.send_message("Starting timer...",ephemeral=True)
            self.message = await interaction.channel.send(embed = self.gen_embed())
            
            await self.set_reactions()

        async def reaction_added(self, reaction: discord.Reaction, user: discord.User):    
            if self.active:
                emoji = reaction.emoji
              
                match(emoji):
                    case "⬆️":
                        if self.session.model.num_tokens <= 20:
                            self.model.tick_up()
                        await reaction.remove(user)
                    case "⏏️":
                        if self.session.model.num_tokens <= 20:
                            for i in range(0,5):
                                self.model.tick_up()
                        await reaction.remove(user)
                    case "0️⃣":
                        if self.model.num_tokens > 0:
                            self.model.reset()
                        await reaction.remove(user)
                    case "⬇️":
                        if self.model.num_tokens > 0:
                            self.model.tick_down()
                        await reaction.remove(user)
                    case "🔁":
                        self.model.num_tokens = self.init_tokens
                        await reaction.remove(user)
                    case "⏹️":
                        await reaction.remove(user)
                        await self.end_timer()
                    case _:
                        print("Caseless reaction")
            await self.update()    

        # creates an embed representing the current state of the tracker
        def gen_embed(self):
            colour = discord.Colour.dark_orange()
            if self.active:
                return super().gen_embed(colour=colour)
            else:
                embed = discord.Embed(title=f"Timer {self.name}", colour=colour)
                embed.add_field(name=f"Timer {self.name}", value=f"Timer Stopped")
                return embed
            
        # start timer
        async def start_timer(self):
            if not self.active:
                self.active = True
            await self.update()

        # end combat
        async def end_timer(self):
            if self.active:
                self.active = False
                self.session.remove_timer((self.name))
                self.model.reset()
            await self.update()


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
        "combat": "⚔️",
        "combat": "⚔️",
    }

    # initialize variables
    def __init__(self, starting_fear):
        super().__init__(starting_val=starting_fear, max_val=6)
    
    # initializes and sends out the tracker message
    # must be called after initializing
    async def message_init(self, interaction: discord.Interaction):
        self.active = True
        await interaction.response.send_message("Starting tracker...",ephemeral=True)
        self.message = await interaction.channel.send(embed = self.gen_embed())

        self.combat_tracker = SessionTracker.CombatTracker(session=self)
        await self.combat_tracker.message_init(channel=self.message.channel)

        # dictionary to store timer
        self.timers = {}
        

        # dictionary to store timer
        self.timers = {}
        
        await self.set_reactions()
        
    async def create_timer(self, timer_name, starting_time, interaction: discord.Interaction):
        # if timer name is not unique
        if timer_name in self.timers:
            await interaction.response.send_message(content="timer name is already in use, please pick another", ephemeral=True)
        else:
            self.timers[timer_name] = SessionTracker.TimerTracker(session=self,tname=timer_name,stime=starting_time)
            await (self.timers[timer_name]).message_init(interaction)

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
        await self.update()

    def in_combat(self):
        return self.combat_tracker.active

    def get_combat_id(self):
        return self.combat_tracker.get_id()
    
    def in_timer(self):
        for t in self.timers:
            t = self.timers[t]
            if t.active == True:
                return True
        return False

    def is_timer_id(self, msg_id):
        for t in self.timers:
            t = self.timers[t]
            if t.active == True and t.get_id() == msg_id:
                return True
        return False
    
    def get_timer_tracker(self,msg_id):
        for t in self.timers:
            t = self.timers[t]
            if t.active == True and t.get_id() == msg_id:
                return t
    
    def remove_timer(self,tname):
        if tname in self.timers:
            del self.timers[tname]
         
    
    def in_timer(self):
        for t in self.timers:
            t = self.timers[t]
            if t.active == True:
                return True
        return False

    def is_timer_id(self, msg_id):
        for t in self.timers:
            t = self.timers[t]
            if t.active == True and t.get_id() == msg_id:
                return True
        return False
    
    def get_timer_tracker(self,msg_id):
        for t in self.timers:
            t = self.timers[t]
            if t.active == True and t.get_id() == msg_id:
                return t
    
    def remove_timer(self,tname):
        if tname in self.timers:
            del self.timers[tname]
         
    # creates an embed representing the current state of the tracker
    def gen_embed(self):
        embed = super().gen_embed(colour=discord.Colour.blurple())
        if not self.active:
            embed.add_field(name="\u200b", value="Session over", inline=False)
        return embed
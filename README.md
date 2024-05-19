# Trackerheart
This bot is intended to help track fear and action tokens for the Daggerheart tabletop role-playing game system.

### Demo
[![Demo video](https://img.youtube.com/vi/jGKoqW8o6iM/0.jpg)](https://www.youtube.com/watch?v=jGKoqW8o6iM)

### Dependencies
Running this bot requires:
* [python](https://www.python.org/) (3.8 or higher)
* [discord.py](https://discordpy.readthedocs.io/en/stable/) 
    * Can be installed using pip, e.g `pip install discord.py`

## Setup
* Follow [this](https://discordpy.readthedocs.io/en/stable/discord.html) guide to create the bot and add it to your server.
* Make sure to grant it the "bot" and "applications.commands" scopes as well as the following permissions:
    * Send Messages
    * Manage Messages
    * Add Reactions
    * Use Slash Commands
* Enable "server members intent" in the Bot tab as well.
* Add your bot's secret token into the config.json file. Make sure to never share your bot's token publically.
* Add your server's id into the config.json file.
    * You can find your server id by enabling developer mode in your discord settings, right-clicking the server's icon, and selecting 'Copy Server ID'.
* Your bot should be ready to run now!

## Running the Bot
* Running the bot.py file will boot up the bot. You can run it in the terminal by using `python bot.py`
* You should see that the bot is now online in discord and ready to accept slash commands!

## Using the Bot
* `/session_start` => Begins the tracker.
    * `starting_fear` is an optional argument that allows you to specify how much fear to start the session with.
* `/session_end` => Ends the tracker.
* `/create_timer` => Creates a timer
    * `timer_name` Required argument to specify a name for the timer
        * You can have multiple timers, but each must have an unique name
    * `starting_time` Required argument to specify how many tokens the timer starts with.
* Currently, this bot only supports tracking one session at a time.
### Fear Tracker
* React with ⬆️ to add a fear token.
* React with ⬇️ to remove a fear token.
* React with ⚔️ to begin the Action Tracker for combat.
    * Removing this reaction will end the combat and automatically convert half of the remaining action tokens to fear.
### Action Tracker
* React with ⬆️ to add an action token.
* React with ⬇️ to remove an action token.
* React with ⚡ to automatically convert 1 fear token into 2 action tokens.
* React with 💀 to automatically convert 2 action tokens into 1 fear token.
### Timer Tracker
* React with ⬆️ to add a time token.
* React with ⬇️ to remove a time token.
* React with ⏏️ to add 5 time tokens.
* React with 0️⃣ to clear all time tokens.
* React with 🔁 to reset tracker to the starting amount of time tokens specified in `/create_timer`.
* React with ⏹️ to stop/remove time tracker(this deletes the given time tracker from the bot).
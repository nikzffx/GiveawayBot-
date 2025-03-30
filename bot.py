import os
import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class GiveawayBot(commands.Bot):
    def __init__(self):
        # IMPORTANT: Read from environment if we should disable privileged intents
        # This allows the bot to start without privileged intents if needed
        disable_privileged_intents = os.getenv("DISABLE_PRIVILEGED_INTENTS", "false").lower() == "true"
        
        # Create default intents with minimal privileges
        intents = discord.Intents.default()
        
        # No need for reaction intents as we've moved to button-based interactions
        
        # Add privileged intents only if not disabled
        # These require enabling in the Discord Developer Portal
        if not disable_privileged_intents:
            logger.info("Enabling privileged intents (message_content and members)")
            # If these fail, the bot will still run with limited functionality
            try:
                intents.message_content = True  # Requires Message Content Intent
            except Exception as e:
                logger.warning(f"Unable to enable message_content intent: {e}")
                
            try:
                intents.members = True  # Requires Server Members Intent
            except Exception as e:
                logger.warning(f"Unable to enable members intent: {e}")
        else:
            logger.warning("Running with privileged intents DISABLED. Some features may not work!")
            logger.warning("To enable all features, remove DISABLE_PRIVILEGED_INTENTS=true from environment")
            logger.warning("and enable the intents in Discord Developer Portal")
        
        super().__init__(
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="A Discord bot for managing giveaways"
        )
        
        # Add our cogs
        self.initial_extensions = [
            'cogs.giveaway'
        ]
        
        # Prepare for slash commands
        self.tree_sync_guilds = []
    
    async def setup_hook(self):
        """Setup hook that gets called when the bot is first connecting"""
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
    
    async def on_ready(self):
        """Event triggered when the bot is ready and connected to Discord"""
        logger.info(f"{self.user.name} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for giveaways | /giveaway"
            )
        )
        
        # Sync application commands with Discord
        try:
            # Store current guilds for syncing
            self.tree_sync_guilds = [guild.id for guild in self.guilds]
            
            # Sync commands globally (may take up to an hour to propagate)
            logger.info("Syncing slash commands globally...")
            await self.tree.sync()
            
            # Sync commands to all guilds immediately
            for guild_id in self.tree_sync_guilds:
                logger.info(f"Syncing slash commands to guild {guild_id}...")
                await self.tree.sync(guild=discord.Object(id=guild_id))
            
            logger.info("Slash commands synced successfully!")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I'm missing permissions to execute this command: {error}")
            return
        
        # Log other errors
        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send(f"An error occurred: {error}")

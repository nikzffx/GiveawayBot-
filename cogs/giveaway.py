import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import asyncio
import random
import datetime
from typing import Dict, Optional, List, Callable, Any, Union
import logging
from utils.time_utils import parse_time, format_time_remaining, create_discord_timestamp, format_end_time

logger = logging.getLogger(__name__)

class GiveawayModal(ui.Modal):
    """Modal form for creating a giveaway"""
    
    # Set the title for the modal
    title: str = "Create a Giveaway"
    
    # Define the text inputs
    duration = ui.TextInput(
        label="Duration",
        placeholder="Ex: 10 minutes, 2h, 1d",
        required=True,
        min_length=1,
        max_length=100
    )
    
    winners_count = ui.TextInput(
        label="Number of Winners",
        placeholder="1",
        required=True,
        default="1",
        min_length=1,
        max_length=3
    )
    
    
    prize = ui.TextInput(
        label="Prize",
        placeholder="What are you giving away?",
        required=True,
        min_length=1,
        max_length=100
    )
    
    description = ui.TextInput(
        label="Description",
        placeholder="Optional details about the giveaway",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    def __init__(self, on_submit_callback: Callable[[discord.Interaction, str, int, str, str], Any]):
        super().__init__()
        self.on_submit_callback = on_submit_callback
    
    async def on_submit(self, interaction: discord.Interaction):
        # Parse the duration and winners count
        duration_str = self.duration.value
        
        try:
            winners = int(self.winners_count.value)
            if winners < 1:
                raise ValueError("Number of winners must be at least 1")
        except ValueError:
            await interaction.response.send_message("❌ Invalid number of winners. Please enter a positive number.", ephemeral=True)
            return
            
        prize_text = self.prize.value
        description_text = self.description.value
        
        # Call the callback to create the giveaway
        await self.on_submit_callback(interaction, duration_str, winners, prize_text, description_text)

class GiveawayButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            #label="Enter Giveaway",
            emoji="🎉", 
            custom_id="enter_giveaway"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Get the message ID from the interaction
        message_id = interaction.message.id
        
        # Get the cog instance (this will be set when the button is created)
        cog = self.view.cog
        
        if message_id in cog.giveaways:
            giveaway = cog.giveaways[message_id]
            
            # Check if giveaway has ended
            if giveaway.is_ended:
                await interaction.response.send_message("This giveaway has already ended!", ephemeral=True)
                return
            
            # Check if user already entered
            if interaction.user.id in giveaway.entries:
                await interaction.response.send_message(f"You have already entered this giveaway!", ephemeral=True)
                return
                
            # Add user to entries
            giveaway.entries.add(interaction.user.id)
            
            # Update the embed with new entries count
            try:
                message = interaction.message
                embed = message.embeds[0]
                
                # Find the entries field and update it
                for i, field in enumerate(embed.fields):
                    if field.name == "Entries":
                        embed.set_field_at(i, name="Entries", value=f"**{giveaway.entries_count}**", inline=True)
                        break
                
                await message.edit(embed=embed)
            except Exception as e:
                logging.error(f"Error updating giveaway embed: {e}")
            
            # Confirm entry
            await interaction.response.send_message(f"✅ You've entered the giveaway for **{giveaway.prize}**!", ephemeral=True)
        else:
            await interaction.response.send_message("Unable to find this giveaway.", ephemeral=True)

class GiveawayView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
        self.add_item(GiveawayButton())


class TutorialButton(ui.Button):
    def __init__(self, label, style=discord.ButtonStyle.primary, disabled=False, custom_id=None, url=None, emoji=None):
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji
        )
        
class TutorialView(ui.View):
    """A view for the giveaway tutorial with navigation buttons"""
    
    def __init__(self, author_id: int, pages: List[discord.Embed], timeout=180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.pages = pages
        self.current_page = 0
        self.update_buttons()
        
    def update_buttons(self):
        # Clear existing buttons
        self.clear_items()
        
        # Add navigation buttons
        if self.current_page > 0:
            previous_button = TutorialButton(
                label="Previous",
                style=discord.ButtonStyle.secondary,
                custom_id=f"tutorial_prev_{self.author_id}",
                emoji="⬅️"
            )
            previous_button.callback = self.previous_page_callback
            self.add_item(previous_button)
            
        # Add next button if not on the last page
        if self.current_page < len(self.pages) - 1:
            next_button = TutorialButton(
                label="Next",
                style=discord.ButtonStyle.primary,
                custom_id=f"tutorial_next_{self.author_id}",
                emoji="➡️"
            )
            next_button.callback = self.next_page_callback
            self.add_item(next_button)
            
        # Add close button
        close_button = TutorialButton(
            label="Close Tutorial",
            style=discord.ButtonStyle.danger,
            custom_id=f"tutorial_close_{self.author_id}",
            emoji="❌"
        )
        close_button.callback = self.close_callback
        self.add_item(close_button)
    
    async def next_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This tutorial is not for you! Use `/tutorial` to start your own.", ephemeral=True)
            return
            
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        
    async def previous_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This tutorial is not for you! Use `/tutorial` to start your own.", ephemeral=True)
            return
            
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
            
    async def close_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This tutorial is not for you! Use `/tutorial` to start your own.", ephemeral=True)
            return
            
        # Disable all buttons
        for item in self.children:
            item.disabled = True
            
        # Edit the message to show disabled buttons
        await interaction.response.edit_message(view=self)
        
        # Then delete the message after a short delay
        await asyncio.sleep(0.5)
        await interaction.message.delete()
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the author to interact with buttons
        return interaction.user.id == self.author_id

class Giveaway:
    def __init__(self, channel_id, message_id, guild_id, creator_id, prize, end_time, winners_count=1):
        self.channel_id = channel_id
        self.message_id = message_id
        self.guild_id = guild_id
        self.creator_id = creator_id
        self.prize = prize
        self.end_time = end_time
        self.winners_count = winners_count
        self.ended = False
        self.winner_ids = []  # Store multiple winner IDs
        self.entries = set()  # Store user IDs who entered via button
        
    @property
    def entries_count(self):
        """Returns the number of entries in the giveaway"""
        return len(self.entries)
    
    @property
    def time_remaining(self) -> float:
        """Returns the time remaining in seconds"""
        if self.ended:
            return 0
        now = datetime.datetime.now().timestamp()
        return max(0, self.end_time - now)
    
    @property
    def is_ended(self) -> bool:
        """Returns True if the giveaway has ended"""
        if self.ended:
            return True
        return self.time_remaining <= 0


class GiveawayCog(commands.Cog):
    """A cog for managing giveaways"""
    
    def __init__(self, bot):
        self.bot = bot
        self.giveaways: Dict[int, Giveaway] = {}  # message_id -> Giveaway
        self.check_giveaways.start()
    
    def cog_unload(self):
        self.check_giveaways.cancel()
    
    async def create_giveaway_from_modal(self, interaction: discord.Interaction, duration_str: str, winners_count: int, prize: str, description: str):
        """Create a giveaway from the modal form submission"""
        try:
            # Parse duration
            try:
                duration_seconds = parse_time(duration_str)
                if duration_seconds <= 0:
                    raise ValueError("Duration must be positive")
            except ValueError as e:
                await interaction.response.send_message(f"❌ Invalid duration format: {e}", ephemeral=True)
                return
                
            end_time = datetime.datetime.now().timestamp() + duration_seconds
            
            # Create the embed for the giveaway
            embed = discord.Embed(
                title="**{prize}**",
                color=0x9BC5E7,
                timestamp=datetime.datetime.fromtimestamp(end_time)
            )
            
            # Add the prize and description
          #  description_text = f"**{prize}**\n\n"
          #  if description:
               # description_text += f"{description}\n\n"
            description_text += f"**Hosted by:** {interaction.user.mention}"
           # embed.description = description_text

            # Add fields for time, winners, and entries
            time_formats = format_end_time(end_time)

            # Display time in a more user-friendly format with multiple formats
            time_value = (
                f"{time_formats['discord_relative']}({time_formats['discord_absolute']})"
            )
            embed.add_field(name="Ends At", value=time_value, inline=False)
            embed.add_field(name="Winners", value=f"**{winners_count}**", inline=True)
            embed.add_field(name="Entries", value="**0**", inline=True)
            
            
            
            # embed.set_footer(text="Click the 🎉 button to enter!")
            
            # Create view with button
            view = GiveawayView(self)
            
            # Send success message that the form was submitted
            await interaction.response.send_message("✅ Creating your giveaway...", ephemeral=True)
            
            # Send the giveaway message to the channel with the view
            giveaway_message = await interaction.channel.send(embed=embed, view=view)
            
            # Create and store the giveaway
            giveaway = Giveaway(
                channel_id=interaction.channel.id,
                message_id=giveaway_message.id,
                guild_id=interaction.guild.id,
                creator_id=interaction.user.id,
                prize=prize,
                end_time=end_time,
                winners_count=winners_count
            )
            self.giveaways[giveaway_message.id] = giveaway
            
            logger.info(f"Created giveaway {giveaway_message.id} in guild {interaction.guild.id}, "
                      f"ends at {datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error creating giveaway from modal: {e}")
            # We already sent a response with the modal submission, can't respond again
            # Just log the error
        
    # Slash Command implementation
    
    @app_commands.command(name="create", description="Create a new giveaway using a form")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_giveaway_create(self, interaction: discord.Interaction):
        """Create a new giveaway using an interactive form
        
        Opens a form where you can specify the giveaway details including:
        - Duration
        - Number of winners
        - Prize
        - Optional detailed description"""
        # Check permissions first
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server", ephemeral=True)
            return
            
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            # Fallback when member cache is not available
            try:
                member = await interaction.guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.response.send_message("❌ Failed to verify your server permissions", ephemeral=True)
                return
                
        if not member.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need Manage Messages permission to start a giveaway", ephemeral=True)
            return
        
        # Send the modal form
        await interaction.response.send_modal(GiveawayModal(self.create_giveaway_from_modal))

    # slash_giveaway_start command removed as requested
            
    @app_commands.command(name="end", description="End a giveaway and pick winner(s)")
    @app_commands.describe(message_id="The ID of the giveaway message")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_giveaway_end(self, interaction: discord.Interaction, message_id: str):
        """End a giveaway and pick winner(s)
        
        This will end the giveaway early and pick winner(s) based on the winners_count setting.
        If there are fewer entries than winners_count, all entrants will win."""
        # Check permissions first, before doing anything else
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server", ephemeral=True)
            return
            
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            # Fallback when member cache is not available
            try:
                member = await interaction.guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.response.send_message("❌ Failed to verify your server permissions", ephemeral=True)
                return
                
        if not member.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need Manage Messages permission to end a giveaway", ephemeral=True)
            return
            
        # Parse message ID
        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID. Please enter a numeric ID.", ephemeral=True)
            return
            
        if message_id_int not in self.giveaways:
            await interaction.response.send_message("❌ No giveaway found with that message ID.", ephemeral=True)
            return
        
        # Acknowledge the command
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        try:
            # Mark as ended and pick winner(s)
            await self.end_giveaway(message_id_int)
            await interaction.followup.send(f"✅ Giveaway ended! Check {interaction.channel.mention} for the winner(s)!")
            
        except Exception as e:
            logger.error(f"Error ending giveaway: {e}")
            try:
                await interaction.followup.send(f"❌ An error occurred while ending the giveaway", ephemeral=True)
            except discord.NotFound:
                # If followup fails, the interaction may have timed out
                pass
            
    @app_commands.command(name="list", description="List all active giveaways in this server")
    async def slash_giveaway_list(self, interaction: discord.Interaction):
        """List active giveaways in this server
        
        Shows all ongoing giveaways with their IDs, channels, and time remaining.
        Use these IDs with the /end or /reroll commands."""
        # Check if we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server", ephemeral=True)
            return
            
        # Acknowledge the command
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        try:
            active_giveaways = [g for g in self.giveaways.values() 
                              if g.guild_id == interaction.guild.id and not g.is_ended]
            
            if not active_giveaways:
                await interaction.followup.send("📝 No active giveaways in this server.")
                return
            
            embed = discord.Embed(
                title="Active Giveaways",
                color=0x00ff00,
                description=f"Found {len(active_giveaways)} active giveaways"
            )
            
            for giveaway in active_giveaways:
                channel = self.bot.get_channel(giveaway.channel_id)
                if channel:
                    time_left = format_time_remaining(giveaway.time_remaining)
                    time_formats = format_end_time(giveaway.end_time)
                    
                    embed.add_field(
                        name=f"{giveaway.prize}",
                        value=f"ID: `{giveaway.message_id}`\n"
                              f"Channel: {channel.mention}\n"
                              f"Time left: **{time_left}**\n"
                              f"Ends: {time_formats['discord_relative']} (Your time: {time_formats['discord_time']} on {time_formats['discord_date']})",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing giveaways: {e}")
            try:
                await interaction.followup.send(f"❌ An error occurred while listing giveaways", ephemeral=True)
            except discord.NotFound:
                # If followup fails, the interaction may have timed out
                pass
            
    @app_commands.command(name="reroll", description="Reroll a giveaway to pick new winner(s)")
    @app_commands.describe(message_id="The ID of the giveaway message")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        """Reroll a giveaway to pick new winner(s)
        
        This will select new winner(s) based on the original winners_count setting.
        If there are fewer entries than winners_count, all entrants will win."""
        # Check permissions first
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server", ephemeral=True)
            return
            
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            # Fallback when member cache is not available
            try:
                member = await interaction.guild.fetch_member(interaction.user.id)
            except discord.NotFound:
                await interaction.response.send_message("❌ Failed to verify your server permissions", ephemeral=True)
                return
                
        if not member.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need Manage Messages permission to reroll a giveaway", ephemeral=True)
            return
            
        # Parse message ID
        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID. Please enter a numeric ID.", ephemeral=True)
            return
            
        if message_id_int not in self.giveaways:
            await interaction.response.send_message("❌ No giveaway found with that message ID.", ephemeral=True)
            return
        
        giveaway = self.giveaways[message_id_int]
        if not giveaway.ended:
            await interaction.response.send_message("❌ This giveaway hasn't ended yet. End it first before rerolling.", ephemeral=True)
            return
            
        # Acknowledge the command
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        try:
            # Get the giveaway's channel
            channel = self.bot.get_channel(giveaway.channel_id)
            if not channel:
                await interaction.followup.send("❌ Could not find the giveaway channel.", ephemeral=True)
                return
                
            # Get all entries
            all_user_ids = giveaway.entries
            if not all_user_ids:
                await interaction.followup.send("❌ There were no entries in this giveaway.", ephemeral=True)
                return
                
            # Get user objects for all entries
            users = []
            for user_id in all_user_ids:
                user = self.bot.get_user(user_id)
                if user:
                    users.append(user)
                else:
                    # Try to fetch the user if not in cache
                    try:
                        user = await self.bot.fetch_user(user_id)
                        users.append(user)
                    except discord.NotFound:
                        logger.error(f"Could not find user with ID {user_id}")
            
            if not users:
                await interaction.followup.send("❌ Could not find any valid users to select as winners.", ephemeral=True)
                return
                
            # Determine how many winners to pick based on entries and winners_count
            winners_to_pick = min(giveaway.winners_count, len(users))
            
            # If there are fewer users than winners_count, we can't have duplicates
            if winners_to_pick == len(users):
                winners = users
            else:
                # Sample without replacement to get unique winners
                winners = random.sample(users, winners_to_pick)
            
            # Store new winner IDs
            giveaway.winner_ids = [winner.id for winner in winners]
            
            # Create mentions string for announcement
            if len(winners) == 1:
                winner_mentions = winners[0].mention
                winner_s = ""
            else:
                winner_mentions = ", ".join([winner.mention for winner in winners])
                winner_s = "s"
            
            # Send reroll announcement
            await channel.send(
                f"🎉 Giveaway rerolled! Congratulations {winner_mentions}! You are the new winner{winner_s} of **{giveaway.prize}**!"
            )
            
            await interaction.followup.send(f"✅ Giveaway rerolled! Check {channel.mention} for the new winner(s)!")
            
            winner_names = ", ".join([str(winner) for winner in winners])
            logger.info(f"Rerolled giveaway {message_id_int} in guild {giveaway.guild_id}, new winners: {winner_names}")
            
        except Exception as e:
            logger.error(f"Error rerolling giveaway: {e}")
            try:
                await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)
            except discord.NotFound:
                # If followup fails, the interaction may have timed out
                pass
        
    @app_commands.command(name="invite", description="Get an invite link to add this bot to your server")
    async def slash_giveaway_invite(self, interaction: discord.Interaction):
        """Get an invite link to add this bot to your server
        
        Provides a link that you can use to invite this bot to other servers you manage.
        The bot requires certain permissions to function properly."""
        
        # Create an invite URL with required permissions
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            read_messages=True,
            read_message_history=True,
            use_external_emojis=True,
            manage_messages=True  # For managing messages
        )
        
        invite_url = discord.utils.oauth_url(
            client_id=self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]  # Include slash commands
        )
        
        # Create embed for better presentation
        embed = discord.Embed(
            title="Invite Giveaway Bot",
            description="Thank you for your interest in Giveaway Bot!",
            color=0x00ff00
        )
        embed.add_field(
            name="Add to Your Server",
            value=f"[Click here to invite the bot]({invite_url})",
            inline=False
        )
        embed.add_field(
            name="Required Permissions",
            value="• Send Messages\n• Embed Links\n• Read Messages\n• Read Message History\n• Use External Emojis\n• Manage Messages",
            inline=False
        )
        embed.set_footer(text="Make sure to enable the proper permissions for full functionality")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="tutorial", description="Start an interactive tutorial on how to use the giveaway bot")
    async def slash_giveaway_tutorial(self, interaction: discord.Interaction):
        """Start an interactive tutorial for new giveaway hosts
        
        This will guide you through all the features of the giveaway bot with
        step-by-step instructions and examples."""
        # Create tutorial pages (embeds)
        pages = []
        
        # Welcome page
        welcome_embed = discord.Embed(
            title="🎉 Giveaway Bot Tutorial",
            description="Welcome to the Giveaway Bot tutorial! This interactive guide will show you how to create and manage giveaways in your server.",
            color=0x00aa00
        )
        welcome_embed.add_field(
            name="What You'll Learn",
            value="• How to create giveaways\n"
                 "• Managing giveaway entries\n"
                 "• Ending giveaways manually\n"
                 "• Rerolling to pick new winners\n"
                 "• Best practices for hosting giveaways",
            inline=False
        )
        welcome_embed.set_footer(text="Use the buttons below to navigate through the tutorial")
        pages.append(welcome_embed)
        
        # Page 1: Creating Giveaways
        create_embed = discord.Embed(
            title="Creating Giveaways",
            description="There are two ways to create giveaways:",
            color=0x00aa00
        )
        create_embed.add_field(
            name="1️⃣ Using the Form (Recommended)",
            value="Type `/create` to open an interactive form where you can enter:\n"
                 "• Duration (e.g., '1h', '2d', '3d12h')\n"
                 "• Number of winners\n"
                 "• Prize name\n"
                 "• Optional detailed description",
            inline=False
        )
        create_embed.add_field(
            name="2️⃣ Using the Command",
            value="Type `!giveaway start <time> [winners] <prize>`\n"
                 "Example: `!giveaway start 24h 3 Steam Game Keys`\n"
                 "This would create a giveaway for Steam Game Keys lasting 24 hours with 3 winners.",
            inline=False
        )
        create_embed.add_field(
            name="Required Permissions",
            value="You need the **Manage Messages** permission to create giveaways.",
            inline=False
        )
        create_embed.set_footer(text="Page 2/7 • Use the Next button to continue")
        pages.append(create_embed)
        
        # Page 2: Time Formats
        time_embed = discord.Embed(
            title="Time Format Guide",
            description="The bot supports flexible time formats for setting giveaway duration.",
            color=0x00aa00
        )
        time_embed.add_field(
            name="Basic Time Units",
            value="• `s` - Seconds\n"
                 "• `m` - Minutes\n"
                 "• `h` - Hours\n"
                 "• `d` - Days",
            inline=False
        )
        time_embed.add_field(
            name="Examples",
            value="• `30s` - 30 seconds\n"
                 "• `5m` - 5 minutes\n"
                 "• `2h` - 2 hours\n"
                 "• `1d` - 1 day\n"
                 "• `2d12h` - 2 days and 12 hours\n"
                 "• `1d6h30m` - 1 day, 6 hours, and 30 minutes",
            inline=False
        )
        time_embed.set_footer(text="Page 3/7 • Use the Next button to continue")
        pages.append(time_embed)
        
        # Page 3: How Entries Work
        entries_embed = discord.Embed(
            title="How Entries Work",
            description="Giveaways use a button-based entry system for simplicity and fairness.",
            color=0x00aa00
        )
        entries_embed.add_field(
            name="Entry Methods",
            value="Users enter by clicking the 🎉 button under the giveaway.\n"
                 "• Each user can only enter once\n"
                 "• The bot tracks entries automatically\n"
                 "• The entry count updates in real-time\n"
                 "• Users receive confirmation when they enter",
            inline=False
        )
        entries_embed.add_field(
            name="Multiple Winners",
            value="When creating a giveaway, you can specify how many winners to pick.\n"
                 "If there are fewer entries than winner slots, all entrants will win.",
            inline=False
        )
        entries_embed.set_footer(text="Page 4/7 • Use the Next button to continue")
        pages.append(entries_embed)
        
        # Page 4: Managing Giveaways
        manage_embed = discord.Embed(
            title="Managing Active Giveaways",
            description="You can view and manage all ongoing giveaways in your server.",
            color=0x00aa00
        )
        manage_embed.add_field(
            name="Listing Giveaways",
            value="To see all active giveaways, use:\n"
                 "• `/list` - Slash command\n"
                 "• `!giveaway list` - Prefix command\n\n"
                 "This will show all ongoing giveaways with their IDs, channels, and time remaining.",
            inline=False
        )
        manage_embed.add_field(
            name="Message IDs",
            value="Many giveaway commands require the giveaway's message ID.\n"
                 "To get a message ID:\n"
                 "1. Enable Developer Mode in Discord Settings > Advanced\n"
                 "2. Right-click on the giveaway message\n"
                 "3. Click 'Copy ID'",
            inline=False
        )
        manage_embed.set_footer(text="Page 5/7 • Use the Next button to continue")
        pages.append(manage_embed)
        
        # Page 5: Ending Giveaways
        end_embed = discord.Embed(
            title="Ending Giveaways",
            description="Giveaways end automatically when their time expires, but you can also end them manually.",
            color=0x00aa00
        )
        end_embed.add_field(
            name="Ending Manually",
            value="To end a giveaway before its scheduled time:\n"
                 "• `/end <message_id>` - Slash command\n"
                 "• `!giveaway end <message_id>` - Prefix command\n\n"
                 "This will immediately pick and announce winners.",
            inline=False
        )
        end_embed.add_field(
            name="Winner Selection",
            value="Winners are randomly selected from all entries.\n"
                 "The bot will automatically announce winners in the channel where the giveaway was hosted.",
            inline=False
        )
        end_embed.set_footer(text="Page 6/7 • Use the Next button to continue")
        pages.append(end_embed)
        
        # Page 6: Rerolling Winners
        reroll_embed = discord.Embed(
            title="Rerolling Winners",
            description="If a winner doesn't claim their prize, you can reroll to pick a new winner.",
            color=0x00aa00
        )
        reroll_embed.add_field(
            name="How to Reroll",
            value="To reroll a giveaway and pick new winners:\n"
                 "• `/reroll <message_id>` - Slash command\n"
                 "• `!giveaway reroll <message_id>` - Prefix command\n\n"
                 "This will pick new winners from the original entrants and announce them.",
            inline=False
        )
        reroll_embed.add_field(
            name="Important Notes",
            value="• You can only reroll ended giveaways\n"
                 "• Rerolling uses the same number of winners as the original giveaway\n"
                 "• Previous winners could be selected again",
            inline=False
        )
        reroll_embed.set_footer(text="Page 7/7 • Use the Next button to continue")
        pages.append(reroll_embed)
        
        # Final page: Best Practices
        best_practices_embed = discord.Embed(
            title="Giveaway Best Practices",
            description="Here are some tips for running successful giveaways in your server:",
            color=0x00aa00
        )
        best_practices_embed.add_field(
            name="Tips for Successful Giveaways",
            value="• Set reasonable durations (1-7 days is recommended)\n"
                 "• Use clear and specific prize descriptions\n"
                 "• Announce giveaways in a dedicated channel\n"
                 "• Include the prize value if applicable\n"
                 "• Use shorter durations for smaller prizes\n"
                 "• Pin the giveaway message for visibility\n"
                 "• Follow up with winners to ensure they claim prizes",
            inline=False
        )
        best_practices_embed.add_field(
            name="Need More Help?",
            value="If you have questions, use `/tutorial` to revisit this guide anytime!",
            inline=False
        )
        best_practices_embed.set_footer(text="Page 7/7 • This completes the tutorial")
        pages.append(best_practices_embed)
        
        # Create and send the tutorial view
        view = TutorialView(interaction.user.id, pages)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)
    
    @commands.group(name="giveaway", aliases=["g"], invoke_without_command=True)
    async def giveaway(self, ctx):
        """Giveaway commands with multiple winners support. Use !help giveaway for more info.
        
        This bot allows you to create giveaways with custom durations and multiple winners.
        Users enter by clicking a button, and winners are randomly selected when the giveaway ends."""
        await ctx.send_help(ctx.command)
    
    @giveaway.command(name="start", aliases=["create"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_start(self, ctx, time_str: str, winners_count: int = 1, *, prize: str):
        """
        Start a new giveaway
        Usage: !giveaway start <time> [winners_count] <prize>
        Examples: 
        - !giveaway start 1h Gaming Mouse (1 winner)
        - !giveaway start 2d 3 Steam Game Keys (3 winners)
        
        Time format: 
        - Numbers followed by s, m, h, d (seconds, minutes, hours, days)
        - Examples: 30s, 5m, 2h, 1d, 1d12h
        """
        try:
            duration_seconds = parse_time(time_str)
            if duration_seconds <= 0:
                raise ValueError("Duration must be positive")
            
            end_time = datetime.datetime.now().timestamp() + duration_seconds
            
            embed = discord.Embed(
               # title="🎊 GIVEAWAY 🎊",
                description=f"**{prize}**\n"
                f"**Hosted by:** {ctx.author.mention}",
                color=0x9BC5E7,
                timestamp=datetime.datetime.fromtimestamp(end_time)
            )
            time_formats = format_end_time(end_time)

            # Display time in a more user-friendly format with multiple formats
            time_value = (
                f"{time_formats['discord_relative']}({time_formats['discord_absolute']})"
            )
            embed.add_field(name="Ends At", value=time_value, inline=False)
            embed.add_field(name="Winners", value=f"**{winners_count}**", inline=True)
            embed.add_field(name="Entries", value="**0**", inline=True)
            
            # Format time details with timezone-aware timestamps
            time_formats = format_end_time(end_time)
            
            
           # embed.set_footer(text="Click the 🎉 button below to enter")
            
            # Create view with button
            view = GiveawayView(self)
            
            # Send the giveaway message with the view
            giveaway_message = await ctx.send(embed=embed, view=view)
            
            # Create and store the giveaway
            giveaway = Giveaway(
                channel_id=ctx.channel.id,
                message_id=giveaway_message.id,
                guild_id=ctx.guild.id,
                creator_id=ctx.author.id,
                prize=prize,
                end_time=end_time,
                winners_count=winners_count
            )
            self.giveaways[giveaway_message.id] = giveaway
            
            logger.info(f"Created giveaway {giveaway_message.id} in guild {ctx.guild.id}, "
                        f"ends at {datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
            
        except ValueError as e:
            await ctx.send(f"❌ Error: {e}")
    
    @giveaway.command(name="end", aliases=["stop"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_end(self, ctx, message_id: int):
        """
        End a giveaway and pick winner(s)
        Usage: !giveaway end <message_id>
        
        This will end the giveaway early and pick winner(s) based on the winners_count setting.
        If there are fewer entries than winners_count, all entrants will win.
        
        Get the message ID by right-clicking on the giveaway message and clicking "Copy ID"
        (You need to enable Developer Mode in Discord Settings > Advanced)
        """
        if message_id not in self.giveaways:
            await ctx.send("❌ No giveaway found with that message ID.")
            return
        
        # Mark as ended and pick winner(s)
        await self.end_giveaway(message_id)
        await ctx.send(f"✅ Giveaway ended! Check {ctx.channel.mention} for the winner(s)!")
    
    @giveaway.command(name="invite", aliases=["inv", "link"])
    async def giveaway_invite(self, ctx):
        """
        Get an invite link to add this bot to your server
        Usage: !giveaway invite
        
        Provides a link that you can use to invite this bot to other servers you manage.
        The bot requires certain permissions to function properly.
        """
        # Create an invite URL with required permissions
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            read_messages=True,
            read_message_history=True,
            use_external_emojis=True,
            manage_messages=True  # For managing messages
        )
        
        invite_url = discord.utils.oauth_url(
            client_id=self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]  # Include slash commands
        )
        
        # Create embed for better presentation
        embed = discord.Embed(
            title="Invite Giveaway Bot",
            description="Thank you for your interest in Giveaway Bot!",
            color=0x00ff00
        )
        embed.add_field(
            name="Add to Your Server",
            value=f"[Click here to invite the bot]({invite_url})",
            inline=False
        )
        embed.add_field(
            name="Required Permissions",
            value="• Send Messages\n• Embed Links\n• Read Messages\n• Read Message History\n• Use External Emojis\n• Manage Messages",
            inline=False
        )
        embed.set_footer(text="Make sure to enable the proper permissions for full functionality")
        
        await ctx.send(embed=embed)
    
    @giveaway.command(name="list", aliases=["ongoing", "active"])
    async def giveaway_list(self, ctx):
        """
        List all active giveaways in this server
        Usage: !giveaway list
        
        Shows all ongoing giveaways with their IDs, channels, and time remaining.
        Use these IDs with the !giveaway end or !giveaway reroll commands.
        """
        active_giveaways = [g for g in self.giveaways.values() 
                          if g.guild_id == ctx.guild.id and not g.is_ended]
        
        if not active_giveaways:
            await ctx.send("📝 No active giveaways in this server.")
            return
        
        embed = discord.Embed(
            title="Active Giveaways",
            color=0x00ff00,
            description=f"Found {len(active_giveaways)} active giveaways"
        )
        
        for giveaway in active_giveaways:
            channel = self.bot.get_channel(giveaway.channel_id)
            if channel:
                time_left = format_time_remaining(giveaway.time_remaining)
                time_formats = format_end_time(giveaway.end_time)
                
                embed.add_field(
                    name=f"{giveaway.prize}",
                    value=f"ID: `{giveaway.message_id}`\n"
                          f"Channel: {channel.mention}\n"
                          f"Time left: **{time_left}**\n"
                          f"Ends: {time_formats['discord_relative']} (Your time: {time_formats['discord_time']} on {time_formats['discord_date']})",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @giveaway.command(name="reroll", aliases=["pick"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_reroll(self, ctx, message_id: int):
        """
        Reroll a giveaway to pick new winner(s)
        Usage: !giveaway reroll <message_id>
        
        This will pick new winner(s) based on the original winners_count.
        If there are fewer entries than winners_count, all entrants will win.
        """
        if message_id not in self.giveaways or not self.giveaways[message_id].ended:
            await ctx.send("❌ No ended giveaway found with that message ID.")
            return
        
        giveaway = self.giveaways[message_id]
        
        try:
            channel = self.bot.get_channel(giveaway.channel_id)
            if not channel:
                await ctx.send("❌ Cannot find the giveaway channel.")
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                await ctx.send("❌ Cannot find the giveaway message.")
                return
            
            # Get entries from the giveaway
            all_user_ids = giveaway.entries
            
            # Get user objects for all entries
            users = []
            for user_id in all_user_ids:
                user = self.bot.get_user(user_id)
                if user:
                    users.append(user)
                else:
                    # Try to fetch the user if not in cache
                    try:
                        user = await self.bot.fetch_user(user_id)
                        users.append(user)
                    except discord.NotFound:
                        logger.error(f"Could not find user with ID {user_id}")
            
            if not users:
                await ctx.send(f"❌ No valid entries for the giveaway of **{giveaway.prize}**.")
                return
            
            # Determine how many winners to pick based on entries and winners_count
            winners_to_pick = min(giveaway.winners_count, len(users))
            
            # If there are fewer users than winners_count, we can't have duplicates
            if winners_to_pick == len(users):
                winners = users
            else:
                # Sample without replacement to get unique winners
                winners = random.sample(users, winners_to_pick)
            
            # Store winner IDs
            giveaway.winner_ids = [winner.id for winner in winners]
            
            # Create mentions string for announcement
            if len(winners) == 1:
                winner_mentions = winners[0].mention
                winner_s = ""
            else:
                winner_mentions = ", ".join([winner.mention for winner in winners])
                winner_s = "s"
            
            await channel.send(
                f"🎊 Giveaway rerolled! The new winner{winner_s} of **{giveaway.prize}** is {winner_mentions}! Congratulations!"
            )
            
            winner_names = ", ".join([str(winner) for winner in winners])
            logger.info(f"Rerolled giveaway {message_id} in guild {ctx.guild.id}, new winners: {winner_names}")
            
        except Exception as e:
            logger.error(f"Error rerolling giveaway {message_id}: {e}")
            await ctx.send(f"❌ An error occurred: {e}")
    
    @tasks.loop(seconds=60)
    async def check_giveaways(self):
        """Check for giveaways that have ended and announce winners"""
        # Make a copy of keys to avoid changing dictionary during iteration
        giveaway_ids = list(self.giveaways.keys())
        
        for message_id in giveaway_ids:
            giveaway = self.giveaways[message_id]
            
            # Skip already ended giveaways
            if giveaway.ended:
                continue
            
            # Check if the giveaway has ended
            if giveaway.is_ended:
                await self.end_giveaway(message_id)
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        """Wait until the bot is ready before starting the task loop"""
        await self.bot.wait_until_ready()
    
    async def end_giveaway(self, message_id: int):
        """End a giveaway and pick winner(s) based on the winners_count setting"""
        if message_id not in self.giveaways:
            return
        
        giveaway = self.giveaways[message_id]
        giveaway.ended = True
        
        try:
            channel = self.bot.get_channel(giveaway.channel_id)
            if not channel:
                logger.error(f"Cannot find channel {giveaway.channel_id} for giveaway {message_id}")
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                logger.error(f"Cannot find message {message_id} for giveaway")
                return
            
            # Update the embed to show that the giveaway has ended
            embed = message.embeds[0]
            embed.color = 0xff0000
            embed.set_field_at(0, name="Time Remaining", value="Giveaway has ended!")
            
            # Update the entries and winners fields too
            for i, field in enumerate(embed.fields):
                if field.name == "Entries":
                    embed.set_field_at(i, name="Entries", value=str(giveaway.entries_count), inline=True)
                elif field.name == "Winners":
                    embed.set_field_at(i, name="Winners", value=str(giveaway.winners_count), inline=True)
            
            # Get all entries from the button
            all_user_ids = giveaway.entries
            
            # Get user objects for all entries
            users = []
            for user_id in all_user_ids:
                user = self.bot.get_user(user_id)
                if user:
                    users.append(user)
                else:
                    # Try to fetch the user if not in cache
                    try:
                        user = await self.bot.fetch_user(user_id)
                        users.append(user)
                    except discord.NotFound:
                        logger.error(f"Could not find user with ID {user_id}")
            
            # Edit the original message
            await message.edit(embed=embed)
            
            # Announce the winners
            if users:
                # Determine how many winners to pick based on entries and winners_count
                winners_to_pick = min(giveaway.winners_count, len(users))
                
                # If there are fewer users than winners_count, we can't have duplicates
                if winners_to_pick == len(users):
                    winners = users
                else:
                    # Sample without replacement to get unique winners
                    winners = random.sample(users, winners_to_pick)
                
                # Store winner IDs
                giveaway.winner_ids = [winner.id for winner in winners]
                
                # Create mentions string for announcement
                if len(winners) == 1:
                    winner_mentions = winners[0].mention
                    winner_s = ""
                else:
                    winner_mentions = ", ".join([winner.mention for winner in winners])
                    winner_s = "s"
                
                # Send winner announcement
                await channel.send(
                    f"🎉 Congratulations {winner_mentions}! You are the winner{winner_s} of **{giveaway.prize}**!"
                )
                
                winner_names = ", ".join([str(winner) for winner in winners])
                logger.info(f"Ended giveaway {message_id} in guild {giveaway.guild_id}, winners: {winner_names}")
            else:
                await channel.send(
                    f"❌ No valid entries for the giveaway of **{giveaway.prize}**."
                )
                logger.info(f"Ended giveaway {message_id} in guild {giveaway.guild_id}, no valid entries")
            
        except Exception as e:
            logger.error(f"Error ending giveaway {message_id}: {e}")

    # Reaction event handlers removed as we no longer support reaction-based entries


async def setup(bot):
    cog = GiveawayCog(bot)
    await bot.add_cog(cog)

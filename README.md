# Discord Giveaway Bot

A Discord bot built with Python that manages giveaways with advanced features for community engagement. Provides comprehensive giveaway management using interactive buttons for entry, random winner selection, and duration tracking for server administrators. Supports both prefix commands and slash commands for seamless interaction.

## Features

- Create giveaways with customizable duration and prize
- Interactive button-based entry system (no reactions needed)
- Support for both prefix commands (`!giveaway`) and slash commands (`/giveaway`)
- Automatically select random winners when giveaways end
- List active giveaways in a server
- End giveaways early
- Reroll winners for ended giveaways
- Support for running in limited permissions mode

## Running on Replit

When running on Replit, the bot is configured to run automatically.

### Setup Steps

1. Fork this template on Replit
2. Create a Discord bot on the [Discord Developer Portal](https://discord.com/developers/applications)
3. In your bot settings, enable these privileged intents:
   - Message Content Intent
   - Server Members Intent
4. Add the bot to your Discord server with appropriate permissions
5. Go to your Replit project's "Secrets" tab and add the following secrets:
   - `DISCORD_TOKEN`: Your Discord bot token
6. Click the "Run" button to start the bot

## Local Development

If you're developing locally outside of Replit:

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install discord.py python-dotenv
   ```
3. Create a Discord bot on the [Discord Developer Portal](https://discord.com/developers/applications)
4. Create a `.env` file and add your bot token:
   ```
   DISCORD_TOKEN=your_token_here
   COMMAND_PREFIX=!
   ```
5. Run the bot:
   ```
   python main.py
   ```

## Discord Commands

### Prefix Commands
- `!giveaway start <time> <prize>` - Start a new giveaway
  - Example: `!giveaway start 1d12h Gaming Mouse`
  - Time format: Numbers followed by s, m, h, d (seconds, minutes, hours, days)
- `!giveaway end <message_id>` - End a giveaway early
- `!giveaway list` - List all active giveaways in the server
- `!giveaway reroll <message_id>` - Reroll a winner for an ended giveaway
- `!ghelp giveaway` - Show help information for giveaway commands

### Slash Commands
- `/start duration:<time> prize:<prize>` - Start a new giveaway
- `/end message_id:<message_id>` - End a giveaway early
- `/list` - List all active giveaways in the server
- `/reroll message_id:<message_id>` - Reroll a winner for an ended giveaway

## Required Permissions

The bot requires the following permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Use External Emojis & Stickers
- Read Message History
- Use Application Commands (for slash commands)

Users need the "Manage Messages" permission to create, end, or reroll giveaways.

## Configuration Options

### Environment Variables

- `DISCORD_TOKEN` - Your Discord bot token (required)
- `COMMAND_PREFIX` - Command prefix (default: `!`)
- `DISABLE_PRIVILEGED_INTENTS` - Set to "true" to run with limited functionality if you can't enable privileged intents

## Troubleshooting

### Privileged Intents Error
If you see an error about "Privileged Intents Required", you need to enable privileged intents in the Discord Developer Portal:

1. Go to https://discord.com/developers/applications
2. Select your application
3. Go to the "Bot" tab
4. Enable "Message Content Intent" and "Server Members Intent"
5. Save changes and restart your bot

### Commands Not Working
- Verify that the bot has the necessary permissions in your Discord server
- Make sure you've enabled Message Content Intent in the Discord Developer Portal
- Check that you're using the correct command prefix (default: `!`)
- For slash commands, make sure the bot has the "Use Application Commands" permission
- Try reinviting the bot with the updated permissions if needed

### Buttons Not Working
- Make sure the bot has the "Use External Emojis & Stickers" permission
- If buttons are unresponsive, it may be because the bot was restarted and lost its stored button handlers
- Try creating a new giveaway if this happens

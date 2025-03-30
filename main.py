import os
import discord.errors
from app import db, logger

# Initialize the database with context
from app import app
with app.app_context():
    # Import models
    import models  # noqa: F401
    
    # Create tables
    db.create_all()
    logger.info("Database tables created successfully")

def main():
    """Run the Discord bot"""
    from bot import GiveawayBot
    
    # Get Discord token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("No Discord bot token found. Set the DISCORD_TOKEN environment variable.")
        logger.error("To use this bot, you need to:")
        logger.error("1. Create a bot in the Discord Developer Portal: https://discord.com/developers/applications")
        logger.error("2. Go to the Bot section and enable 'Message Content Intent' and 'Server Members Intent'")
        logger.error("3. Set your bot token as DISCORD_TOKEN in your environment")
        return
    
    # Start the bot
    logger.info("Starting Discord Giveaway Bot...")
    bot = GiveawayBot()
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")
        logger.error("Please check your bot token and internet connection.")

# Run the bot when this module is executed directly
if __name__ == "__main__":
    main()

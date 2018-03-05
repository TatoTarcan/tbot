#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Bot that explains Telegram's "Deep Linking Parameters" functionality.

This program is dedicated to the public domain under the CC0 license.

This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Deep Linking example. Send /start to get the link.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, Filters
# Enable logging
from telegram.utils import helpers

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define constants the will allow us to reuse the deep-linking parameters.
CHECK_THIS_OUT = 'check-this-out'
USING_ENTITIES = 'using-entities-here'
SO_COOL = 'so-cool'


def start(bot, update):
    """Send a deep-linked URL when the command /start is issued."""
    url = helpers.create_deep_linked_url(bot.get_me().username, CHECK_THIS_OUT)
    text = "Feel free to tell your friends about it:\n\n" + url
    update.message.reply_text(text)


def deep_linked_level_1(bot, update):
    """Reached through the CHECK_THIS_OUT payload"""
    url = helpers.create_deep_linked_url(bot.get_me().username, SO_COOL)
    text = "Awesome, you just accessed hidden functionality!\n\nContinue here: " + url
    update.message.reply_text(text)


def deep_linked_level_2(bot, update):
    """Reached through the SO_COOL payload"""
    url = helpers.create_deep_linked_url(bot.get_me().username, USING_ENTITIES)
    text = "You can also mask the deep-linked URLs as links: " \
           "[▶️ CLICK HERE]({0}).".format(url)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def deep_linked_level_3(bot, update, args):
    """Reached through the USING_ENTITIES payload"""
    payload = args
    update.message.reply_text("Congratulations! This is as deep as it gets 👏🏻\n\n"
                              "The payload was: {0}".format(payload))


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("TOKEN")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register a deep-linking handler
    dp.add_handler(CommandHandler("start", deep_linked_level_1, Filters.regex(CHECK_THIS_OUT)))

    # This one works with a textual link instead of an URL
    dp.add_handler(CommandHandler("start", deep_linked_level_2, Filters.regex(SO_COOL)))

    # We can also pass on the deep-linking payload
    dp.add_handler(CommandHandler("start",
                                  deep_linked_level_3,
                                  Filters.regex(USING_ENTITIES),
                                  pass_args=True))

    # Make sure the deep-linking handlers occur *before* the normal /start handler.
    dp.add_handler(CommandHandler("start", start))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

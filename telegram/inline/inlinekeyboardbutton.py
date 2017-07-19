#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2017
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module contains an object that represents a Telegram
InlineKeyboardButton"""

from telegram import TelegramObject


class InlineKeyboardButton(TelegramObject):
    """
    This object represents one button of an inline keyboard.

    Note:
        You must use exactly one of the optional fields.

    Attributes:
        text (str): Label text on the button.
        url (str): Optional. HTTP url to be opened when button is pressed.
        callback_data (str): Optional. Data to be sent in a callback query to the bot when button
                is pressed, 1-64 bytes.
        switch_inline_query (str): Optional. If set, pressing the button will prompt the user to
                select one of their chats, open that chat and insert the bot's username and the
                specified inline query in the input field. Can be empty, in which case just the
                bot's username will be inserted. This offers an easy way for users to start using
                your bot in inline mode when they are currently in a private chat with it.
                Especially useful when combined with switch_pm* actions - in this case the user
                will be automatically returned to the chat they switched from, skipping the
                chat selection screen.
        switch_inline_query_current_chat (str): Optional. If set, pressing the button will insert
                the bot's username and the specified inline query in the current chat's input
                field. Can be empty, in which case only the bot's username will be inserted. This
                offers a quick way for the user to open your bot in inline mode in the same chat
                - good for selecting something from multiple options.
        callback_game (:class:`telegram.CallbackGame`): Optional. Description of the game that will
                be launched when the user presses the button. This type of button must always be
                the ``first`` button in the first row.
        pay (bool): Optional. Specify True, to send a Pay button. This type of button must always
                be the ``first`` button in the first row.

    Args:
        text (str): Label text on the button.
        url (Optional[str0): HTTP url to be opened when button is pressed.
        callback_data (Optional[str]): Data to be sent in a callback query to the bot when button
                is pressed, 1-64 bytes.
        switch_inline_query (Optional[str]): If set, pressing the button will prompt the user to
                select one of their chats, open that chat and insert the bot's username and the
                specified inline query in the input field. Can be empty, in which case just the
                bot's username will be inserted. This offers an easy way for users to start using
                your bot in inline mode when they are currently in a private chat with it.
                Especially useful when combined with switch_pm* actions - in this case the user
                will be automatically returned to the chat they switched from, skipping the
                chat selection screen.
        switch_inline_query_current_chat (Optional[str]): If set, pressing the button will insert
                the bot's username and the specified inline query in the current chat's input
                field. Can be empty, in which case only the bot's username will be inserted. This
                offers a quick way for the user to open your bot in inline mode in the same chat
                - good for selecting something from multiple options.
        callback_game (Optional[:class:`telegram.CallbackGame`]): Description of the game that will
                be launched when the user presses the button. This type of button must always be
                the ``first`` button in the first row.
        pay (Optional[bool]): Specify True, to send a Pay button. This type of button must always
                be the ``first`` button in the first row.
        **kwargs (dict): Arbitrary keyword arguments.
    """

    def __init__(self,
                 text,
                 url=None,
                 callback_data=None,
                 switch_inline_query=None,
                 switch_inline_query_current_chat=None,
                 callback_game=None,
                 pay=None,
                 **kwargs):
        # Required
        self.text = text

        # Optionals
        self.url = url
        self.callback_data = callback_data
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        self.callback_game = callback_game
        self.pay = pay

    @staticmethod
    def de_json(data, bot):
        """
        Args:
            data (dict):
            bot (:class:`telegram.Bot`):

        Returns:
            :class:`telegram.InlineKeyboardButton`
        """

        data = super(InlineKeyboardButton, InlineKeyboardButton).de_json(data, bot)

        if not data:
            return None

        return InlineKeyboardButton(**data)

    @staticmethod
    def de_list(data, bot):
        if not data:
            return []

        inline_keyboards = list()
        for inline_keyboard in data:
            inline_keyboards.append(InlineKeyboardButton.de_json(inline_keyboard, bot))

        return inline_keyboards

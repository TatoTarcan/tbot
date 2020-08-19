#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2020
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
"""This module contains the classes that represent Telegram InputTextMessageContent."""

from dataclasses import dataclass
from telegram import InputMessageContent
from telegram.utils.helpers import DEFAULT_NONE, DefaultValue
from typing import Any, Optional, Union


@dataclass(eq=False)
class InputTextMessageContent(InputMessageContent):
    """
    Represents the content of a text message to be sent as the result of an inline query.

    Objects of this class are comparable in terms of equality. Two objects of this class are
    considered equal, if their :attr:`message_text` is equal.

    Attributes:
        message_text (:obj:`str`): Text of the message to be sent, 1-4096 characters after entities
            parsing.
        parse_mode (:obj:`str`): Optional. Send Markdown or HTML, if you want Telegram apps to show
            bold, italic, fixed-width text or inline URLs in your bot's message.
        disable_web_page_preview (:obj:`bool`): Optional. Disables link previews for links in the
            sent message.

    Args:
        message_text (:obj:`str`): Text of the message to be sent, 1-4096 characters after entities
            parsing. Also found as :attr:`telegram.constants.MAX_MESSAGE_LENGTH`.
        parse_mode (:obj:`str`, optional): Send Markdown or HTML, if you want Telegram apps to show
            bold, italic, fixed-width text or inline URLs in your bot's message.
        disable_web_page_preview (:obj:`bool`, optional): Disables link previews for links in the
            sent message.
        **kwargs (:obj:`dict`): Arbitrary keyword arguments.

    """

    # Required
    message_text: str
    # Optionals
    parse_mode: Optional[Union[str, DefaultValue]] = DEFAULT_NONE
    disable_web_page_preview: Optional[Union[bool, DefaultValue]] = DEFAULT_NONE

    def __post_init__(self, **kwargs: Any) -> None:
        self._id_attrs = (self.message_text,)

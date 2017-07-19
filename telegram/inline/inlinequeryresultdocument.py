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
"""This module contains the classes that represent Telegram InlineQueryResultDocument"""

from telegram import InlineQueryResult, InlineKeyboardMarkup, InputMessageContent


class InlineQueryResultDocument(InlineQueryResult):
    """
    Represents a link to a file. By default, this file will be sent by the user with an optional
    caption. Alternatively, you can use :attr:`input_message_content` to send a message with the
    specified content instead of the file. Currently, only .PDF and .ZIP files can be sent
    using this method.

    Attributes:
        type (str): 'document'.
        id (str): Unique identifier for this result, 1-64 bytes.
        title (str): Title for the result.
        caption (str): Optional. Caption, 0-200 characters
        document_url (str): A valid URL for the file.
        mime_type (str): Mime type of the content of the file, either "application/pdf"
                or "application/zip".
        description (str): Optional. Short description of the result.
        reply_markup (:class:`telegram.InlineKeyboardMarkup`): Optional. Inline keyboard attached
                to the message.
        input_message_content (:class:`telegram.InputMessageContent`): Optional. Content of the
                message to be sent instead of the file.
        thumb_url (str): Optional. URL of the thumbnail (jpeg only) for the file.
        thumb_width (int): Optional. Thumbnail width.
        thumb_height (int): Optional. Thumbnail height.

    Args:
        id (str): Unique identifier for this result, 1-64 bytes.
        title (str): Title for the result.
        caption (Optional[str]): Caption, 0-200 characters
        document_url (str): A valid URL for the file.
        mime_type (str): Mime type of the content of the file, either "application/pdf"
                or "application/zip".
        description (Optional[str]): Short description of the result.
        reply_markup (:class:`telegram.InlineKeyboardMarkup`): Optional. Inline keyboard attached
                to the message.
        input_message_content (:class:`telegram.InputMessageContent`): Optional. Content of the
                message to be sent instead of the file.
        thumb_url (Optional[str]): URL of the thumbnail (jpeg only) for the file.
        thumb_width (Optional[int]): Thumbnail width.
        thumb_height (Optional[int]): Thumbnail height.
        **kwargs (dict): Arbitrary keyword arguments.
    """

    def __init__(self,
                 id,
                 document_url,
                 title,
                 mime_type,
                 caption=None,
                 description=None,
                 reply_markup=None,
                 input_message_content=None,
                 thumb_url=None,
                 thumb_width=None,
                 thumb_height=None,
                 **kwargs):
        # Required
        super(InlineQueryResultDocument, self).__init__('document', id)
        self.document_url = document_url
        self.title = title
        self.mime_type = mime_type

        # Optionals
        if caption:
            self.caption = caption
        if description:
            self.description = description
        if reply_markup:
            self.reply_markup = reply_markup
        if input_message_content:
            self.input_message_content = input_message_content
        if thumb_url:
            self.thumb_url = thumb_url
        if thumb_width:
            self.thumb_width = thumb_width
        if thumb_height:
            self.thumb_height = thumb_height

    @staticmethod
    def de_json(data, bot):
        data = super(InlineQueryResultDocument, InlineQueryResultDocument).de_json(data, bot)

        data['reply_markup'] = InlineKeyboardMarkup.de_json(data.get('reply_markup'), bot)
        data['input_message_content'] = InputMessageContent.de_json(
            data.get('input_message_content'), bot)

        return InlineQueryResultDocument(**data)

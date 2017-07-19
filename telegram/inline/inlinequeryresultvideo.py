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
"""This module contains the classes that represent Telegram
InlineQueryResultVideo"""

from telegram import InlineQueryResult, InlineKeyboardMarkup, InputMessageContent


class InlineQueryResultVideo(InlineQueryResult):
    """
    Represents a link to a page containing an embedded video player or a video file. By default,
    this video file will be sent by the user with an optional caption. Alternatively, you can use
    :attr:`input_message_content` to send a message with the specified content instead of
    the video.

    Attributes:
        type (str): 'video'.
        id (str): Unique identifier for this result, 1-64 bytes.
        video_url (str): A valid URL for the embedded video player or video file.
        mime_type (str): Mime type of the content of video url, "text/html" or "video/mp4".
        thumb_url (str): URL of the thumbnail (jpeg only) for the video.
        title (str): Title for the result.
        caption (str): Optional. Caption, 0-200 characters
        video_width (int): Optional. Video width.
        video_height (int): Optional. Video height.
        video_duration (int): Optional. Video duration in seconds.
        description (str): Optional. Short description of the result.
        reply_markup (:class:`telegram.InlineKeyboardMarkup`): Optional. Inline keyboard attached
                to the message.
        input_message_content (:class:`telegram.InputMessageContent`): Optional. Content of the
                message to be sent instead of the video.

    Args:
        id (str): Unique identifier for this result, 1-64 bytes.
        video_url (str): A valid URL for the embedded video player or video file.
        mime_type (str): Mime type of the content of video url, "text/html" or "video/mp4".
        thumb_url (str): URL of the thumbnail (jpeg only) for the video.
        title (str): Title for the result.
        caption (Optional[str]): Caption, 0-200 characters.
        video_width (Optional[int]): Video width.
        video_height (Optional[int]): Video height.
        video_duration (Optional[int]): Video duration in seconds.
        description (Optional[str]): Short description of the result.
        reply_markup (Optional[:class:`telegram.InlineKeyboardMarkup`]): Inline keyboard attached
                to the message.
        input_message_content (Optional[:class:`telegram.InputMessageContent`]): Content of the
                message to be sent instead of the video.
        **kwargs (dict): Arbitrary keyword arguments.
    """

    def __init__(self,
                 id,
                 video_url,
                 mime_type,
                 thumb_url,
                 title,
                 caption=None,
                 video_width=None,
                 video_height=None,
                 video_duration=None,
                 description=None,
                 reply_markup=None,
                 input_message_content=None,
                 **kwargs):

        # Required
        super(InlineQueryResultVideo, self).__init__('video', id)
        self.video_url = video_url
        self.mime_type = mime_type
        self.thumb_url = thumb_url
        self.title = title

        # Optional
        if caption:
            self.caption = caption
        if video_width:
            self.video_width = video_width
        if video_height:
            self.video_height = video_height
        if video_duration:
            self.video_duration = video_duration
        if description:
            self.description = description
        if reply_markup:
            self.reply_markup = reply_markup
        if input_message_content:
            self.input_message_content = input_message_content

    @staticmethod
    def de_json(data, bot):
        data = super(InlineQueryResultVideo, InlineQueryResultVideo).de_json(data, bot)

        data['reply_markup'] = InlineKeyboardMarkup.de_json(data.get('reply_markup'), bot)
        data['input_message_content'] = InputMessageContent.de_json(
            data.get('input_message_content'), bot)

        return InlineQueryResultVideo(**data)

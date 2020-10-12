# python-telegram-bot - a Python interface to the Telegram Bot API
# Copyright (C) 2015-2020
# by the python-telegram-bot contributors <devs@python-telegram-bot.org>
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
"""Constants in the Telegram network.

The following constants were extracted from the
`Telegram Bots FAQ <https://core.telegram.org/bots/faq>`_ and
`Telegram Bots API <https://core.telegram.org/bots/api>`_.

Attributes:
    MAX_MESSAGE_LENGTH (:obj:`int`): 4096
    MAX_CAPTION_LENGTH (:obj:`int`): 1024
    SUPPORTED_WEBHOOK_PORTS (List[:obj:`int`]): [443, 80, 88, 8443]
    MAX_FILESIZE_DOWNLOAD (:obj:`int`): In bytes (20MB)
    MAX_FILESIZE_UPLOAD (:obj:`int`): In bytes (50MB)
    MAX_PHOTOSIZE_UPLOAD (:obj:`int`): In bytes (10MB)
    MAX_MESSAGES_PER_SECOND_PER_CHAT (:obj:`int`): `1`. Telegram may allow short bursts that go
        over this limit, but eventually you'll begin receiving 429 errors.
    MAX_MESSAGES_PER_SECOND (:obj:`int`): 30
    MAX_MESSAGES_PER_MINUTE_PER_GROUP (:obj:`int`): 20
    MAX_INLINE_QUERY_RESULTS (:obj:`int`): 50

The following constant have been found by experimentation:

Attributes:
    MAX_MESSAGE_ENTITIES (:obj:`int`): 100 (Beyond this cap telegram will simply ignore further
        formatting styles)

The following constants are attributes of classes:

:class:`telegram.Chat`:

Attributes:
    CHAT_PRIVATE (:obj:`str`): 'private'
    CHAT_GROUP (:obj:`str`): 'group'
    CHAT_SUPERGROUP (:obj:`str`): 'supergroup'
    CHAT_CHANNEL (:obj:`str`): 'channel'

:class:`telegram.ChatAction`:

Attributes:
    CHATACTION_FIND_LOCATION (:obj:`str`): 'find_location'
    CHATACTION_RECORD_AUDIO (:obj:`str`): 'record_audio'
    CHATACTION_RECORD_VIDEO (:obj:`str`): 'record_video'
    CHATACTION_RECORD_VIDEO_NOTE (:obj:`str`): 'record_video_note'
    CHATACTION_TYPING (:obj:`str`): 'typing'
    CHATACTION_UPLOAD_AUDIO (:obj:`str`): 'upload_audio'
    CHATACTION_UPLOAD_DOCUMENT (:obj:`str`): 'upload_document'
    CHATACTION_UPLOAD_PHOTO (:obj:`str`): 'upload_photo'
    CHATACTION_UPLOAD_VIDEO (:obj:`str`): 'upload_video'
    CHATACTION_UPLOAD_VIDEO_NOTE (:obj:`str`): 'upload_video_note'

:class:`telegram.ChatMember`:

Attributes:
    CHATMEMBER_ADMINISTRATOR (:obj:`str`): 'administrator'
    CHATMEMBER_CREATOR (:obj:`str`): 'creator'
    CHATMEMBER_KICKED (:obj:`str`): 'kicked'
    CHATMEMBER_LEFT (:obj:`str`): 'left'
    CHATMEMBER_MEMBER (:obj:`str`): 'member'
    CHATMEMBER_RESTRICTED (:obj:`str`): 'restricted'

:class:`telegram.Dice`:

Attributes:
    DICE_DICE (:obj:`str`): '🎲'
    DICE_DARTS (:obj:`str`): '🎯'
    DICE_BASKETBALL (:obj:`str`): '🏀'

:class:`telegram.MessageEntity`:

Attributes:
    MESSAGEENTITY_MENTION (:obj:`str`): 'mention'
    MESSAGEENTITY_HASHTAG (:obj:`str`): 'hashtag'
    MESSAGEENTITY_CASHTAG (:obj:`str`): 'cashtag'
    MESSAGEENTITY_PHONE_NUMBER (:obj:`str`): 'phone_number'
    MESSAGEENTITY_BOT_COMMAND (:obj:`str`): 'bot_command'
    MESSAGEENTITY_URL (:obj:`str`): 'url'
    MESSAGEENTITY_EMAIL (:obj:`str`): 'email'
    MESSAGEENTITY_BOLD (:obj:`str`): 'bold'
    MESSAGEENTITY_ITALIC (:obj:`str`): 'italic'
    MESSAGEENTITY_CODE (:obj:`str`): 'code'
    MESSAGEENTITY_PRE (:obj:`str`): 'pre'
    MESSAGEENTITY_TEXT_LINK (:obj:`str`): 'text_link'
    MESSAGEENTITY_TEXT_MENTION (:obj:`str`): 'text_mention'
    MESSAGEENTITY_UNDERLINE (:obj:`str`): 'underline'
    MESSAGEENTITY_STRIKETHROUGH (:obj:`str`): 'strikethrough'

:class:`telegram.ParseMode`:

Attributes:
    PARSEMODE_MARKDOWN (:obj:`str`): 'Markdown'
    PARSEMODE_MARKDOWN_V2 (:obj:`str`): 'MarkdownV2'
    PARSEMODE_HTML (:obj:`str`): 'HTML'

:class:`telegram.Poll`:

Attributes:
    POLL_REGULAR (:obj:`str`): 'regular'
    POLL_QUIZ (:obj:`str`): 'quiz'



:class:`telegram.ext.ConversationHandler`:

Attributes:
    CONVERSATIONHANDLER_END (:obj:`int`): -1
    CONVERSATIONHANDLER_TIMEOUT (:obj:`int`): -2
    CONVERSATIONHANDLER_WAITING (:obj:`int`): -3

:class:`telegram.files.MaskPosition`:

Attributes:
    STICKER_FOREHEAD (:obj:`str`): 'forehead'
    STICKER_EYES (:obj:`str`): 'eyes'
    STICKER_MOUTH (:obj:`str`): 'mouth'
    STICKER_CHIN (:obj:`str`): 'chin'

:class:`telegram.ext.BasePersistence`:

Attributes:
    BASEPERSISTENCE_REPLACED_BOT (:obj:`str`): 'bot_instance_replaced_by_ptb_persistence'

Other constants:

Attributes:

    INPUTFILE_DEFAULT_MIME_TYPE (:obj:`str`): 'application/octet-stream'
    REQUEST_USER_AGENT (:obj:`str`):Python Telegram Bot  \
    (https://github.com/python-telegram-bot/python-telegram-bot)


"""
from typing import List

MAX_MESSAGE_LENGTH: int = 4096
MAX_CAPTION_LENGTH: int = 1024

# constants above this line are tested

SUPPORTED_WEBHOOK_PORTS: List[int] = [443, 80, 88, 8443]
MAX_FILESIZE_DOWNLOAD: int = int(20e6)  # (20MB)
MAX_FILESIZE_UPLOAD: int = int(50e6)  # (50MB)
MAX_PHOTOSIZE_UPLOAD: int = int(10e6)  # (10MB)
MAX_MESSAGES_PER_SECOND_PER_CHAT: int = 1
MAX_MESSAGES_PER_SECOND: int = 30
MAX_MESSAGES_PER_MINUTE_PER_GROUP: int = 20
MAX_MESSAGE_ENTITIES: int = 100
MAX_INLINE_QUERY_RESULTS: int = 50

CHAT_PRIVATE: str = 'private'
CHAT_GROUP: str = 'group'
CHAT_SUPERGROUP: str = 'supergroup'
CHAT_CHANNEL: str = 'channel'

CHATACTION_FIND_LOCATION: str = 'find_location'
CHATACTION_RECORD_AUDIO: str = 'record_audio'
CHATACTION_RECORD_VIDEO: str = 'record_video'
CHATACTION_RECORD_VIDEO_NOTE: str = 'record_video_note'
CHATACTION_TYPING: str = 'typing'
CHATACTION_UPLOAD_AUDIO: str = 'upload_audio'
CHATACTION_UPLOAD_DOCUMENT: str = 'upload_document'
CHATACTION_UPLOAD_PHOTO: str = 'upload_photo'
CHATACTION_UPLOAD_VIDEO: str = 'upload_video'
CHATACTION_UPLOAD_VIDEO_NOTE: str = 'upload_video_note'

CHATMEMBER_ADMINISTRATOR: str = 'administrator'
CHATMEMBER_CREATOR: str = 'creator'
CHATMEMBER_KICKED: str = 'kicked'
CHATMEMBER_LEFT: str = 'left'
CHATMEMBER_MEMBER: str = 'member'
CHATMEMBER_RESTRICTED: str = 'restricted'

DICE_DICE: str = '🎲'
DICE_DARTS: str = '🎯'
DICE_BASKETBALL: str = '🏀'

MESSAGEENTITY_MENTION: str = 'mention'
MESSAGEENTITY_HASHTAG: str = 'hashtag'
MESSAGEENTITY_CASHTAG: str = 'cashtag'
MESSAGEENTITY_PHONE_NUMBER: str = 'phone_number'
MESSAGEENTITY_BOT_COMMAND: str = 'bot_command'
MESSAGEENTITY_URL: str = 'url'
MESSAGEENTITY_EMAIL: str = 'email'
MESSAGEENTITY_BOLD: str = 'bold'
MESSAGEENTITY_ITALIC: str = 'italic'
MESSAGEENTITY_CODE: str = 'code'
MESSAGEENTITY_PRE: str = 'pre'
MESSAGEENTITY_TEXT_LINK: str = 'text_link'
MESSAGEENTITY_TEXT_MENTION: str = 'text_mention'
MESSAGEENTITY_UNDERLINE: str = 'underline'
MESSAGEENTITY_STRIKETHROUGH: str = 'strikethrough'

PARSEMODE_MARKDOWN: str = 'Markdown'
PARSEMODE_MARKDOWN_V2: str = 'MarkdownV2'
PARSEMODE_HTML: str = 'HTML'

POLL_REGULAR: str = 'regular'
POLL_QUIZ: str = 'quiz'

CONVERSATIONHANDLER_END = -1
CONVERSATIONHANDLER_TIMEOUT = -2
CONVERSATIONHANDLER_WAITING = -3

STICKER_FOREHEAD: str = 'forehead'
STICKER_EYES: str = 'eyes'
STICKER_MOUTH: str = 'mouth'
STICKER_CHIN: str = 'chin'

BASEPERSISTENCE_REPLACED_BOT = 'bot_instance_replaced_by_ptb_persistence'
INPUTFILE_DEFAULT_MIME_TYPE = 'application/octet-stream'
REQUEST_USER_AGENT = 'Python Telegram Bot ' \
                     '(https://github.com/python-telegram-bot/python-telegram-bot)'

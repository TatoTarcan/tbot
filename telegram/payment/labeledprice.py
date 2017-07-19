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
"""This module contains an object that represents a Telegram LabeledPrice."""

from telegram import TelegramObject


class LabeledPrice(TelegramObject):
    """
    This object represents a portion of the price for goods or services.

    Attributes:
        label (str): Portion label
        amount (int): Price of the product in the smallest units of the currency (integer, not
                float/double). For example, for a price of US$ 1.45 pass amount = 145. See the
                exp parameter in currencies.json, it shows the number of digits past the decimal
                point for each currency (2 for the majority of currencies).

    Args:
        label (str): Portion label
        amount (int): Price of the product in the smallest units of the currency (integer, not
                float/double). For example, for a price of US$ 1.45 pass amount = 145. See the
                exp parameter in currencies.json, it shows the number of digits past the decimal
                point for each currency (2 for the majority of currencies).
        **kwargs (dict): Arbitrary keyword arguments.
    """

    def __init__(self, label, amount, **kwargs):
        self.label = label
        self.amount = amount

    @staticmethod
    def de_json(data, bot):
        """
        Args:
            data (dict):
            bot (:class:`telegram.Bot`):

        Returns:
            :class:`telegram.LabeledPrice`
        """

        if not data:
            return None

        return LabeledPrice(**data)

    @staticmethod
    def de_list(data, bot):
        """
        Args:
            data (list):
            bot (:class:`telegram.Bot`):

        Returns:
            list(:class:`telegram.LabeledPrice`)
        """

        if not data:
            return []

        labeled_prices = list()
        for labeled_price in data:
            labeled_prices.append(LabeledPrice.de_json(labeled_price, bot))

        return labeled_prices

#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2022
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
"""This module contains the Application class."""
import asyncio
import inspect
import itertools
import logging
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from types import TracebackType, MappingProxyType
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Union,
    Generic,
    TypeVar,
    TYPE_CHECKING,
    Type,
    Tuple,
    Coroutine,
    Any,
    Set,
    Mapping,
    DefaultDict,
)

from telegram import Update
from telegram._utils.types import DVInput, ODVInput
from telegram.error import TelegramError
from telegram.ext import BasePersistence, ContextTypes, ExtBot, Updater
from telegram.ext._handler import Handler
from telegram.ext._callbackdatacache import CallbackDataCache
from telegram._utils.defaultvalue import DefaultValue, DEFAULT_TRUE, DEFAULT_NONE
from telegram._utils.warnings import warn
from telegram.ext._utils.trackingdict import TrackingDict
from telegram.ext._utils.types import CCT, UD, CD, BD, BT, JQ, HandlerCallback, ConversationKey
from telegram.ext._utils.stack import was_called_by

if TYPE_CHECKING:
    from telegram import Message
    from telegram.ext._jobqueue import Job
    from telegram.ext._applicationbuilder import InitApplicationBuilder
    from telegram.ext import ConversationHandler

DEFAULT_GROUP: int = 0

_AppType = TypeVar('_AppType', bound="Application")
_RT = TypeVar('_RT')
_STOP_SIGNAL = object()

_logger = logging.getLogger(__name__)


class ApplicationHandlerStop(Exception):
    """
    Raise this in a handler or an error handler to prevent execution of any other handler (even in
    different group).

    In order to use this exception in a :class:`telegram.ext.ConversationHandler`, pass the
    optional ``state`` parameter instead of returning the next state:

    .. code-block:: python

        def callback(update, context):
            ...
            raise ApplicationHandlerStop(next_state)

    Note:
        Has no effect, if the handler or error handler is run asynchronously.

    Args:
        state (:obj:`object`, optional): The next state of the conversation.

    Attributes:
        state (:obj:`object`): Optional. The next state of the conversation.
    """

    __slots__ = ('state',)

    def __init__(self, state: object = None) -> None:
        super().__init__()
        self.state = state


class Application(Generic[BT, CCT, UD, CD, BD, JQ]):
    """This class dispatches all kinds of updates to its registered handlers.

    Note:
         This class may not be initialized directly. Use :class:`telegram.ext.ApplicationBuilder`
         or :meth:`builder` (for convenience).

    .. versionchanged:: 14.0

        * Initialization is now done through the :class:`telegram.ext.ApplicationBuilder`.
        * Removed the attribute ``groups``.

    Attributes:
        bot (:class:`telegram.Bot`): The bot object that should be passed to the handlers.
        update_queue (:class:`asyncio.Queue`): The synchronized queue that will contain the
            updates.
        updater (:class:`telegram.ext.Updater`, optional): The updater used by this application.
        job_queue (:class:`telegram.ext.JobQueue`): Optional. The :class:`telegram.ext.JobQueue`
            instance to pass onto handler callbacks.
        chat_data (:obj:`types.MappingProxyType`): A dictionary handlers can use to store data for
            the chat.

            .. versionchanged:: 14.0
                :attr:`chat_data` is now read-only

            .. tip::
               Manually modifying :attr:`chat_data` is almost never needed and unadvisable.

        user_data (:obj:`types.MappingProxyType`): A dictionary handlers can use to store data for
            the user.

            .. versionchanged:: 14.0
               :attr:`user_data` is now read-only

            .. tip::
               Manually modifying :attr:`user_data` is almost never needed and unadvisable.

        bot_data (:obj:`dict`): A dictionary handlers can use to store data for the bot.
        persistence (:class:`telegram.ext.BasePersistence`): Optional. The persistence class to
            store data that should be persistent over restarts.
        handlers (Dict[:obj:`int`, List[:class:`telegram.ext.Handler`]]): A dictionary mapping each
            handler group to the list of handlers registered to that group.

            .. seealso::
                :meth:`add_handler`, :meth:`add_handlers`.
        error_handlers (Dict[:obj:`callable`, :obj:`bool`]): A dict, where the keys are error
            handlers and the values indicate whether they are to be run blocking.

            .. seealso::
                :meth:`add_error_handler`
        context_types (:class:`telegram.ext.ContextTypes`): Specifies the types used by this
            dispatcher for the ``context`` argument of handler and job callbacks.

    """

    # Allowing '__weakref__' creation here since we need it for the JobQueue
    __slots__ = (
        '__create_task_tasks',
        '__update_fetcher_task',
        '__update_persistence_event',
        '__update_persistence_lock',
        '__update_persistence_task',
        '__weakref__',
        '_chat_data',
        '_chat_ids_to_be_deleted_in_persistence',
        '_chat_ids_to_be_updated_in_persistence',
        '_concurrent_updates',
        '_concurrent_updates_sem',
        '_conversation_handler_conversations',
        '_initialized',
        '_running',
        '_user_data',
        '_user_ids_to_be_deleted_in_persistence',
        '_user_ids_to_be_updated_in_persistence',
        'bot',
        'bot_data',
        'chat_data',
        'context_types',
        'error_handlers',
        'handlers',
        'job_queue',
        'persistence',
        'update_queue',
        'updater',
        'user_data',
    )

    def __init__(
        self: 'Application[BT, CCT, UD, CD, BD, JQ]',
        *,
        bot: BT,
        update_queue: asyncio.Queue,
        updater: Optional[Updater],
        job_queue: JQ,
        concurrent_updates: Union[bool, int],
        persistence: Optional[BasePersistence],
        context_types: ContextTypes[CCT, UD, CD, BD],
    ):
        if not was_called_by(
            inspect.currentframe(), Path(__file__).parent.resolve() / '_applicationbuilder.py'
        ):
            warn(
                '`Application` instances should be built via the `ApplicationBuilder`.',
                stacklevel=2,
            )

        self.bot = bot
        self.update_queue = update_queue
        self.job_queue = job_queue
        self.context_types = context_types
        self.updater = updater
        self.handlers: Dict[int, List[Handler]] = {}
        self.error_handlers: Dict[Callable, Union[bool, DefaultValue]] = {}

        if isinstance(concurrent_updates, int) and concurrent_updates < 0:
            raise ValueError('`concurrent_updates` must be a non-negative integer!')
        if concurrent_updates is True:
            concurrent_updates = 4096
        self._concurrent_updates_sem = asyncio.BoundedSemaphore(concurrent_updates or 1)
        self._concurrent_updates: int = concurrent_updates or 0

        self.bot_data = self.context_types.bot_data()
        self._user_data: DefaultDict[int, UD] = defaultdict(self.context_types.user_data)
        self._chat_data: DefaultDict[int, CD] = defaultdict(self.context_types.chat_data)
        # Read only mapping
        self.user_data: Mapping[int, UD] = MappingProxyType(self._user_data)
        self.chat_data: Mapping[int, CD] = MappingProxyType(self._chat_data)

        self.persistence: Optional[BasePersistence] = None
        if persistence and not isinstance(persistence, BasePersistence):
            raise TypeError("persistence must be based on telegram.ext.BasePersistence")
        self.persistence = persistence

        # Some book keeping for persistence logic
        self._chat_ids_to_be_updated_in_persistence: Set[int] = set()
        self._user_ids_to_be_updated_in_persistence: Set[int] = set()
        self._chat_ids_to_be_deleted_in_persistence: Set[int] = set()
        self._user_ids_to_be_deleted_in_persistence: Set[int] = set()

        # This attribute will hold references to the conversation dicts of all conversation
        # handlers so that we can extract the changed states during `update_persistence`
        self._conversation_handler_conversations: Dict[
            str, TrackingDict[ConversationKey, object]
        ] = {}

        # A number of low-level helpers for the internal logic
        self._initialized = False
        self._running = False
        self.__update_fetcher_task: Optional[asyncio.Task] = None
        self.__update_persistence_task: Optional[asyncio.Task] = None
        self.__update_persistence_event = asyncio.Event()
        self.__update_persistence_lock = asyncio.Lock()
        self.__create_task_tasks: Set[asyncio.Task] = set()

    def _check_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                'This Application was not initialized via `Application.initialize`!'
            )

    @property
    def running(self) -> bool:
        """:obj:`bool`: Indicates if this application is running.

        .. seealso::
            :meth:`start`, :meth:`stop`
        """
        return self._running

    @property
    def concurrent_updates(self) -> int:
        """0 == not concurrent"""
        return self._concurrent_updates

    async def initialize(self) -> None:
        if self._initialized:
            _logger.debug('This Application is already initialized.')
            return

        await self.bot.initialize()
        if self.updater:
            await self.updater.initialize()

        if not self.persistence:
            self._initialized = True
            return

        await self._initialize_persistence()

        # Unfortunately due to circular imports this has to be here
        # pylint: disable=import-outside-toplevel
        from telegram.ext._conversationhandler import ConversationHandler

        # Initialize the persistent conversation handlers with the stored states
        for handler in itertools.chain.from_iterable(self.handlers.values()):
            if isinstance(handler, ConversationHandler) and handler.persistent and handler.name:
                await self._add_ch_to_persistence(handler)

        self._initialized = True

    async def _add_ch_to_persistence(self, handler: 'ConversationHandler') -> None:
        self._conversation_handler_conversations.update(
            await handler._initialize_persistence(self)  # pylint: disable=protected-access
        )

    async def shutdown(self) -> None:
        """

        Returns:

        Raises:
            :exc:`RuntimeError`: If the application is still :attr:`running`.
        """
        if self.running:
            raise RuntimeError('This Application is still running!')

        if not self._initialized:
            _logger.debug('This Application is already shut down. Returning.')
            return

        await self.bot.shutdown()
        if self.updater:
            await self.updater.shutdown()

        if self.persistence:
            _logger.debug('Updating & flushing persistence before shutdown')
            await self.update_persistence()
            await self.persistence.flush()
            _logger.debug('Updated and flushed persistence')

        self._initialized = False

    async def __aenter__(self: _AppType) -> _AppType:
        try:
            await self.initialize()
            return self
        except Exception as exc:
            await self.shutdown()
            raise exc

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        # Make sure not to return `True` so that exceptions are not suppressed
        # https://docs.python.org/3/reference/datamodel.html?#object.__aexit__
        await self.shutdown()

    async def _initialize_persistence(self) -> None:
        if not self.persistence:
            return

        if self.persistence.store_data.user_data:
            self._user_data.update(await self.persistence.get_user_data())
        if self.persistence.store_data.chat_data:
            self._chat_data.update(await self.persistence.get_chat_data())
        if self.persistence.store_data.bot_data:
            self.bot_data = await self.persistence.get_bot_data()
            if not isinstance(self.bot_data, self.context_types.bot_data):
                raise ValueError(
                    f"bot_data must be of type {self.context_types.bot_data.__name__}"
                )
        if self.persistence.store_data.callback_data:
            persistent_data = await self.persistence.get_callback_data()
            if persistent_data is not None:
                if not isinstance(persistent_data, tuple) or len(persistent_data) != 2:
                    raise ValueError('callback_data must be a tuple of length 2')
                # Mypy doesn't know that persistence.set_bot (see above) already checks that
                # self.bot is an instance of ExtBot if callback_data should be stored ...
                self.bot.callback_data_cache = CallbackDataCache(  # type: ignore[attr-defined]
                    self.bot,  # type: ignore[arg-type]
                    self.bot.callback_data_cache.maxsize,  # type: ignore[attr-defined]
                    persistent_data=persistent_data,
                )

    @staticmethod
    def builder() -> 'InitApplicationBuilder':
        """Convenience method. Returns a new :class:`telegram.ext.ApplicationBuilder`.

        .. versionadded:: 14.0
        """
        # Unfortunately this needs to be here due to cyclical imports
        from telegram.ext import ApplicationBuilder  # pylint: disable=import-outside-toplevel

        return ApplicationBuilder()

    async def start(self) -> None:
        """Starts

        * a background task that fetches updates from :attr:`update_queue` and
          processes them.
        * :attr:`job_queue`, if set
        * a background tasks that calls :meth:`update_persistence` in regular intervals, if
          :attr:`persistence` is set.

        Note:
            This does *not* start fetching updates from Telegram. You need to either start
            :attr:`updater` manually or use one of :meth:`run_polling` or :meth:`run_webhook`.

        Raises:
            :exc:`RuntimeError`: If the application is already running or was not initialized.
        """
        if self.running:
            raise RuntimeError('This Application is already running!')
        self._check_initialized()

        self._running = True
        self.__update_persistence_event.clear()

        try:
            if self.persistence:
                self.__update_persistence_task = asyncio.create_task(
                    self._persistence_updater()
                    # TODO: Add this once we drop py3.7
                    # name=f'Application:{self.bot.id}:persistence_updater'
                )
                _logger.debug('Loop for updating persistence started')

            if self.job_queue:
                await self.job_queue.start()
                _logger.debug('JobQueue started')

            self.__update_fetcher_task = asyncio.create_task(
                self._update_fetcher(),
                # TODO: Add this once we drop py3.7
                # name=f'Application:{self.bot.id}:update_fetcher'
            )
            _logger.info('Application started')

        except Exception as exc:
            self._running = False
            raise exc

    async def stop(self) -> None:
        """Stops the process after processing any pending updates or tasks created by
        :meth:`create_task`. Also stops :attr:`job_queue`, if set.
        Finally, calls :meth:`update_persistence` and :meth:`BasePersistence.flush` on
        :attr:`persistence`, if set.

        Warning:
            Once this method is called, no more updates will be fetched from :attr:`update_queue`,
            even if it's not empty.

        Note:
            This does *not* stop :attr:`updater`. You need to either manually call
            :meth:`telegram.ext.Updater.stop` or use one of :meth:`run_polling` or
            :meth:`run_webhook`.

        Raises:
            :exc:`RuntimeError`: If the application is not running.
        """
        if not self.running:
            raise RuntimeError('This Application is not running!')

        self._running = False
        _logger.info('Application is stopping. This might take a moment.')

        # Stop listening for new updates and handle all pending ones
        await self.update_queue.put(_STOP_SIGNAL)
        _logger.debug('Waiting for update_queue to join')
        await self.update_queue.join()
        if self.__update_fetcher_task:
            await self.__update_fetcher_task
        _logger.debug("Application stopped fetching of updates.")

        if self.job_queue:
            _logger.debug('Waiting for running jobs to finish')
            await self.job_queue.stop(wait=True)
            _logger.debug('JobQueue stopped')

        _logger.debug('Waiting for `create_task` calls to be processed')
        await asyncio.gather(*self.__create_task_tasks, return_exceptions=True)

        # Make sure that this is the *last* step of stopping the application!
        if self.persistence and self.__update_persistence_task:
            _logger.debug('Waiting for persistence loop to finish')
            self.__update_persistence_event.set()
            await self.__update_persistence_task
            self.__update_persistence_event.clear()

        _logger.info('Application.stop() complete')

    def run_polling(
        self,
        poll_interval: float = 0.0,
        timeout: int = 10,
        bootstrap_retries: int = -1,
        read_timeout: float = 2,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        allowed_updates: List[str] = None,
        drop_pending_updates: bool = None,
        close_loop: bool = True,
    ) -> None:
        """Temp docstring to make this referencable
        #TODO: Adda meaningful description
        """
        if not self.updater:
            raise RuntimeError(
                'Application.run_polling is only available if the application has an Updater.'
            )

        def error_callback(exc: TelegramError) -> None:
            self.create_task(self.process_error(error=exc, update=None))

        return self.__run(
            updater_coroutine=self.updater.start_polling(
                poll_interval=poll_interval,
                timeout=timeout,
                bootstrap_retries=bootstrap_retries,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
                connect_timeout=connect_timeout,
                pool_timeout=pool_timeout,
                allowed_updates=allowed_updates,
                drop_pending_updates=drop_pending_updates,
                error_callback=error_callback,
            ),
            close_loop=close_loop,
        )

    def run_webhook(
        self,
        listen: str = '127.0.0.1',
        port: int = 80,
        url_path: str = '',
        cert: Union[str, Path] = None,
        key: Union[str, Path] = None,
        bootstrap_retries: int = 0,
        webhook_url: str = None,
        allowed_updates: List[str] = None,
        drop_pending_updates: bool = None,
        ip_address: str = None,
        max_connections: int = 40,
        close_loop: bool = True,
    ) -> None:
        """Temp docstring to make this referencable
        #TODO: Adda meaningful description
        """
        if not self.updater:
            raise RuntimeError(
                'Application.run_webhook is only available if the application has an Updater.'
            )

        return self.__run(
            updater_coroutine=self.updater.start_webhook(
                listen=listen,
                port=port,
                url_path=url_path,
                cert=cert,
                key=key,
                bootstrap_retries=bootstrap_retries,
                drop_pending_updates=drop_pending_updates,
                webhook_url=webhook_url,
                allowed_updates=allowed_updates,
                ip_address=ip_address,
                max_connections=max_connections,
            ),
            close_loop=close_loop,
        )

    def __run(self, updater_coroutine: Coroutine, close_loop: bool = True) -> None:
        # Calling get_event_loop() should still be okay even in py3.10+ as long as there is a
        # running event loop or we are in the main thread, which are the intended use cases.
        # See the docs of get_event_loop() and get_running_loop() for more info
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.initialize())
            loop.run_until_complete(updater_coroutine)
            loop.run_until_complete(self.start())

            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as exc:
            # In case the coroutine wasn't awaited, we don't need to bother the user with a warning
            updater_coroutine.close()
            raise exc
        finally:
            # We arrive here either by catching the exceptions above or if the loop gets stopped
            try:
                # Mypy doesn't know that we already check if updater is None
                if self.updater.running:  # type: ignore[union-attr]
                    loop.run_until_complete(self.updater.stop())  # type: ignore[union-attr]
                if self.running:
                    loop.run_until_complete(self.stop())
                loop.run_until_complete(self.shutdown())
                loop.run_until_complete(self.updater.shutdown())  # type: ignore[union-attr]
            finally:
                if close_loop:
                    loop.close()

    def create_task(self, coroutine: Coroutine, update: object = None) -> asyncio.Task:
        """Thin wrapper around :func:`asyncio.create_task` that handles exceptions raised by
        the :paramref:`coroutine` with :meth:`process_error`.

        Note:
            * If :paramref:`coroutine` raises an exception, it will be set on the task created by
              this method even though it's handled by :meth:`process_error`.
            * If the application is currently running, tasks created by this methods will be
              awaited by :meth:`stop`.

        Args:
            coroutine: The coroutine to run as task.
            update: Optional. If passed, will be passed to :meth:`process_error` as additional
                information for the error handlers. Moreover, the corresponding :attr:`chat_data`
                and :attr:`user_data` entries will be updated in the next run of
                :meth:`update_persistence` after the :paramref:`coroutine` is finished.

        Returns:
            :class:`asyncio.Task`: The created task.
        """
        return self.__create_task(coroutine=coroutine, update=update)

    def __create_task(
        self, coroutine: Coroutine, update: object = None, is_error_handler: bool = False
    ) -> asyncio.Task:
        # Unfortunately, we can't know if `coroutine` runs one of the error handler functions
        # but by passing `is_error_handler=True` from `process_error`, we can make sure that we
        # get at most one recursion of the user calls `create_task` manually with an error handler
        # function
        task = asyncio.create_task(
            self.__create_task_callback(
                coroutine=coroutine, update=update, is_error_handler=is_error_handler
            )
        )

        if self.running:
            self.__create_task_tasks.add(task)
            task.add_done_callback(self.__create_task_done_callback)
        else:
            _logger.warning(
                "Tasks created via `Application.create_task` while the application is not "
                "running won't be automatically awaited!"
            )

        return task

    def __create_task_done_callback(self, task: asyncio.Task) -> None:
        self.__create_task_tasks.discard(task)
        # We just retrieve the eventual exception so that asyncio doesn't complain in case
        # it's not retrieved somewhere else
        try:
            task.exception()
        except (asyncio.CancelledError, asyncio.InvalidStateError):
            pass

    async def __create_task_callback(
        self,
        coroutine: Coroutine[Any, Any, _RT],
        update: object = None,
        is_error_handler: bool = False,
    ) -> _RT:
        try:
            return await coroutine
        except asyncio.CancelledError as cancel:
            # TODO: in py3.8+, CancelledError is a subclass of BaseException, so we can drop this
            #   close when we drop py3.7
            raise cancel
        except Exception as exception:
            if isinstance(exception, ApplicationHandlerStop):
                warn(
                    'ApplicationHandlerStop is not supported with asynchronously '
                    'running handlers.',
                    stacklevel=1,
                )

            # Avoid infinite recursion of error handlers.
            elif is_error_handler:
                _logger.exception(
                    'An error was raised and an uncaught error was raised while '
                    'handling the error with an error_handler.',
                    exc_info=exception,
                )

            else:
                # If we arrive here, an exception happened in the task and was neither
                # ApplicationHandlerStop nor raised by an error handler.
                # So we can and must handle it
                await self.process_error(update=update, error=exception, coroutine=coroutine)

            # Raise exception so that it can be set on the task
            raise exception
        finally:
            self._mark_for_persistence_update(update=update)

    async def _update_fetcher(self) -> None:
        # Continuously fetch updates from the queue. Exit only once the signal object is found.
        while True:
            update = await self.update_queue.get()

            if update is _STOP_SIGNAL:
                _logger.debug('Dropping pending updates')
                while not self.update_queue.empty():
                    self.update_queue.task_done()

                # For the _STOP_SIGNAL
                self.update_queue.task_done()
                return

            _logger.debug('Processing update %s', update)

            if self._concurrent_updates:
                self.create_task(self.__process_update_wrapper(update), update=update)
            else:
                await self.__process_update_wrapper(update)

    async def __process_update_wrapper(self, update: object) -> None:
        async with self._concurrent_updates_sem:
            await self.process_update(update)
            self.update_queue.task_done()

    async def process_update(self, update: object) -> None:
        """Processes a single update and updates the persistence.
        Exceptions raised by handler callbacks will be processed by :meth:`process_update`.

        .. versionchanged:: 14.0
            This calls :meth:`update_persistence` exactly once after handling of the update was
            finished by *all* handlers that handled the update, including asynchronously running
            handlers.

        Args:
            update (:class:`telegram.Update` | :obj:`object` | \
                :class:`telegram.error.TelegramError`):
                The update to process.

        Raises:
            :exc:`RuntimeError`: If the application was not initialized.
        """
        # Processing updates before initialize() is a problem e.g. if persistence is used
        self._check_initialized()

        context = None
        any_blocking = False

        for handlers in self.handlers.values():
            try:
                for handler in handlers:
                    check = handler.check_update(update)
                    if not (check is None or check is False):
                        if not context:
                            context = self.context_types.context.from_update(update, self)
                            await context.refresh_data()
                        coroutine: Coroutine = handler.handle_update(update, self, check, context)

                        if not handler.block or (
                            handler.block is DEFAULT_TRUE
                            and isinstance(self.bot, ExtBot)
                            and self.bot.defaults
                            and not self.bot.defaults.block
                        ):
                            self.create_task(coroutine, update=update)
                        else:
                            any_blocking = True
                            await coroutine
                        break

            # Stop processing with any other handler.
            except ApplicationHandlerStop:
                _logger.debug('Stopping further handlers due to ApplicationHandlerStop')
                break

            # Dispatch any error.
            except Exception as exc:
                if await self.process_error(update=update, error=exc):
                    _logger.debug('Error handler stopped further handlers.')
                    break

        if any_blocking:
            # Only need to mark the update for persistence if there was at least one
            # blocking handler - the non-blocking handlers mark the update again when finished
            self._mark_for_persistence_update(update=update)

    def add_handler(self, handler: Handler[Any, CCT], group: int = DEFAULT_GROUP) -> None:
        """Register a handler.

        TL;DR: Order and priority counts. 0 or 1 handlers per group will be used. End handling of
        update with :class:`telegram.ext.ApplicationHandlerStop`.

        A handler must be an instance of a subclass of :class:`telegram.ext.Handler`. All handlers
        are organized in groups with a numeric value. The default group is 0. All groups will be
        evaluated for handling an update, but only 0 or 1 handler per group will be used. If
        :class:`telegram.ext.ApplicationHandlerStop` is raised from one of the handlers, no further
        handlers (regardless of the group) will be called.

        The priority/order of handlers is determined as follows:

          * Priority of the group (lower group number == higher priority)
          * The first handler in a group which should handle an update (see
            :attr:`telegram.ext.Handler.check_update`) will be used. Other handlers from the
            group will not be used. The order in which handlers were added to the group defines the
            priority.

        Warning:
            Adding persistent :class:`telegram.ext.ConversationHandler` after the application has
            been initialized is discouraged. This is because the persisted conversation states need
            to be loaded into memory while the application is already processing updates, which
            might lead to race conditions and undesired behavior. In particular, current
            conversation states may be overridden by the loaded data.

        Args:
            handler (:class:`telegram.ext.Handler`): A Handler instance.
            group (:obj:`int`, optional): The group identifier. Default is 0.

        """
        # Unfortunately due to circular imports this has to be here
        # pylint: disable=import-outside-toplevel
        from telegram.ext._conversationhandler import ConversationHandler

        if not isinstance(handler, Handler):
            raise TypeError(f'handler is not an instance of {Handler.__name__}')
        if not isinstance(group, int):
            raise TypeError('group is not int')
        if isinstance(handler, ConversationHandler) and handler.persistent and handler.name:
            if not self.persistence:
                raise ValueError(
                    f"ConversationHandler {handler.name} "
                    f"can not be persistent if application has no persistence"
                )
            if self._initialized:
                self.create_task(self._add_ch_to_persistence(handler))
                warn(
                    'A persistent `ConversationHandler` was passed to `add_handler`, '
                    'after `Application.initialize` was called. This is discouraged.'
                    'See the docs of `Application.add_handler` for details.',
                    stacklevel=2,
                )

        if group not in self.handlers:
            self.handlers[group] = []
            self.handlers = dict(sorted(self.handlers.items()))  # lower -> higher groups

        self.handlers[group].append(handler)

    def add_handlers(
        self,
        handlers: Union[
            Union[List[Handler], Tuple[Handler]], Dict[int, Union[List[Handler], Tuple[Handler]]]
        ],
        group: DVInput[int] = DefaultValue(0),
    ) -> None:
        """Registers multiple handlers at once. The order of the handlers in the passed
        sequence(s) matters. See :meth:`add_handler` for details.

        .. versionadded:: 14.0
        .. seealso:: :meth:`add_handler`

        Args:
            handlers (List[:obj:`telegram.ext.Handler`] | \
                Dict[int, List[:obj:`telegram.ext.Handler`]]): \
                Specify a sequence of handlers *or* a dictionary where the keys are groups and
                values are handlers.
            group (:obj:`int`, optional): Specify which group the sequence of ``handlers``
                should be added to. Defaults to ``0``.

        """
        if isinstance(handlers, dict) and not isinstance(group, DefaultValue):
            raise ValueError('The `group` argument can only be used with a sequence of handlers.')

        if isinstance(handlers, dict):
            for handler_group, grp_handlers in handlers.items():
                if not isinstance(grp_handlers, (list, tuple)):
                    raise ValueError(f'Handlers for group {handler_group} must be a list or tuple')

                for handler in grp_handlers:
                    self.add_handler(handler, handler_group)

        elif isinstance(handlers, (list, tuple)):
            for handler in handlers:
                self.add_handler(handler, DefaultValue.get_value(group))

        else:
            raise ValueError(
                "The `handlers` argument must be a sequence of handlers or a "
                "dictionary where the keys are groups and values are sequences of handlers."
            )

    def remove_handler(self, handler: Handler, group: int = DEFAULT_GROUP) -> None:
        """Remove a handler from the specified group.

        Args:
            handler (:class:`telegram.ext.Handler`): A Handler instance.
            group (:obj:`object`, optional): The group identifier. Default is 0.

        """
        if handler in self.handlers[group]:
            self.handlers[group].remove(handler)
            if not self.handlers[group]:
                del self.handlers[group]

    def drop_chat_data(self, chat_id: int) -> None:
        """Drops the corresponding entry from the :attr:`chat_data`. Will also be deleted from
        the persistence on the next run of :meth:`update_persistence`, if applicable.

        Warning:
            When using :paramref:`concurrent_updates` or the :attr:`job_queue`,
            :meth:`process_update` or :meth:`telegram.ext.Job.run` may re-create this entry due to
            the asynchronous nature of these features. Please make sure that your program can
            avoid or handle such situations.

        .. versionadded:: 14.0

        Args:
            chat_id (:obj:`int`): The chat id to delete. The entry will be deleted even if it is
                not empty.
        """
        self._chat_data.pop(chat_id, None)  # type: ignore[arg-type]
        self._chat_ids_to_be_deleted_in_persistence.add(chat_id)

    def drop_user_data(self, user_id: int) -> None:
        """Drops the corresponding entry from the :attr:`user_data`. Will also be deleted from
        the persistence on the next run of :meth:`update_persistence`, if applicable.

        Warning:
            When using :paramref:`concurrent_updates` or the :attr:`job_queue`,
            :meth:`process_update` or :meth:`telegram.ext.Job.run` may re-create this entry due to
            the asynchronous nature of these features. Please make sure that your program can
            avoid or handle such situations.

        .. versionadded:: 14.0

        Args:
            user_id (:obj:`int`): The user id to delete. The entry will be deleted even if it is
                not empty.
        """
        self._user_data.pop(user_id, None)  # type: ignore[arg-type]
        self._user_ids_to_be_deleted_in_persistence.add(user_id)

    def migrate_chat_data(
        self, message: 'Message' = None, old_chat_id: int = None, new_chat_id: int = None
    ) -> None:
        """Moves the contents of :attr:`chat_data` at key old_chat_id to the key new_chat_id.
        Also marks the entries to be updated accordingly in the next run of
        :meth:`update_persistence`.

        Warning:
            * Any data stored in :attr:`chat_data` at key `new_chat_id` will be overridden
            * The key `old_chat_id` of :attr:`chat_data` will be deleted
            * This does not update the :attr:`~telegram.ext.Job.chat_id` attribute of any scheduled
              :class:`telegram.ext.Job`.

        Warning:
            When using :paramref:`concurrent_updates` or the :attr:`job_queue`,
            :meth:`process_update` or :meth:`telegram.ext.Job.run` may re-create the old entry due
            to the asynchronous nature of these features. Please make sure that your program can
            avoid or handle such situations.

        Args:
            message (:class:`telegram.Message`, optional): A message with either
                :attr:`~telegram.Message.migrate_from_chat_id` or
                :attr:`~telegram.Message.migrate_to_chat_id`.
                Mutually exclusive with passing :paramref:`old_chat_id`` and
                :paramref:`new_chat_id`
                .. seealso: `telegram.ext.filters.StatusUpdate.MIGRATE`
            old_chat_id (:obj:`int`, optional): The old chat ID.
                Mutually exclusive with passing :paramref:`message`
            new_chat_id (:obj:`int`, optional): The new chat ID.
                Mutually exclusive with passing :paramref:`message`
        """
        if message and (old_chat_id or new_chat_id):
            raise ValueError("Message and chat_id pair are mutually exclusive")
        if not any((message, old_chat_id, new_chat_id)):
            raise ValueError("chat_id pair or message must be passed")

        if message:
            if message.migrate_from_chat_id is None and message.migrate_to_chat_id is None:
                raise ValueError(
                    "Invalid message instance. The message must have either "
                    "`Message.migrate_from_chat_id` or `Message.migrate_to_chat_id`."
                )

            old_chat_id = message.migrate_from_chat_id or message.chat.id
            new_chat_id = message.migrate_to_chat_id or message.chat.id

        elif not (isinstance(old_chat_id, int) and isinstance(new_chat_id, int)):
            raise ValueError("old_chat_id and new_chat_id must be integers")

        self._chat_data[new_chat_id] = self._chat_data[old_chat_id]
        self.drop_chat_data(old_chat_id)

        self._chat_ids_to_be_updated_in_persistence.add(new_chat_id)
        # old_chat_id is marked for deletion by drop_chat_data above

    def _mark_for_persistence_update(self, *, update: object = None, job: 'Job' = None) -> None:
        if isinstance(update, Update):
            if update.effective_chat:
                self._chat_ids_to_be_updated_in_persistence.add(update.effective_chat.id)
            if update.effective_user:
                self._user_ids_to_be_updated_in_persistence.add(update.effective_user.id)

        if job:
            if job.chat_id:
                self._chat_ids_to_be_updated_in_persistence.add(job.chat_id)
            if job.user_id:
                self._user_ids_to_be_updated_in_persistence.add(job.user_id)

    async def _persistence_updater(self) -> None:
        # Update the persistence in regular intervals. Exit only when the stop event has been set
        while not self.__update_persistence_event.is_set():
            if not self.persistence:
                return

            try:
                await asyncio.wait_for(
                    self.__update_persistence_event.wait(),
                    timeout=self.persistence.update_interval,
                )
                return
            except asyncio.TimeoutError:
                pass

            # putting this *after* the wait_for so we don't immediately update on startup as
            # that would make little sense
            await self.update_persistence()

    async def update_persistence(self) -> None:
        """Updates :attr:`user_data`, :attr:`chat_data`, :attr:`bot_data` in :attr:`persistence`
        along with :attr:`~telegram.ext.ExtBot.callback_data_cache` and the conversation states of
        any persistent :class:`~telegram.ext.ConversationHandler` registered for this application.

        For :attr:`user_data`, :attr:`chat_data`, only entries used since the last run of this
        method are updated.

        Tip:
            This method will be called in regular intervals by the application. There is usually
            no need to call it manually.

        .. seealso:: :attr:`telegram.ext.BasePersistence.update_interval`.
        """
        async with self.__update_persistence_lock:
            await self.__update_persistence()

    async def __update_persistence(self) -> None:
        if not self.persistence:
            return

        _logger.debug('Starting next run of updating the persistence.')

        coroutines: Set[Coroutine] = set()

        if self.persistence.store_data.callback_data:
            # Mypy doesn't know that persistence.set_bot (see above) already checks that
            # self.bot is an instance of ExtBot if callback_data should be stored ...
            coroutines.add(
                self.persistence.update_callback_data(
                    deepcopy(
                        self.bot.callback_data_cache.persistence_data  # type: ignore[attr-defined]
                    )
                )
            )

        if self.persistence.store_data.bot_data:
            coroutines.add(self.persistence.update_bot_data(deepcopy(self.bot_data)))

        if self.persistence.store_data.chat_data:
            update_ids = self._chat_ids_to_be_updated_in_persistence
            self._chat_ids_to_be_updated_in_persistence = set()
            delete_ids = self._chat_ids_to_be_deleted_in_persistence
            self._chat_ids_to_be_deleted_in_persistence = set()

            # We don't want to update any data that has been deleted!
            update_ids -= delete_ids

            for chat_id in update_ids:
                coroutines.add(
                    self.persistence.update_chat_data(chat_id, deepcopy(self.chat_data[chat_id]))
                )
            for chat_id in delete_ids:
                coroutines.add(self.persistence.drop_chat_data(chat_id))

        if self.persistence.store_data.user_data:
            update_ids = self._user_ids_to_be_updated_in_persistence
            self._user_ids_to_be_updated_in_persistence = set()
            delete_ids = self._user_ids_to_be_deleted_in_persistence
            self._user_ids_to_be_deleted_in_persistence = set()

            # We don't want to update any data that has been deleted!
            update_ids -= delete_ids

            for user_id in update_ids:
                coroutines.add(
                    self.persistence.update_user_data(user_id, deepcopy(self.user_data[user_id]))
                )
            for user_id in delete_ids:
                coroutines.add(self.persistence.drop_user_data(user_id))

        # Unfortunately due to circular imports this has to be here
        # pylint: disable=import-outside-toplevel
        from telegram.ext._conversationhandler import PendingState

        for name, (key, new_state) in itertools.chain.from_iterable(
            zip(itertools.repeat(name), states_dict.pop_accessed_write_items())
            for name, states_dict in self._conversation_handler_conversations.items()
        ):
            if isinstance(new_state, PendingState):
                # If the handler was running non-blocking, we check if the new state is already
                # available. Otherwise, we update with the old state, which is the next best
                # guess.
                # Note that when updating the persistence one last time during self.stop(),
                # *all* tasks will be done.
                if not new_state.done():
                    if self.running:
                        _logger.debug(
                            'A ConversationHandlers state was not yet resolved. Updating the '
                            'persistence with the current state. Will check again on next run of '
                            'Application.update_persistence.'
                        )
                    else:
                        _logger.warning(
                            'A ConversationHandlers state was not yet resolved. Updating the '
                            'persistence with the current state.'
                        )
                    result = new_state.old_state
                    # We need to check again on the next run if the state is done
                    self._conversation_handler_conversations[name].mark_as_accessed(key)
                else:
                    result = new_state.resolve()
            else:
                result = new_state

            effective_new_state = None if result is TrackingDict.DELETED else result
            coroutines.add(
                self.persistence.update_conversation(
                    name=name, key=key, new_state=effective_new_state
                )
            )

        results = await asyncio.gather(*coroutines, return_exceptions=True)
        _logger.debug('Finished updating persistence.')

        # dispatch any errors
        await asyncio.gather(
            *(
                self.process_error(error=result, update=None)
                for result in results
                if isinstance(result, Exception)
            )
        )

    def add_error_handler(
        self,
        callback: HandlerCallback[object, CCT, None],
        block: DVInput[bool] = DEFAULT_TRUE,
    ) -> None:
        """Registers an error handler in the Application. This handler will receive every error
        which happens in your bot. See the docs of :meth:`process_error` for more details on how
        errors are handled.

        Note:
            Attempts to add the same callback multiple times will be ignored.

        Args:
            callback (:obj:`callable`): The callback function for this error handler. Will be
                called when an error is raised. Callback signature:
                ``def callback(update: Optional[object], context: CallbackContext)``.
                The error that happened will be present in ``context.error``.
            block (:obj:`bool`, optional): Determines whether the return value of the callback
                should be awaited before processing the next error handler in
                :meth:`process_error`. Defaults to :obj:`True`.
        """
        if callback in self.error_handlers:
            _logger.warning('The callback is already registered as an error handler. Ignoring.')
            return

        self.error_handlers[callback] = block

    def remove_error_handler(self, callback: Callable[[object, CCT], None]) -> None:
        """Removes an error handler.

        Args:
            callback (:obj:`callable`): The error handler to remove.

        """
        self.error_handlers.pop(callback, None)

    async def process_error(
        self,
        update: Optional[object],
        error: Exception,
        job: 'Job' = None,
        coroutine: Coroutine = None,
    ) -> bool:
        """Processes an error by passing it to all error handlers registered with
        :meth:`add_error_handler`. If one of the error handlers raises
        :class:`telegram.ext.ApplicationHandlerStop`, the error will not be handled by other error
        handlers. Raising :class:`telegram.ext.ApplicationHandlerStop` also stops processing of
        the update when this method is called by :meth:`process_update`, i.e. no further handlers
        (even in other groups) will handle the update. All other exceptions raised by an error
        handler will just be logged.

        .. versionchanged:: 14.0

            * Exceptions raised by error handlers are now properly logged.
            * :class:`telegram.ext.ApplicationHandlerStop` is no longer reraised but converted into
              the return value.

        Args:
            update (:obj:`object` | :class:`telegram.Update`): The update that caused the error.
            error (:obj:`Exception`): The error that was raised.
            job (:class:`telegram.ext.Job`, optional): The job that caused the error.

                .. versionadded:: 14.0

        Returns:
            :obj:`bool`: :obj:`True` if one of the error handlers raised
                :class:`telegram.ext.ApplicationHandlerStop`. :obj:`False`, otherwise.
        """
        if self.error_handlers:
            for (
                callback,
                block,
            ) in self.error_handlers.items():  # pylint: disable=redefined-outer-name
                context = self.context_types.context.from_error(
                    update=update,
                    error=error,
                    application=self,
                    job=job,
                    coroutine=coroutine,
                )
                if not block or (
                    block is DEFAULT_TRUE
                    and isinstance(self.bot, ExtBot)
                    and self.bot.defaults
                    and not self.bot.defaults.block
                ):
                    self.__create_task(
                        callback(update, context), update=update, is_error_handler=True
                    )
                else:
                    try:
                        await callback(update, context)
                    except ApplicationHandlerStop:
                        return True
                    except Exception as exc:
                        _logger.exception(
                            'An error was raised and an uncaught error was raised while '
                            'handling the error with an error_handler.',
                            exc_info=exc,
                        )
            return False

        _logger.exception('No error handlers are registered, logging exception.', exc_info=error)
        return False

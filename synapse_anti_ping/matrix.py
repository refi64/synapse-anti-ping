from typing import *

import asyncio
import concurrent.futures
import contextlib
import logging
import threading

import nio

from .config import Config

logger = logging.getLogger('synapse_anti_ping.Matrix')


class Matrix:
    def __init__(self, config: Config) -> None:
        self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True  # so ctrl-c cleanly exits
        self._init_event = asyncio.Event()

        self._config = config

        assert config.user.homeserver is not None
        self._client = nio.AsyncClient(config.user.homeserver, config.user.user)

    def start(self) -> None:
        self._thread.start()

    async def _initialize(self) -> None:
        logger.info('Matrix thread logging in')
        while True:
            result = await self._client.login(self._config.user.password)
            if isinstance(result, nio.LoginError):
                logger.error('Error occurred on login, trying again later: '
                             f'{result.message}')  # type: ignore
                await asyncio.sleep(2)
                continue

            break

        logger.info('Matrix thread joining rooms')
        await self._client.join(self._config.mjolnir.room)
        if self._config.mjolnir.room != self._config.log.room:
            await self._client.join(self._config.log.room)

        logger.info('Matrix thread initialized')
        self._init_event.set()

    async def _complete_send_message(self, message: str, *, room: str, formatted: str, notice: bool,
                                     join: bool) -> None:
        logger.info(f'Waiting to ensure init is complete')
        await self._init_event.wait()

        if join:
            await self._client.join(room)

        logger.info(f'Completing send message command')

        content = {
            'msgtype': 'm.notice' if notice else 'm.text',
            'body': message,
        }

        if formatted:
            content['format'] = 'org.matrix.custom.html'
            content['formatted_body'] = formatted

        await self._client.room_send(  # type: ignore
            room_id=room, message_type='m.room.message', content=content)

    def send_message(self,
                     message: str,
                     *,
                     room: str,
                     formatted: str = '',
                     notice: bool = False,
                     join: bool = True) -> 'concurrent.futures.Future[None]':
        logger.info(f'Message send in progress')
        return asyncio.run_coroutine_threadsafe(
            self._complete_send_message(message,
                                        room=room,
                                        formatted=formatted,
                                        notice=notice,
                                        join=join), self._loop)

    def _run(self) -> None:
        logger.info('Starting main loop')

        asyncio.ensure_future(self._initialize(), loop=self._loop)
        self._loop.run_forever()


class EventLimiter:
    class Inserter:
        def __init__(self, key: str) -> None:
            self.key = key
            self.future: 'concurrent.futures.Future[None]'

        def insert(self, future: 'concurrent.futures.Future[None]') -> None:
            assert self
            self.future = future

        def __bool__(self) -> bool:
            return bool(self.key)

    def __init__(self) -> None:
        self._active: Set[str] = set()

    @contextlib.contextmanager
    def insert(self, key: str) -> 'Iterator[Inserter]':
        if key in self._active:
            yield EventLimiter.Inserter('')
        else:
            inserter = EventLimiter.Inserter(key)
            yield inserter

            inserter.future.add_done_callback(lambda _: self._active.remove(key))
            self._active.add(key)


class Mjolnir:
    def __init__(self, config: Config, matrix: Matrix) -> None:
        self._config = config
        self._matrix = matrix

        self._in_progress_bans = EventLimiter()

    def ban(self, user: str) -> None:
        with self._in_progress_bans.insert(user) as inserter:
            if not inserter:
                return

            logger.info(f'Ban on {user} in progress')

            command = (f'{self._config.mjolnir.prefix} ban {self._config.mjolnir.banlist}'
                       f' user {user} spam')

            inserter.future = self._matrix.send_message(command, room=self._config.mjolnir.room)

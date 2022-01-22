import logging
from typing import Union, List

import nextcord
import psycopg2
import psycopg2.pool

from anisearch.config import DB_PASSWORD, DB_HOST, DB_NAME, DB_USER, DB_PORT
from anisearch.utils.constants import DEFAULT_PREFIX

log = logging.getLogger(__name__)


class DataBase:

    def __init__(self) -> None:
        self.pool = psycopg2.pool.SimpleConnectionPool(5, 20, host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER,
                                                       password=DB_PASSWORD)

    @staticmethod
    def _connect():
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        return conn

    def close(self) -> None:
        self.pool.closeall()

    def get_prefix(self, message: nextcord.Message) -> str:
        if isinstance(message.channel, nextcord.channel.DMChannel):
            return DEFAULT_PREFIX
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        'SELECT prefix FROM guilds WHERE id = %s;', (message.guild.id,))
                    prefix = cur.fetchone()[0]
                    return prefix
                except TypeError:
                    cur.execute('INSERT INTO guilds (id) VALUES (%s)',
                                (message.guild.id,))
                    conn.commit()
                    cur.execute(
                        'SELECT prefix FROM guilds WHERE id = %s;', (message.guild.id,))
                    prefix = cur.fetchone()[0]
                    log.info(
                        f'Inserted guild {message.guild.id}')
                    return prefix
        finally:
            self.pool.putconn(conn)

    def insert_guild(self, guild: nextcord.Guild) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE guilds SET prefix = %s WHERE id = %s;', (DEFAULT_PREFIX, guild.id,))
                cur.execute('INSERT INTO guilds (id) SELECT %s WHERE NOT EXISTS '
                            '(SELECT 1 FROM guilds WHERE id = %s);', (guild.id, guild.id,))
                conn.commit()
                log.info(
                    f'Inserted guild {guild.id}')
        finally:
            self.pool.putconn(conn)

    def delete_guild(self, guild: nextcord.Guild) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM guilds WHERE id = %s;', (guild.id,))
                conn.commit()
                log.info(
                    f'Deleted guild {guild.id}')
        finally:
            self.pool.putconn(conn)

    def update_prefix(self, message: nextcord.Message, prefix: str) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE guilds SET prefix = %s WHERE id = %s;', (prefix, message.guild.id,))
                cur.execute(
                    'SELECT prefix FROM guilds WHERE id = %s;', (message.guild.id,))
                prefix = cur.fetchone()[0]
                conn.commit()
                log.info(
                    f'Changed prefix for guild {message.guild.id} to {prefix}')
        finally:
            self.pool.putconn(conn)

    def insert_profile(self, site: str, username: str, id_: int) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                if site == 'anilist':
                    cur.execute(
                        'UPDATE users SET anilist = %s WHERE id = %s;', (username, id_,))
                    cur.execute('INSERT INTO users (id, anilist) SELECT %s, %s WHERE NOT EXISTS '
                                '(SELECT 1 FROM users WHERE id = %s);', (id_, username, id_,))
                elif site == 'myanimelist':
                    cur.execute(
                        'UPDATE users SET myanimelist = %s WHERE id = %s;', (username, id_,))
                    cur.execute('INSERT INTO users (id, myanimelist) SELECT %s, %s WHERE NOT EXISTS '
                                '(SELECT 1 FROM users WHERE id = %s);', (id_, username, id_,))
                elif site == 'kitsu':
                    cur.execute(
                        'UPDATE users SET kitsu = %s WHERE id = %s;', (username, id_,))
                    cur.execute('INSERT INTO users (id, kitsu) SELECT %s, %s WHERE NOT EXISTS '
                                '(SELECT 1 FROM users WHERE id = %s);', (id_, username, id_,))
                conn.commit()
                log.info(f'Set {site} profile for user {id_} to {username}')
        finally:
            self.pool.putconn(conn)

    def select_profile(self, site: str, id_: int) -> Union[str, None]:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                try:
                    if site == 'anilist':
                        cur.execute(
                            'SELECT anilist FROM users WHERE id = %s;', (id_,))
                        profile = cur.fetchone()[0]
                    elif site == 'myanimelist':
                        cur.execute(
                            'SELECT myanimelist FROM users WHERE id = %s;', (id_,))
                        profile = cur.fetchone()[0]
                    elif site == 'kitsu':
                        cur.execute(
                            'SELECT kitsu FROM users WHERE id = %s;', (id_,))
                        profile = cur.fetchone()[0]
                    return profile
                except TypeError:
                    return None
        finally:
            self.pool.putconn(conn)

    def check_user(self, id_: int) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT EXISTS(SELECT 1 FROM users WHERE id = %s);', (id_,))
                user = cur.fetchone()[0]
                return user
        finally:
            self.pool.putconn(conn)

    def delete_user(self, id_: int) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM users WHERE id = %s;', (id_,))
                conn.commit()
                log.info(f'Removed user {id_}')
        finally:
            self.pool.putconn(conn)

    def set_channel(self, channel_id: int, guild: nextcord.Guild) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE guilds SET channel = %s WHERE id = %s;', (channel_id, guild.id,))
                cur.execute(
                    'SELECT channel FROM guilds WHERE id = %s;', (guild.id,))
                channel_id = cur.fetchone()[0]
                conn.commit()
                log.info(
                    f'Set channel for guild {guild.id} to {channel_id}')
        finally:
            self.pool.putconn(conn)

    def get_channel(self, guild: nextcord.Guild) -> Union[int, None]:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        'SELECT channel FROM guilds WHERE id = %s;', (guild.id,))
                    channel = cur.fetchone()[0]
                    return channel
                except TypeError:
                    return None
        finally:
            self.pool.putconn(conn)

    def set_role(self, role_id: int, guild: nextcord.Guild) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE guilds SET role = %s WHERE id = %s;', (role_id, guild.id,))
                cur.execute(
                    'SELECT role FROM guilds WHERE id = %s;', (guild.id,))
                role_id = cur.fetchone()[0]
                conn.commit()
                log.info(
                    f'Set role for guild {guild.id} to {role_id}')
        finally:
            self.pool.putconn(conn)

    def get_role(self, guild: nextcord.Guild) -> Union[int, None]:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        'SELECT role FROM guilds WHERE id = %s;', (guild.id,))
                    role = cur.fetchone()[0]
                    return role
                except TypeError:
                    return None
        finally:
            self.pool.putconn(conn)

    def add_watchlist(self, anime_id: int, guild_id: int):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE guilds SET watchlist = array_cat(watchlist, '{%s}') WHERE id = %s;",
                            (anime_id, guild_id,))
                conn.commit()
                log.info(f'Added {anime_id} to the server watchlist of guild {guild_id}')
        finally:
            self.pool.putconn(conn)

    def remove_watchlist(self, anime_id: int, guild_id: int):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE guilds SET watchlist = array_remove(watchlist, %s) WHERE id = %s;",
                            (anime_id, guild_id,))
                conn.commit()
                log.info(f'Removed {anime_id} from the server watchlist of guild {guild_id}')
        finally:
            self.pool.putconn(conn)

    def get_watchlist(self, guild_id: int) -> List[int]:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT watchlist FROM guilds WHERE id = %s;', (guild_id,))
                id_list = cur.fetchone()[0]
                return id_list
        finally:
            self.pool.putconn(conn)

    def clear_watchlist(self, guild_id: int):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE guilds SET watchlist = '{}' WHERE id = %s;", (guild_id,))
                conn.commit()
        finally:
            self.pool.putconn(conn)

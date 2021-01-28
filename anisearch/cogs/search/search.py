"""
This file is part of the AniSearch Discord Bot.

Copyright (C) 2021 IchBinLeoon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import datetime
import logging
import random
import re
from typing import Union, List, Dict, Any, Optional

import discord
from discord import Embed
from discord.ext import commands, menus
from discord.ext.commands import Context

from anisearch.bot import AniSearchBot
from anisearch.utils.checks import is_adult
from anisearch.utils.constants import ERROR_EMBED_COLOR, DEFAULT_EMBED_COLOR
from anisearch.utils.formats import get_media_title, get_media_stats, format_description, format_date, \
    get_char_staff_name, format_media_type
from anisearch.utils.paginator import EmbedListMenu

log = logging.getLogger(__name__)


class Search(commands.Cog, name='Search'):
    """
    Search cog.
    """

    def __init__(self, bot: AniSearchBot):
        """
        Initializes the `Search` cog.
        """
        self.bot = bot

    async def anilist_search(self, ctx: Context, search: str, type_: str) -> Union[List[Embed], None]:
        """
        Returns a list of Discord embeds with the retrieved anilist data about the searched entry.

        Args:
            ctx (Context): The context in which the command was invoked under.
            search (str): The entry to be searched for.
            type_ (str): The type to be searched for (`anime`, `manga`, `character`, `staff`, `studio`).

        Returns:
            list (Embed): A list of discord embeds.
            None: If no entries were found.
        """
        embeds = []
        data = None

        try:
            if type_ == 'anime':
                data = await self.bot.anilist.media(search=search, page=1, perPage=15, type=type_.upper())
            elif type_ == 'manga':
                data = await self.bot.anilist.media(search=search, page=1, perPage=15, type=type_.upper())
            elif type_ == 'character':
                data = await self.bot.anilist.character(search=search, page=1, perPage=15)
            elif type_ == 'staff':
                data = await self.bot.anilist.staff(search=search, page=1, perPage=15)
            elif type_ == 'studio':
                data = await self.bot.anilist.studio(search=search, page=1, perPage=15)

        except Exception as e:
            log.exception(e)

            embed = discord.Embed(
                title=f'An error occurred while searching for the {type_} `{search}`. Try again.',
                color=ERROR_EMBED_COLOR)
            embeds.append(embed)

            return embeds

        if data is not None:
            for page, entry in enumerate(data):

                embed = None

                try:
                    if type_ == 'anime':
                        embed = self.get_media_embed(entry, page + 1, len(data))
                    elif type_ == 'manga':
                        embed = self.get_media_embed(entry, page + 1, len(data))
                    elif type_ == 'character':
                        embed = self.get_character_embed(entry, page + 1, len(data))
                    elif type_ == 'staff':
                        embed = self.get_staff_embed(entry, page + 1, len(data))
                    elif type_ == 'studio':
                        embed = self.get_studio_embed(entry, page + 1, len(data))

                    if is_adult(entry):
                        if not ctx.channel.is_nsfw():
                            embed = discord.Embed(
                                title='Error',
                                color=ERROR_EMBED_COLOR,
                                description=f'Adult content. No NSFW channel.')
                            embed.set_footer(
                                text=f'Provided by https://anilist.co/ • Page {page + 1}/{len(data)}')

                except Exception as e:
                    log.exception(e)

                    embed = discord.Embed(
                        title='Error',
                        color=ERROR_EMBED_COLOR,
                        description=f'An error occurred while loading the embed for the {type_}.')
                    embed.set_footer(
                        text=f'Provided by https://anilist.co/ • Page {page + 1}/{len(data)}')

                embeds.append(embed)

            return embeds
        return None

    async def anilist_random(self, ctx: Context, search: str, type_: str, format_in: List[str]) -> Union[Embed, None]:
        """
        Returns a Discord embed with the retrieved anilist data about a random media of a specified genre.

        Args:
            ctx (Context): The context in which the command was invoked under.
            search (str): The media genre to be searched for.
            type_ (str): The media search type (`anime`, `manga`).
            format_in (list): The media format.

        Returns:
            Embed: A discord embed.
            None: If no entry was found.
        """
        try:

            data = await self.bot.anilist.genre(genre=search, page=1, perPage=1, type=type_.upper(),
                                                format_in=format_in)

            if data.get('data')['Page']['media'] is not None and len(data.get('data')['Page']['media']) > 0:
                page = random.randrange(1, data.get('data')['Page']['pageInfo']['lastPage'])
                data = await self.bot.anilist.genre(genre=search, page=page, perPage=1, type=type_.upper(),
                                                    format_in=format_in)

            else:

                data = await self.bot.anilist.tag(tag=search, page=1, perPage=1, type=type_.upper(),
                                                  format_in=format_in)

                if data.get('data')['Page']['media'] is not None and len(data.get('data')['Page']['media']) > 0:
                    page = random.randrange(1, data.get('data')['Page']['pageInfo']['lastPage'])
                    data = await self.bot.anilist.tag(tag=search, page=page, perPage=1, type=type_.upper(),
                                                      format_in=format_in)
                else:
                    return None

        except Exception as e:
            log.exception(e)

            embed = discord.Embed(
                title=f'An error occurred while searching for an {type_} with the genre `{search}`.',
                color=ERROR_EMBED_COLOR)

            return embed

        if data.get('data')['Page']['media'] is not None and len(data.get('data')['Page']['media']) > 0:

            try:
                embed = self.get_media_embed(data.get('data')['Page']['media'][0])

                if is_adult(data.get('data')['Page']['media'][0]):
                    if not ctx.channel.is_nsfw():
                        embed = discord.Embed(title='Error', color=ERROR_EMBED_COLOR,
                                              description=f'Adult content. No NSFW channel.')

            except Exception as e:
                log.exception(e)

                embed = discord.Embed(
                    title=f'An error occurred while searching for an {type_} with the genre `{search}`.',
                    color=ERROR_EMBED_COLOR)

            return embed

        return None

    @staticmethod
    def get_media_embed(data: Dict[str, Any], page: Optional[int] = None, pages: Optional[int] = None) -> Embed:
        """
        Returns the `media` embed.

        Args:
            data (dict): The data about the anime.
            page (int, optional): The current page.
            pages (page, optional): The number of all pages.

        Returns:
            Embed: A discord embed.
        """
        embed = discord.Embed(
            title=get_media_title(data.get('title')),
            description=format_description(data.get('description'), 400) if data.get('description')
            else 'N/A',
            colour=int('0x' + data.get('coverImage')['color'].replace('#', ''), 0) if data.get('coverImage')['color']
            else DEFAULT_EMBED_COLOR
        )

        if data.get('coverImage')['large']:
            embed.set_thumbnail(url=data.get('coverImage')['large'])

        if data.get('bannerImage'):
            embed.set_image(url=data.get('bannerImage'))

        embed.set_author(name=get_media_stats(data.get('format'), data.get('type'), data.get('status'),
                                              data.get('meanScore')))

        if data.get('type') == 'ANIME':
            if data.get('status') == 'RELEASING':
                try:
                    if data.get('nextAiringEpisode')['episode']:
                        aired_episodes = str(
                            data.get('nextAiringEpisode')['episode'] - 1)
                        next_episode_time = 'N/A'
                        if data.get('nextAiringEpisode')['timeUntilAiring']:
                            seconds = data.get('nextAiringEpisode')[
                                'timeUntilAiring']
                            next_episode_time = str(
                                datetime.timedelta(seconds=seconds))
                        embed.add_field(name='Aired Episodes', value=f'{aired_episodes} (Next in {next_episode_time})',
                                        inline=True)
                except TypeError:
                    embed.add_field(name='Episodes', value='N/A', inline=True)
            elif data.get('episodes'):
                embed.add_field(name='Episodes', value=data.get(
                    'episodes'), inline=True)

        elif data.get('type') == 'MANGA':
            embed.add_field(name='Chapters', value=data.get(
                'chapters') if data.get('chapters') else 'N/A', inline=True)
            embed.add_field(name='Volumes', value=data.get(
                'volumes') if data.get('volumes') else 'N/A', inline=True)
            embed.add_field(name='Source', value=data.get('source').replace('_', ' ').title() if data.get('source') else
                            'N/A', inline=True)

        date_name = 'Released'
        if data.get('type') == 'ANIME':
            date_name = 'Aired'
        elif data.get('type') == 'MANGA':
            date_name = 'Published'
        if data.get('startDate')['day']:
            try:
                start_date = format_date(data.get('startDate')['day'], data.get('startDate')['month'],
                                         data.get('startDate')['year'])
                end_date = '?'
                if data.get('endDate')['day']:
                    end_date = format_date(data.get('endDate')['day'], data.get('endDate')['month'],
                                           data.get('endDate')['year'])
                embed.add_field(name=date_name, value='{} to {}'.format(
                    start_date, end_date), inline=False)
            except TypeError:
                embed.add_field(name=date_name, value='N/A', inline=False)
        else:
            embed.add_field(name=date_name, value='N/A', inline=False)

        if data.get('type') == 'ANIME':
            duration = 'N/A'
            if data.get('duration'):
                duration = str(data.get(
                    'duration')) + ' {}'.format('min' if data.get('episodes') == 1 else 'min each')
            embed.add_field(name='Duration', value=duration, inline=True)
            embed.add_field(name='Source', value=data.get('source').replace('_', ' ').title() if data.get('source') else
                            'N/A', inline=True)
            try:
                studio = data.get('studios')['nodes'][0]['name']
            except IndexError:
                studio = 'N/A'
            embed.add_field(name='Studio', value=studio, inline=True)

        if data.get('synonyms'):
            embed.add_field(name='Synonyms', value=', '.join(
                data.get('synonyms')), inline=False)

        if data.get('genres'):
            embed.add_field(name='Genres', value=', '.join(
                data.get('genres')), inline=False)

        external_sites = []
        if data.get('trailer'):
            if data.get('trailer')['site'] == 'youtube':
                trailer_site = 'https://www.youtube.com/watch?v=' + \
                               data.get('trailer')['id']
                external_sites.append('[Trailer]({})'.format(trailer_site))
        if data.get('externalLinks'):
            for i in data.get('externalLinks'):
                external_sites.append('[{}]({})'.format(i['site'], i['url']))
        if len(external_sites) > 1:
            external_name = 'External sites'
            if data.get('type') == 'ANIME':
                external_name = 'Streaming and external sites'
            embed.add_field(name=external_name, value=' | '.join(
                external_sites), inline=False)

        sites = []
        if data.get('siteUrl'):
            sites.append('[Anilist]({})'.format(data.get('siteUrl')))
            embed.url = data.get('siteUrl')
        if data.get('idMal'):
            sites.append(
                '[MyAnimeList](https://myanimelist.net/anime/{})'.format(str(data.get('idMal'))))
        if len(sites) > 0:
            embed.add_field(name='Find out more',
                            value=' | '.join(sites), inline=False)

        if page is not None and pages is not None:
            embed.set_footer(
                text=f'Provided by https://anilist.co/ • Page {page}/{pages}')
        else:
            embed.set_footer(text=f'Provided by https://anilist.co/')

        return embed

    @staticmethod
    def get_character_embed(data: Dict[str, Any], page: int, pages: int) -> Embed:
        """
        Returns the `character` embed.

        Args:
            data (dict): The data about the character.
            page (int): The current page.
            pages (page): The number of all pages.

        Returns:
            Embed: A discord embed.
        """
        embed = discord.Embed(
            color=DEFAULT_EMBED_COLOR,
            description=format_description(data.get('description'), 1000) if data.get('description') else 'N/A',
            title=get_char_staff_name(data.get('name'))
        )

        if data.get('image')['large']:
            embed.set_thumbnail(url=data.get('image')['large'])

        if data.get('siteUrl'):
            embed.url = data.get('siteUrl')

        if data.get('name')['alternative'] != ['']:
            embed.add_field(name='Synonyms', value=', '.join(
                data.get('name')['alternative']), inline=False)

        if data.get('media')['nodes']:
            media = []
            for x in data.get('media')['nodes']:
                media_name = '[{}]({})'.format(
                    [x][0]['title']['romaji'], [x][0]['siteUrl'])
                media.append(media_name)
            if len(media) > 5:
                media = media[0:5]
                media[4] = media[4] + '...'
            embed.add_field(name='Appearances',
                            value=' | '.join(media), inline=False)
        embed.set_footer(
            text=f'Provided by https://anilist.co/ • Page {page}/{pages}')

        return embed

    @staticmethod
    def get_staff_embed(data: Dict[str, Any], page: int, pages: int) -> Embed:
        """
        Returns the `staff` embed.

        Args:
            data (dict): The data about the staff.
            page (int): The current page.
            pages (page): The number of all pages.

        Returns:
            Embed: A discord embed.
        """
        embed = discord.Embed(
            title=get_char_staff_name(data.get('name')),
            description=format_description(data.get('description'), 1000) if data.get('description') else 'N/A',
            color=DEFAULT_EMBED_COLOR
        )

        if data.get('image')['large']:
            embed.set_thumbnail(url=data.get('image')['large'])

        if data.get('name')['native'] is None:
            embed.title = data.get('name')['full']

        if data.get('siteUrl'):
            embed.url = data.get('siteUrl')

        if data.get('staffMedia')['nodes']:
            staff_roles = []
            for x in data.get('staffMedia')['nodes']:
                media_name = '[{}]({})'.format(
                    [x][0]['title']['romaji'], [x][0]['siteUrl'])
                staff_roles.append(media_name)
            if len(staff_roles) > 5:
                staff_roles = staff_roles[0:5]
                staff_roles[4] = staff_roles[4] + '...'
            embed.add_field(name='Staff Roles', value=' | '.join(
                staff_roles), inline=False)

        if data.get('characters')['nodes']:
            characters = []
            for x in data.get('characters')['nodes']:
                character_name = '[{}]({})'.format([x][0]['name']['full'],
                                                   [x][0]['siteUrl'])
                characters.append(character_name)
            if len(characters) > 5:
                characters = characters[0:5]
                characters[4] = characters[4] + '...'
            embed.add_field(name='Character Roles',
                            value=' | '.join(characters), inline=False)

        embed.set_footer(
            text=f'Provided by https://anilist.co/ • Page {page}/{pages}')

        return embed

    @staticmethod
    def get_studio_embed(data: Dict[str, Any], page: int, pages: int) -> Embed:
        """
        Returns the `studio` embed.

        Args:
            data (dict): The data about the studio.
            page (int): The current page.
            pages (page): The number of all pages.

        Returns:
            Embed: A discord embed.
        """
        embed = discord.Embed(
            color=DEFAULT_EMBED_COLOR,
            title=data.get('name')
        )

        if data.get('siteUrl'):
            embed.url = data.get('siteUrl')

        if data.get('media')['nodes']:
            medias = []
            for x in data.get('media')['nodes']:
                media_name = [x][0]['title']['romaji']
                media_link = [x][0]['siteUrl']
                try:
                    media_type = format_media_type([x][0]['format'])
                except KeyError:
                    media_type = 'N/A'
                media_count = [x][0]['episodes']
                list_object = '[{}]({}) - Type: {} - Episodes: {}'.format(media_name, media_link,
                                                                          media_type, media_count)
                medias.append(list_object)
            if len(medias) > 10:
                medias = medias[0:10]
                medias[9] = medias[9] + '...'
            embed.add_field(name='Most Popular Productions',
                            value='\n'.join(medias), inline=False)

        embed.set_footer(
            text=f'Provided by https://anilist.co/ • Page {page}/{pages}')

        return embed

    @commands.command(name='anime', aliases=['a', 'ani'], usage='anime <title>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def anime(self, ctx: Context, *, title: str):
        """
        Searches for an anime with the given title and displays information about the search results such as type,
        status, episodes, description, and more!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, title, 'anime')
            if embeds:
                menu = menus.MenuPages(source=EmbedListMenu(
                    embeds), clear_reactions_after=True, timeout=30)
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f'The anime `{title}` could not be found.', color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='manga', aliases=['m'], usage='manga <title>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def manga(self, ctx: Context, *, title: str):
        """
        Searches for a manga with the given title and displays information about the search results such as type,
        status, chapters, description, and more!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, title, 'manga')
            if embeds:
                menu = menus.MenuPages(source=EmbedListMenu(
                    embeds), clear_reactions_after=True, timeout=30)
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f'The manga `{title}` could not be found.',
                    color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='character', aliases=['c', 'char'], usage='character <name>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def character(self, ctx: Context, *, name: str):
        """
        Searches for a character with the given name and displays information about the search results such as
        description, synonyms, and appearances!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, 'character')
            if embeds:
                menu = menus.MenuPages(source=EmbedListMenu(
                    embeds), clear_reactions_after=True, timeout=30)
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f'The character `{name}` could not be found.',
                    color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='staff', usage='staff <name>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def staff(self, ctx: Context, *, name: str):
        """
        Searches for a staff with the given name and displays information about the search results such as description,
        staff roles, and character roles!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, 'staff')
            if embeds:
                menu = menus.MenuPages(source=EmbedListMenu(
                    embeds), clear_reactions_after=True, timeout=30)
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f'The staff `{name}` could not be found.',
                    color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='studio', usage='studio <name>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def studio(self, ctx: Context, *, name: str):
        """
        Searches for a studio with the given name and displays information about the search results such as the studio
        productions!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, 'studio')
            if embeds:
                menu = menus.MenuPages(source=EmbedListMenu(
                    embeds), clear_reactions_after=True, timeout=30)
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f'The studio `{name}` could not be found.',
                    color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='random', aliases=['r'], usage='random <anime|manga> <genre>', ignore_extra=False)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def random(self, ctx: Context, media: str, *, genre: str):
        """
        Displays a random anime or manga of the specified genre.
        """
        async with ctx.channel.typing():
            if media.lower() == 'anime':
                embed = await self.anilist_random(ctx, genre, 'anime', ['TV', 'MOVIE', 'OVA', 'ONA', 'TV_SHORT',
                                                                        'MUSIC', 'SPECIAL'])
                if embed:
                    await ctx.channel.send(embed=embed)
                else:
                    embed = discord.Embed(title=f'An anime with the genre `{genre}` could not be found.',
                                          color=ERROR_EMBED_COLOR)
                    await ctx.channel.send(embed=embed)
            elif media.lower() == 'manga':
                embed = await self.anilist_random(ctx, genre, 'manga', ['MANGA', 'ONE_SHOT', 'NOVEL'])
                if embed:
                    await ctx.channel.send(embed=embed)
                else:
                    embed = discord.Embed(title=f'A manga with the genre `{genre}` could not be found.',
                                          color=ERROR_EMBED_COLOR)
                    await ctx.channel.send(embed=embed)
            else:
                ctx.command.reset_cooldown(ctx)
                raise discord.ext.commands.BadArgument

    @commands.command(name='themes', usage='themes <anime>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def themes(self, ctx: Context, *, anime: str):
        """
        Searches for the openings and endings of the given anime and displays them.
        """
        async with ctx.channel.typing():
            data = await self.bot.animethemes.search(anime, 5, ['anime'])
            if data.get('anime'):
                embeds = []
                for page, entry in enumerate(data.get('anime')):
                    try:

                        embed = discord.Embed(color=DEFAULT_EMBED_COLOR, title=entry.get('name'))

                        if entry.get('images'):
                            embed.set_thumbnail(url=entry.get('images')[0]['link'])

                        count = 1
                        sites = []
                        for site in entry.get('resources'):
                            site_string = f'[{site.get("site")}]({site.get("link")})'
                            sites.append(site_string)
                        embed.description = ' | '.join(sites)

                        for theme in entry.get('themes'):
                            if count >= 15:
                                break
                            theme_string = '**Title:** {}{}\n[Link](http://animethemes.moe/video/{})' \
                                .format(theme.get('song')['title'],
                                        ('\n**Artist:** ' + theme.get('song')['artists'][0]['name']) if
                                        theme.get('song')['artists'] else
                                        None, theme.get('entries')[0]['videos'][0]['basename'] if
                                        theme.get('entries')[0]['videos'][0]['basename'] else 'N/A')
                            embed.add_field(
                                name=theme.get('slug').replace('OP', 'Opening ').replace('ED', 'Ending '),
                                value=theme_string, inline=False)
                            count += 1

                        embed.set_footer(
                            text=f'Provided by https://animethemes.moe/ • Page {page + 1}/{len(data.get("anime"))}')

                    except Exception as e:
                        log.exception(e)
                        embed = discord.Embed(
                            title='Error',
                            description=f'An error occurred while loading the embed for the anime.',
                            color=ERROR_EMBED_COLOR)
                        embed.set_footer(
                            text=f'Provided by https://animethemes.moe/ • Page {page + 1}/{len(data.get("anime"))}')
                    embeds.append(embed)

                menu = menus.MenuPages(source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30)
                await menu.start(ctx)

            else:
                embed = discord.Embed(title=f'No themes for the anime `{anime}` found.', color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='theme', usage='theme <OP|ED> <anime>', ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def theme(self, ctx: Context, theme: str, *, anime: str):
        """
        Displays a specific opening or ending of the given anime.
        """
        async with ctx.channel.typing():
            data = await self.bot.animethemes.search(anime, 1, ['anime'])
            if data.get('anime'):
                anime_ = data.get('anime')[0]

                for entry in anime_.get('themes'):
                    if theme.upper() == entry.get('slug') or \
                            (theme.upper() == 'OP' and entry.get('slug') == 'OP1') or \
                            (theme.upper() == 'ED' and entry.get('slug') == 'ED1') or \
                            (theme.upper() == 'OP1' and entry.get('slug') == 'OP') or \
                            (theme.upper() == 'ED1' and entry.get('slug') == 'ED'):

                        embed = discord.Embed(title=anime_.get('name'), colour=DEFAULT_EMBED_COLOR)

                        if anime_.get('images'):
                            embed.set_thumbnail(url=anime_.get('images')[0]['link'])

                        info = []
                        sites = []

                        for site in anime_.get('resources'):
                            site_string = f'[{site.get("site")}]({site.get("link")})'
                            sites.append(site_string)
                        sites_joined = ' | '.join(sites) + '\n'
                        info.append(sites_joined)

                        if entry.get('song')['title']:
                            info.append('**Title:** ' + entry.get('song')['title'])

                        if entry.get('song')['artists']:
                            if len(entry.get('song')['artists']) > 1:
                                artists = []
                                for artist in entry.get('song')['artists']:
                                    artists.append(artist.get('name'))
                                info.append('**Artists:** ' + ', '.join(artists))
                            else:
                                info.append('**Artist:** ' + entry.get('song')['artists'][0]['name'])

                        if len(info) > 0:
                            embed.description = '\n'.join(info)

                        embed.set_footer(
                            text=f'Provided by https://animethemes.moe/')

                        await ctx.channel.send(embed=embed)
                        return await ctx.channel.send(
                            f'http://animethemes.moe/video/{entry.get("entries")[0]["videos"][0]["basename"]}')

                embed = discord.Embed(
                    title=f'Cannot find `{theme.upper()}` for the anime `{anime}`.', color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

            else:
                embed = discord.Embed(title=f'No theme for the anime `{anime}` found.', color=ERROR_EMBED_COLOR)
                await ctx.channel.send(embed=embed)

    @commands.command(name='trace', aliases=['t'], usage='trace <image-url|with image as attachment>',
                      ignore_extra=False)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def trace(self, ctx, trace: Optional[str] = None):
        """
        Tries to find the anime the image is from through the image url or the image as attachment.
        """
        async with ctx.channel.typing():
            url = None
            if trace is None:
                if ctx.message.attachments:
                    url = ctx.message.attachments[0].url
                else:
                    embed = discord.Embed(title='No image to look for the anime.', color=ERROR_EMBED_COLOR)
                    await ctx.channel.send(embed=embed)
            else:
                url = trace
            if url:
                if not url.endswith(('.jpg', '.png', '.bmp', '.jpeg')):
                    embed = discord.Embed(title='No correct url specified (`.jpg`, `.png`, `.bmp`, `.jpeg`).',
                                          color=ERROR_EMBED_COLOR)
                    await ctx.channel.send(embed=embed)
                else:
                    try:
                        data = await self.bot.tracemoe.search(url)

                    except Exception as e:
                        log.exception(e)

                        embed = discord.Embed(
                            title=f'An error occurred while searching for the anime or the link is invalid.',
                            color=ERROR_EMBED_COLOR)

                        return await ctx.channel.send(embed=embed)

                    if data:
                        embeds = []
                        for page, anime in enumerate(data):
                            try:
                                embed = discord.Embed(color=DEFAULT_EMBED_COLOR)

                                if anime.get('title_english') is None or anime.get('title_english') == \
                                        anime.get('title_romaji'):
                                    embed.title = anime.get('title_romaji')
                                else:
                                    embed.title = '{} ({})'.format(anime.get('title_romaji'),
                                                                   anime.get('title_english'))

                                try:
                                    image_url = \
                                        f"https://trace.moe/thumbnail.php?anilist_id={anime.get('anilist_id')}&file=" \
                                        f"{anime.get('filename')}&t={anime.get('at')}&token={anime.get('tokenthumb')}" \
                                        .replace(' ', '%20')
                                    embed.set_image(url=image_url)
                                except Exception as e:
                                    log.exception(e)

                                if anime.get('episode'):
                                    embed.add_field(name='Episode', value=anime.get('episode'), inline=False)
                                if anime.get('synonyms'):
                                    embed.add_field(name='Synonyms', value=', '.join(anime.get('synonyms')),
                                                    inline=False)
                                if anime.get('anilist_id'):
                                    anilist_link = f'https://anilist.co/anime/{str(anime.get("anilist_id"))}'
                                    embed.add_field(name='Anilist Link', value=anilist_link, inline=False)
                                if anime.get('mal_id'):
                                    myanimelist_link = f'https://myanimelist.net/anime/{str(anime.get("mal_id"))}'
                                    embed.add_field(name='MyAnimeList Link', value=myanimelist_link, inline=False)

                                embed.set_footer(
                                    text=f'Provided by https://trace.moe • Page {page + 1}/{len(data)}')

                            except Exception as e:
                                log.info(e)

                                embed = discord.Embed(title='Error', color=DEFAULT_EMBED_COLOR,
                                                      description='An error occurred while loading the embed.')
                                embed.set_footer(
                                    text=f'Provided by https://trace.moe/ • Page {page + 1}/{len(data.get("docs"))}')

                            embeds.append(embed)

                        menu = menus.MenuPages(source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30)
                        await menu.start(ctx)

                    else:
                        embed = discord.Embed(title='No anime found.', color=ERROR_EMBED_COLOR)
                        await ctx.channel.send(embed=embed)

    @commands.command(name='source', aliases=['sauce'], usage='source <image-url|with image as attachment>',
                      ignore_extra=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def source(self, ctx: Context, source: Optional[str] = None):
        """
        Tries to find the source of an image through the image url or the image as attachment.
        """
        async with ctx.channel.typing():
            url = None
            if source is None:
                if ctx.message.attachments:
                    url = ctx.message.attachments[0].url
                else:
                    embed = discord.Embed(title='No image to look for the source.', color=ERROR_EMBED_COLOR)
                    await ctx.channel.send(embed=embed)
            else:
                url = source
            if url:
                if not url.endswith(('.jpg', '.png', '.bmp', '.jpeg')):
                    embed = discord.Embed(title='No correct url specified (`.jpg`, `.png`, `.bmp`, `.jpeg`).',
                                          color=ERROR_EMBED_COLOR)
                    await ctx.channel.send(embed=embed)
                else:
                    try:
                        r = await self.bot.session.get(f'http://saucenao.com/search.php?url={url}')
                        if r.status == 200:
                            content = await r.text()
                        else:
                            content = None

                        material = re.search(r'<strong>Material: </strong>(.*?)<br', content)
                        artist = re.search(r'<strong>Creator: </strong>(.*?)<br', content)
                        characters = re.search(r'<strong>Characters: </strong><br />(.*?)<br /></div>', content)
                        pixiv = re.search(r'<strong>Pixiv ID: </strong><a href=\"(.*?)\" class', content)
                        danbooru = re.search(r'<a href=\"https://danbooru\.donmai\.us/post/show/(\d+)\">', content)
                        gelbooru = re.search(
                            r'<a href=\"https://gelbooru\.com/index\.php\?page=post&s=view&id=(\d+)\">', content)
                        yandere = re.search(r'<a href=\"https://yande\.re/post/show/(\d+)\">', content)
                        konachan = re.search(r'<a href=\"http://konachan\.com/post/show/(\d+)\">', content)
                        sankaku = re.search(r'<a href=\"https://chan\.sankakucomplex\.com/post/show/(\d+)\">', content)

                        embed = discord.Embed(title='Source', color=DEFAULT_EMBED_COLOR)
                        embed.set_thumbnail(url=url)

                        if material:
                            embed.add_field(name='Material', value=material.group(1), inline=False)
                        if artist:
                            embed.add_field(name='Artist', value=artist.group(1), inline=False)
                        if characters:
                            embed.add_field(name='Characters', value=str(characters.group(1)).replace('<br />', ', '),
                                            inline=False)
                        if pixiv:
                            embed.add_field(name='Pixiv', value=pixiv.group(1), inline=False)
                        if danbooru:
                            embed.add_field(name='Danbooru', value='https://danbooru.donmai.us/post/show/' +
                                                                   danbooru.group(1), inline=False)
                        if gelbooru:
                            embed.add_field(name='Gelbooru',
                                            value='https://gelbooru.com/index.php?page=post&s=view&id=' +
                                                  gelbooru.group(1), inline=False)
                        if yandere:
                            embed.add_field(name='Yande.re',
                                            value='https://yande.re/post/show/' + yandere.group(1), inline=False)
                        if konachan:
                            embed.add_field(name='Konachan', value='http://konachan.com/post/show/' + konachan.group(1),
                                            inline=False)
                        if sankaku:
                            embed.add_field(name='Sankaku', value='https://chan.sankakucomplex.com/post/show/' +
                                                                  sankaku.group(1), inline=False)
                        embed.set_footer(text='Provided by https://saucenao.com/')

                        if material or artist or characters or pixiv or danbooru or gelbooru or yandere or konachan or \
                                sankaku:
                            await ctx.channel.send(embed=embed)

                        else:
                            embed = discord.Embed(title='No source found.', color=ERROR_EMBED_COLOR)
                            await ctx.channel.send(embed=embed)

                    except Exception as e:
                        log.exception(e)

                        embed = discord.Embed(
                            title=f'An error occurred while searching for the source or the link is invalid.',
                            color=ERROR_EMBED_COLOR)

                        return await ctx.channel.send(embed=embed)


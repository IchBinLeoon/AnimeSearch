import platform
import discord
from anisearch.utils.database.prefix import get_command_prefix
from anisearch.utils.database.prefix import insert_prefix
from anisearch.utils.database.prefix import delete_prefix
from discord.ext import commands
from discord.ext.commands import Bot as BotBase
from anisearch import config
from anisearch.utils.logger import logger

version = '1.6'

initial_extensions = [
    'anisearch.cogs.help',
    'anisearch.cogs.admin',
    'anisearch.cogs.events',
    'anisearch.cogs.settings',
    'anisearch.cogs.anime',
    'anisearch.cogs.manga',
    'anisearch.cogs.character',
    'anisearch.cogs.staff',
    'anisearch.cogs.studio',
    'anisearch.cogs.random',
    'anisearch.cogs.anilist',
    'anisearch.cogs.myanimelist',
    'anisearch.cogs.kitsu',
    'anisearch.cogs.profile',
    'anisearch.cogs.image',
    'anisearch.cogs.theme'
]


class AniSearchBot(BotBase):

    def __init__(self):
        intents = discord.Intents(messages=True, guilds=True, reactions=True)
        super().__init__(command_prefix=get_command_prefix, intents=intents, owner_id=int(config.OWNER_ID))

    def load_cogs(self):
        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                pass
            except Exception as exception:
                logger.exception(exception)
        logger.info('Cogs loaded {}/{}'.format(len(self.cogs), len(initial_extensions)))

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Logged in as {}'.format(self.user))
        logger.info('Bot-Name: {}'.format(self.user.name))
        logger.info('Bot-Discriminator: {}'.format(self.user.discriminator))
        logger.info('Bot-ID: {}'.format(self.user.id))
        logger.info('Bot-Version: {}'.format(version))
        logger.info('Discord.py-Version: {}'.format(discord.__version__))
        logger.info('Python-Version: {}'.format(platform.python_version()))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='as!help'),
                                   status=discord.Status.online)
        self.load_cogs()
        logger.info('Bot is online')

    @commands.Cog.listener()
    async def on_connect(self):
        logger.info('Connected to Discord')

    @commands.Cog.listener()
    async def on_disconnect(self):
        logger.info('Disconnected from Discord')

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            logger.info('Private Message | Author: {} | Content: {}'.format(ctx.author, ctx.message.content))
        else:
            logger.info('Server: {} | Author: {} | Content: {}'.format(ctx.guild.name, ctx.author, ctx.message.content))
            missing_perms = []
            if not ctx.me.guild_permissions.send_messages:
                missing_perms.append('Send Messages')
            if not ctx.me.guild_permissions.manage_messages:
                missing_perms.append('Manage Messages')
            if not ctx.me.guild_permissions.embed_links:
                missing_perms.append('Embed Links')
            if not ctx.me.guild_permissions.attach_files:
                missing_perms.append('Attach Files')
            if not ctx.me.guild_permissions.read_message_history:
                missing_perms.append('Read Message History')
            if not ctx.me.guild_permissions.add_reactions:
                missing_perms.append('Add Reactions')
            if len(missing_perms) > 0:
                embed = discord.Embed(title='Warning',
                                      description='**Missing bot permissions to function properly:** `{}`'
                                      .format(', '.join(missing_perms)),
                                      color=0xff0000)
                await ctx.channel.send(embed=embed)
                logger.info('Missing Permissions Warning')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info('Joined server {}'.format(guild.name))
        insert_prefix(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.info('Left server {}'.format(guild.name))
        delete_prefix(guild)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        title = 'An error occurred.'
        if isinstance(error, commands.CommandNotFound):
            title = 'Command not found.'
        elif isinstance(error, commands.CommandOnCooldown):
            title = 'Command on cooldown for `{:.2f}s`.'.format(error.retry_after)
        elif isinstance(error, commands.TooManyArguments):
            title = 'Too many arguments.'
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.MissingRequiredArgument):
            title = 'Missing required argument.'
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.BadArgument):
            title = 'Wrong arguments.'
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.MissingPermissions):
            title = 'Missing permissions.'
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.BotMissingPermissions):
            title = 'Bot missing permissions.'
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.NoPrivateMessage):
            title = 'Command cannot be used in private messages.'
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.NotOwner):
            title = 'You are not the owner of the bot.'
            ctx.command.reset_cooldown(ctx)
        else:
            logger.exception(error)
        embed = discord.Embed(title=title, color=0xff0000)
        await ctx.channel.send(embed=embed)
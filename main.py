import typing

import discord
from discord.ext import commands

from consts import BOT_API, WEIRD_GUYS_GUILD_ID, IGNORED_MEMBERS, NO_PING, COMMAND_PREFIX
from graphics import CustomHelpCommand
from player import Player
from team import TeamGroup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=CustomHelpCommand())

teams = TeamGroup()


@bot.check
async def predicate(ctx: commands.Context):
	return ctx.channel.name in ("weird-bots",)  # TODO: Add "weird-balls" when it is time


@bot.event
async def on_ready():
	print(f'Logged in as {bot.user}')

	weird_guys_guild = bot.get_guild(WEIRD_GUYS_GUILD_ID)

	# Init members as players
	for member in weird_guys_guild.members:
		if not member.bot and member.name not in IGNORED_MEMBERS:
			teams.add_player(Player(member))


@bot.command()
async def ping(ctx: commands.Context):
	message = f"This message is in channel: {ctx.channel}\n"
	message += f"The author is owner: {await bot.is_owner(ctx.author)}\n"
	message += f"The author is on team: {teams.get_player(ctx.author).stats.team_id}"
	await ctx.send(message)


@bot.command(help="Collects a snowball")
async def collect(ctx: commands.Context):
	await teams.collect_for(ctx, ctx.author)


@bot.command(
	help="Throws snowball at target",
	usage="""Usage:
  !throw <member>"""
)
async def throw(ctx: commands.Context, *, member: typing.Union[discord.Member, str]):
	if isinstance(member, discord.Member):
		await teams.throw_for(ctx, ctx.author, member)
	else:
		await ctx.send(f"Could not find user {member}")


@bot.command(help="Prints top 3 player stats")
async def leader(ctx: commands.Context):
	sorted_players = teams.get_sorted_players()

	embed = discord.Embed(
		title="Leaderboard",
		color=discord.Color.blurple()
	)

	for index, player in enumerate(sorted_players[:3]):
		player_field_title = "" if index == 0 else r"**\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_**"
		player_field_title += f"\n{index + 1}: **{player.member.nick}**"

		embed.add_field(
			name=player_field_title,
			value="", inline=False
		)

		player.embed_stats(embed, include_xp_stats=False)

	await ctx.send(embed=embed, allowed_mentions=NO_PING)


@bot.command(
	help="Gives the stats of player",
	usage="""Usage:
  !stats          -> Your stats
  !stats <member> -> Stats of specified member"""
)
async def stats(ctx: commands.Context, member: typing.Optional[typing.Union[discord.Member, str]]):
	if isinstance(member, discord.Member) or member is None:
		if member is None:
			member = ctx.author

		if not teams.check_is_player(member):
			await ctx.send(f"Unable to process {member}")
			return

		embed = discord.Embed(
			title=f"{member.nick}'s stats:\n",
			color=discord.Color.blurple()
		)

		teams.get_player(member).embed_stats(embed)

		await ctx.send(embed=embed, allowed_mentions=NO_PING)
	else:
		await ctx.send(f"Could not find user {member}", ephemeral=True)


bot.run(BOT_API)

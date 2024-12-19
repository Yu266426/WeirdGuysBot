import typing

import discord
from discord.ext import commands

from consts import BOT_API, WEIRD_GUYS_GUILD_ID, IGNORED_MEMBERS, NO_PING, COMMAND_PREFIX, STATS_COLOUR, SIGN_UP_COMMAND_NAME
from graphics import CustomHelpCommand, TeamSignUpView
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
	weird_guys_guild = bot.get_guild(WEIRD_GUYS_GUILD_ID)

	# Init members as players
	for member in weird_guys_guild.members:
		if not member.bot and member.name not in IGNORED_MEMBERS:
			teams.add_player(Player(member))

	bot.add_view(TeamSignUpView(teams))

	print(f'Logged in as {bot.user}')


@bot.command()
async def ping(ctx: commands.Context):
	message = f"This message is in channel: {ctx.channel}\n"
	message += f"The author is owner: {await bot.is_owner(ctx.author)}\n"
	message += f"The author is on team: {teams.get_player(ctx.author).stats.team_id}"
	await ctx.send(message)


@bot.command(name=SIGN_UP_COMMAND_NAME)
@commands.is_owner()
async def sign_up(ctx: commands.Context):
	await ctx.send("Press the button to sign up as active member: ", view=TeamSignUpView(teams))


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
		color=STATS_COLOUR
	)

	for index, player in enumerate(sorted_players[:3]):
		player_field_title = "" if index == 0 else r"**\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_**"
		player_field_title += f"\n{index + 1}: **{player.member.nick}**"

		embed.add_field(
			name=player_field_title,
			value="", inline=False
		)

		player.embed_stats(ctx, embed, include_xp_stats=False)

	await ctx.send(embed=embed, allowed_mentions=NO_PING)


@bot.command(
	help="Gives the stats of player",
	usage="""Usage:
  !stats           -> Your stats
  !stats <member>  -> Stats of specified member
  !stats <team_id> -> Stats of specified team"""
)
async def stats(ctx: commands.Context, target: typing.Optional[typing.Union[discord.Member, str]]):
	if isinstance(target, discord.Member) or target is None:
		if target is None:
			target = ctx.author

		if not teams.check_is_player(target):
			await ctx.send(f"Unable to process {target}")
			return

		embed = discord.Embed(
			title=f"{target.nick}'s stats:\n",
			color=STATS_COLOUR
		)

		teams.get_player(target).embed_stats(ctx, embed)

		await ctx.send(embed=embed, allowed_mentions=NO_PING)
	else:
		if target.isnumeric() and teams.is_team(int(target)):
			embed = discord.Embed(
				title=f"Team `{target}`",
				color=STATS_COLOUR
			)

			teams.get_team(int(target)).embed_stats(embed)

			await ctx.send(embed=embed, allowed_mentions=NO_PING)

		else:
			await ctx.send(f"Could not find user {target}", ephemeral=True)


bot.run(BOT_API)

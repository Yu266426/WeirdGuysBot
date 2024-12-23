import random
import typing

import discord
from discord.ext import commands

from consts import BOT_API, WEIRD_GUYS_GUILD_ID, IGNORED_MEMBERS, NO_PING, COMMAND_PREFIX, STATS_COLOR, SIGN_UP_COMMAND_NAME, DISTRIBUTE_MEMBERS_COMMAND_NAME, COLLECT_COMMAND_NAME, THROW_COMMAND_NAME, LEADERBOARD_COMMAND_NAME, STATS_COMMAND_NAME, TEAMS_COLOR, GAME_OVER_COLOR
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


@bot.command(name=DISTRIBUTE_MEMBERS_COMMAND_NAME)
@commands.is_owner()
async def distribute_members(ctx: commands.Context):
	# Add active members
	active_players = teams.get_active_players()
	num_active_members = len(active_players)

	num_team_1 = num_active_members // 2

	# Randomly distribute odd member if needed
	if num_active_members % 2 != 0:
		if random.random() > 0.5:
			num_team_1 += 1

	team_1_active_players: list[Player] = random.sample(active_players, num_team_1)
	for player in team_1_active_players:
		teams.remove_player(player)
		player.stats.set_team(1)
		teams.add_player(player)

		active_players.remove(player)

	for player in active_players:
		teams.remove_player(player)
		player.stats.set_team(2)
		teams.add_player(player)

	# Add remaining members
	non_active_players = teams.get_non_active_players()
	num_non_active_members = len(non_active_players)

	num_team_1 = num_non_active_members // 2

	# Randomly distribute odd member if needed
	if num_non_active_members % 2 != 0:
		if random.random() > 0.5:
			num_team_1 += 1

	team_1_non_active_players: list[Player] = random.sample(non_active_players, num_team_1)

	for player in team_1_non_active_players:
		teams.remove_player(player)
		player.stats.set_team(1)
		teams.add_player(player)

		non_active_players.remove(player)

	for player in non_active_players:
		teams.remove_player(player)
		player.stats.set_team(2)
		teams.add_player(player)

	team_1_message = ""
	for player in sorted(teams.get_players_on_team(1), key=lambda e: e.stats.active, reverse=True):
		if player.stats.active:
			team_1_message += "* "

		team_1_message += f"{player.member.mention}\n"

	team_1_embed = discord.Embed(
		title="Players on team `1`",
		description=team_1_message,
		color=TEAMS_COLOR
	)

	team_2_message = ""
	for player in sorted(teams.get_players_on_team(2), key=lambda e: e.stats.active, reverse=True):
		if player.stats.active:
			team_2_message += "* "

		team_2_message += f"{player.member.mention}\n"

	team_2_embed = discord.Embed(
		title="Players on team `2`",
		description=team_2_message,
		color=TEAMS_COLOR
	)

	await ctx.send(embed=team_1_embed, allowed_mentions=NO_PING)
	await ctx.send(embed=team_2_embed, allowed_mentions=NO_PING)


@bot.command(name=COLLECT_COMMAND_NAME, help="Collects a snowball")
async def collect(ctx: commands.Context):
	await teams.collect_for(ctx, ctx.author)


@bot.command(
	name=THROW_COMMAND_NAME,
	help="Throws snowball at target",
	usage="""Usage:
  !throw <member>"""
)
async def throw(ctx: commands.Context, *, member: typing.Union[discord.Member, str]):
	if isinstance(member, discord.Member):
		check_game_over = await teams.throw_for(ctx, ctx.author, member)

		author = teams.get_player(ctx.author)
		if not author.team.base_team and check_game_over:
			winning_team_players = teams.get_players_on_team(author.team.id)

			message = f"Team `{author.team.id}` won!\n\n"
			message += f"Congratulations to:\n"

			for player in winning_team_players:
				message += f"{player.member.mention}\n"

			message += "\n"
			message += r"\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\~_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"
			message += f"\nMoving everyone to team `0` so the fun can continue!"

			embed = discord.Embed(
				title="GAME OVER!!!!!!",
				description=message,
				colour=GAME_OVER_COLOR
			)

			players = list(teams.players.values())
			for player in players:
				teams.remove_player(player)

			for player in players:
				player.stats.set_team(0)
				teams.add_player(player)

			await ctx.send(embed=embed, allowed_mentions=NO_PING)
	else:
		await ctx.send(f"Could not find user {member}")


@bot.command(name=LEADERBOARD_COMMAND_NAME, help="Prints top 3 player stats")
async def leader(ctx: commands.Context):
	sorted_players = teams.get_sorted_players()

	embed = discord.Embed(
		title="Leaderboard",
		color=STATS_COLOR
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
	name=STATS_COMMAND_NAME,
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
			color=STATS_COLOR
		)

		teams.get_player(target).embed_stats(ctx, embed)

		await ctx.send(embed=embed, allowed_mentions=NO_PING)
	else:
		if target.isnumeric() and teams.is_team(int(target)):
			embed = discord.Embed(
				title=f"Team `{target}`",
				color=STATS_COLOR
			)

			teams.get_team(int(target)).embed_stats(embed)

			await ctx.send(embed=embed, allowed_mentions=NO_PING)

		else:
			await ctx.send(f"Could not find target {target}", ephemeral=True)


bot.run(BOT_API)

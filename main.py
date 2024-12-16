import typing

import discord
from discord.ext import commands

from consts import BOT_API, WEIRD_GUYS_GUILD_ID, IGNORED_MEMBERS, NO_PING
from player import Player

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

players: dict[discord.Member, Player] = {}


@bot.event
async def on_ready():
	print(f'Logged in as {bot.user}')

	weird_guys_guild = bot.get_guild(WEIRD_GUYS_GUILD_ID)

	# Init members as players
	for member in weird_guys_guild.members:
		if not member.bot and member.name not in IGNORED_MEMBERS:
			players[member] = Player(member)


@bot.command()
async def collect(ctx: commands.Context):
	await players[ctx.author].collect(ctx)


@bot.command()
async def throw(ctx: commands.Context, *, member: typing.Union[discord.Member, str]):
	if isinstance(member, discord.Member):
		if member == ctx.author:
			await ctx.send("Why are you hitting yourself?")
			return

		if member not in players:
			await ctx.send(f"User {member} is not a player")
			return

		await players[ctx.author].throw(ctx, players[member])
	else:
		await ctx.send(f"Could not find user {member}")


@bot.command()
async def leader(ctx: commands.Context):
	sorted_players = sorted(players.values(), key=lambda e: e.stats.num_hits, reverse=True)

	embed = discord.Embed(
		title="Leaderboard",
		color=discord.Color.blurple()
	)

	for index, player in enumerate(sorted_players[:3]):
		embed.add_field(name=f"{index + 1}: {player.member.nick}", value="", inline=False)
		player.embed_stats(embed)

	await ctx.send(embed=embed, allowed_mentions=NO_PING)


@bot.command()
async def stats(ctx: commands.Context, member: typing.Optional[typing.Union[discord.Member, str]]):
	if isinstance(member, discord.Member) or member is None:
		if member is None:
			member = ctx.author

		if member not in players:
			await ctx.send(f"Unable to process {member}")
			return

		embed = discord.Embed(
			title=f"{member.nick}'s stats:",
			color=discord.Color.blurple()
		)

		players[member].embed_stats(embed)

		await ctx.send(embed=embed, allowed_mentions=NO_PING)
	else:
		await ctx.send(f"Could not find user {member}", ephemeral=True)


bot.run(BOT_API)

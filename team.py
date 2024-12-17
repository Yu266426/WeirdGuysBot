import discord
from discord.ext import commands

from player import Player


class TeamGroup:
	def __init__(self):
		self.players: dict[discord.Member, Player] = {}

		self.teams: dict[int, "Team"] = {0: Team(allow_friendly_fire=True)}  # 0 is default team

	def get_player(self, member: discord.Member) -> Player:
		return self.players[member]

	def add_player(self, player: Player):
		if player.member not in self.players:
			self.players[player.member] = player

		self.teams.setdefault(player.stats.team_id, Team()).add_player(player)

	def remove_player(self, player: Player):
		self.teams[player.stats.team_id].remove_player(player)

	def check_is_player(self, member: discord.Member) -> bool:
		return member in self.players

	def get_sorted_players(self) -> list[Player]:
		return sorted(self.players.values(), key=lambda e: e.stats.num_hits, reverse=True)

	def get_team_of(self, member: discord.Member) -> "Team":
		return self.teams[self.get_player(member).stats.team_id]

	async def collect_for(self, ctx: commands.Context, member: discord.Member):
		await self.get_player(member).collect(ctx)

	async def throw_for(self, ctx: commands.Context, member: discord.Member, target: discord.Member):
		if target == member:
			await ctx.reply("Why are you hitting yourself?")
			return

		if not self.check_is_player(target):
			await ctx.reply(f"User {target} is not a player")
			return

		player = self.get_player(member)
		target_player = self.get_player(target)

		# Check for friendly fire
		if player.stats.team_id == target_player.stats.team_id:
			if not self.get_team_of(member).allow_friendly_fire:
				await ctx.reply(f"You're on the same team!\nThis team does not allow for friendly fire")
				return

		await player.throw(ctx, target_player)


class Team:
	def __init__(self, allow_friendly_fire: bool = False):
		self.allow_friendly_fire = allow_friendly_fire

		self.players: set[Player] = set()

	def add_player(self, player: Player):
		self.players.add(player)

	def remove_player(self, player: Player):
		self.players.remove(player)

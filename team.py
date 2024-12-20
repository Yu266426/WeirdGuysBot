import discord
from discord.ext import commands

from graphics import xp_bar
from player import Player


class TeamGroup:
	def __init__(self):
		self.players: dict[discord.Member, Player] = {}

		self.teams: dict[int, "Team"] = {0: Team(allow_friendly_fire=True)}  # 0 is default team

	def add_player(self, player: Player):
		if player.member not in self.players:
			self.players[player.member] = player

		self.teams.setdefault(player.stats.team_id, Team()).add_player(player)

	def remove_player(self, player: Player):
		self.teams[player.stats.team_id].remove_player(player)

	def mark_member_active(self, member: discord.Member):
		self.players[member].stats.set_active()

	def get_player(self, member: discord.Member) -> Player:
		return self.players[member]

	def get_active_players(self) -> list[Player]:
		players = []
		for player in self.players.values():
			if player.stats.active:
				players.append(player)
		return players

	def get_non_active_players(self) -> list[Player]:
		players = []
		for player in self.players.values():
			if not player.stats.active:
				players.append(player)
		return players

	def get_players_on_team(self, team_id: int) -> list[Player]:
		if team_id not in self.teams:
			return []

		return list(self.teams[team_id].players)

	def check_is_player(self, member: discord.Member) -> bool:
		return member in self.players

	def get_sorted_players(self) -> list[Player]:
		return sorted(self.players.values(), key=lambda e: e.stats.num_hits, reverse=True)

	def is_team(self, team_id: int) -> bool:
		return team_id in self.teams

	def get_team(self, team_id: int) -> "Team":
		return self.teams[team_id]

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


class TeamStage:
	def __init__(
			self,
			hits_to_progress: int,
			xp_bonus: int,
			crit_bonus_percentage: int,
			cooldown_reduction_percent: int
	):
		self.hits_to_progress = hits_to_progress

		self.xp_bonus = xp_bonus
		self.crit_bonus_percentage = crit_bonus_percentage
		self.cooldown_reduction_percent = cooldown_reduction_percent


class Team:
	def __init__(self, allow_friendly_fire: bool = False):
		self._current_stage_index = 0
		self.previous_hits_to_progress = 0
		self._stages = (
			TeamStage(10, 1, 20, 50),
			TeamStage(10, 2, 40, 70),
		)

		self.allow_friendly_fire = allow_friendly_fire

		self.players: set[Player] = set()

		self.total_been_hits = 0
		self.crit_hits = 0
		self.crit_hits_progress_effect = 0.5

	@property
	def current_stage(self) -> TeamStage:
		if self._current_stage_index >= len(self._stages):
			return self._stages[-1]

		return self._stages[self._current_stage_index]

	def embed_stats(self, embed: discord.Embed):
		stats_message = f"Num players: `{len(self.players)}`\n"
		stats_message += f"Total hits: `{self.total_been_hits}`"

		current_stage = self.current_stage
		bonus_message = f"XP Bonus: `{current_stage.xp_bonus}`\n"
		bonus_message += f"Crit % 🔺: `{current_stage.crit_bonus_percentage}`\n"
		bonus_message += f"Cooldown % 🔻: `{current_stage.cooldown_reduction_percent}`"

		stage_progress_message = f"Stage: `{self._current_stage_index + 1}`/`{len(self._stages)}`\n"
		if self._current_stage_index < len(self._stages):
			stage_progress_message += "Progress: " + xp_bar(
				(self.total_been_hits + int(self.crit_hits * self.crit_hits_progress_effect)) - self.previous_hits_to_progress,
				current_stage.hits_to_progress
			)

		embed.add_field(name="Team Stats:", value=stats_message)
		embed.add_field(name="Team Bonuses:", value=bonus_message)
		embed.add_field(name="Snowman:", value=stage_progress_message, inline=False)

	def _calculate_stage_index(self):
		stage_index = 0
		total_been_hits = self.total_been_hits + int(self.crit_hits * self.crit_hits_progress_effect)

		hits_to_progress = 0

		for stage in self._stages:
			total_been_hits -= stage.hits_to_progress
			hits_to_progress += stage.hits_to_progress

			if total_been_hits <= 0:
				break

			stage_index += 1

		self._current_stage_index = stage_index
		self._previous_hits_to_progress = hits_to_progress

	def add_player(self, player: Player):
		player.team = self
		self.players.add(player)

		self.total_been_hits += player.stats.num_been_hit

		self._calculate_stage_index()

	def remove_player(self, player: Player):
		player.team = None
		self.players.remove(player)

		self.total_been_hits -= player.stats.num_been_hit

		self._calculate_stage_index()

	def player_on_team_hit(self, critical: bool):
		self.total_been_hits += 1
		self.crit_hits += critical

		if self._current_stage_index >= len(self._stages):
			return

		if (self.total_been_hits + int(self.crit_hits * self.crit_hits_progress_effect)) - self.previous_hits_to_progress > self.current_stage.hits_to_progress:
			self._current_stage_index += 1
			self.previous_hits_to_progress += self.current_stage.hits_to_progress

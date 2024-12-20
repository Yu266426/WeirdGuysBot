import random
import time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from consts import NO_PING, CRITICAL_HIT_COLOR, HIT_COLOR, MISS_COLOR, COLLECT_COLOR
from graphics import xp_bar
from player_stats import PlayerStats

if TYPE_CHECKING:
	from team import Team


class Player:
	def __init__(self, member: discord.Member):
		self.member = member
		self.stats = PlayerStats(member)

		self.last_collect_time: int | None = None

		# Will crash if None, which I think is going to be the intended behaviour, as a
		# player should always be on a team
		self.team: Team | None = None  # Set when added to a team

	def embed_stats(self, ctx: commands.Context, embed: discord.Embed, include_xp_stats: bool = True):
		throw_stats = f"Thrown: `{self.stats.num_thrown}`\n"
		throw_stats += f"Hits: `{self.stats.num_hits}`\n"
		throw_stats += f"Misses: `{self.stats.num_thrown - self.stats.num_hits}`\n"
		throw_stats += f"Hit %: `{(round((self.stats.num_hits / self.stats.num_thrown) * 100, 1)) if self.stats.num_thrown != 0 else "N/A"}`"

		hit_by_most = self.stats.get_hit_by_most()
		has_hit_most = self.stats.get_has_hit_most()

		if hit_by_most[1] != 0:
			throw_stats += f"\nHit by {ctx.bot.get_user(hit_by_most[0]).mention} `{hit_by_most[1]}` times"

		if has_hit_most[1] != 0:
			throw_stats += f"\nHas hit {ctx.bot.get_user(has_hit_most[0]).mention} `{has_hit_most[1]}` times"

		snowball_stats = f"Count: `{self.stats.num_snowballs}`\n"
		snowball_stats += f"Capacity: `{self.stats.max_snowballs}`\n"
		snowball_stats += f"Cooldown: `{self.stats.collect_cooldown}` secs\n"

		general_stats = f"Team: `{self.stats.team_id}`\n"
		general_stats += f"Accuracy %: `{self.stats.accuracy}`\n"
		general_stats += f"Crit %: `{self.stats.crit_chance}`\n"
		general_stats += f"Times hit: `{self.stats.num_been_hit}`"

		embed.add_field(name="Throws:", value=throw_stats, inline=True)
		embed.add_field(name="Snowballs:", value=snowball_stats, inline=True)
		embed.add_field(name="Stats:", value=general_stats, inline=True)

		if include_xp_stats:
			xp_stats = f"Level: `{self.stats.level}/{self.stats.TOTAL_LEVELS}`\n"

			if self.stats.level < self.stats.TOTAL_LEVELS:
				xp_stats += f"XP: " + xp_bar(self.stats.xp, self.stats.xp_to_next_level)
				xp_stats += f" (`{self.stats.xp}/{self.stats.xp_to_next_level}`)"

			embed.add_field(name="Level", value=xp_stats, inline=False)

	async def collect(self, ctx: commands.Context):
		if self.last_collect_time is None or self.stats.can_collect(self.last_collect_time, self.team.current_stage.cooldown_reduction_percent):
			if self.stats.add_snowball():
				self.last_collect_time = time.time()

				embed = discord.Embed(
					title=f"{self.member.name} collected a snowball",
					description=f"{self.member.mention} are up to `{self.stats.num_snowballs}` balls",
					color=COLLECT_COLOR
				)

				await ctx.reply(embed=embed, allowed_mentions=NO_PING)
			else:
				await ctx.reply(f"{self.member.mention} is full", allowed_mentions=NO_PING)
		else:
			await ctx.reply(
				f"Cooldown has `{self.stats.get_collect_cooldown(
					self.last_collect_time,
					self.team.current_stage.cooldown_reduction_percent
				)}` seconds remaining",
				ephemeral=True,
				delete_after=3
			)
			await ctx.message.delete(delay=3)

	async def throw(self, ctx: commands.Context, target: "Player"):
		if self.stats.num_snowballs == 0:
			await ctx.reply(f"{self.member.mention} doesn't have any balls!", delete_after=3)
			await ctx.message.delete(delay=3)
			return

		is_hit, is_crit = self.stats.throw(target, self.team.current_stage.crit_bonus_percentage)

		balls_remaining_message = f"You have `{self.stats.num_snowballs}` balls remaining"

		if is_hit:
			target.stats.hit(is_crit, self)
			target.team.player_on_team_hit(is_crit)

			leveled_up = self.stats.add_xp(1 + self.team.current_stage.xp_bonus)

			message = ""
			if is_crit:
				message += "Critical Hit!\n"
			message += f"{self.member.mention} hit {target.member.mention}"
			if is_crit:
				message += " and made them lose their balls!"
			message += "!\n" + balls_remaining_message

			embed = discord.Embed(
				title=f"{random.choice(("Splat", "Plop", "Thwack", "Smack", "Fwhap"))}!!",
				description=message,
				color=CRITICAL_HIT_COLOR if is_crit else HIT_COLOR
			)

			await ctx.reply(
				embed=embed,
				allowed_mentions=NO_PING,
			)

			if leveled_up:
				await ctx.send(f"{self.member.mention} has leveled up!", allowed_mentions=NO_PING)

		else:
			embed = discord.Embed(
				title=f"{random.choice(("Whoosh", "Whiff", "Pfft"))}—",
				description=f"{self.member.mention} missed!\n" + balls_remaining_message,
				color=MISS_COLOR
			)

			await ctx.reply(embed=embed, allowed_mentions=NO_PING)

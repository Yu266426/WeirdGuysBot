import asyncio
import json
import random

import math
import time

import discord
from discord.ext import commands

from consts import DATA_DIR, NO_PING


class PlayerStats:
	def __init__(self, member: discord.Member):
		self._member = member

		self._snowball_count = 0

		self._max_snowballs = 3
		self._collect_cooldown_secs = 5
		self._accuracy_percentage = 70
		self._lose_snowballs_percentage = 90

		self._num_thrown = 0
		self._num_hits = 0
		self._num_been_hit = 0

		self.load()

	@staticmethod
	def _default_data() -> dict:
		return {
			"snowball_count": 0,
			"max_snowballs": 3,
			"collect_cooldown": 5,
			"accuracy": 70,
			"num_thrown": 0,
			"num_hits": 0,
			"num_been_hit": 0
		}

	def save(self):
		file_path = DATA_DIR / f"{self._member.id}.json"

		# Create new file if needed
		if not file_path.is_file():
			with open(file_path, "x") as file:
				file.write(json.dumps(self._default_data()))
			return

		# Save data
		with open(file_path, "r") as file:
			data = json.load(file)

		data["snowball_count"] = self._snowball_count
		data["max_snowballs"] = self._max_snowballs
		data["collect_cooldown"] = self._collect_cooldown_secs
		data["accuracy"] = self._accuracy_percentage
		data["num_thrown"] = self._num_thrown
		data["num_hits"] = self._num_hits
		data["num_been_hit"] = self._num_been_hit

		with open(file_path, "w") as file:
			file.write(json.dumps(data))

	def load(self):
		file_path = DATA_DIR / f"{self._member.id}.json"

		# Create new file if needed
		if not file_path.is_file():
			with open(file_path, "x") as file:
				file.write(json.dumps(self._default_data()))
			return

		with open(file_path, "r") as file:
			data = json.load(file)

		self._snowball_count = data["snowball_count"]
		self._max_snowballs = data["max_snowballs"]
		self._collect_cooldown_secs = data["collect_cooldown"]
		self._accuracy_percentage = data["accuracy"]

		self._num_thrown = data["num_thrown"]
		self._num_hits = data["num_hits"]
		self._num_been_hit = data["num_been_hit"]

	@property
	def num_snowballs(self) -> int:
		return self._snowball_count

	@property
	def max_snowballs(self) -> int:
		return self._max_snowballs

	@property
	def collect_cooldown(self) -> int:
		return self._collect_cooldown_secs

	@property
	def accuracy(self) -> int:
		return self._accuracy_percentage

	@property
	def lose_snowballs_percentage(self) -> int:
		return self._lose_snowballs_percentage

	@property
	def num_thrown(self) -> int:
		return self._num_thrown

	@property
	def num_hits(self) -> int:
		return self._num_hits

	@property
	def num_been_hit(self) -> int:
		return self._num_been_hit

	def can_collect(self, last_collect_time: float) -> bool:
		return time.time() - last_collect_time > self._collect_cooldown_secs

	def get_collect_cooldown(self, last_collect_time: float) -> int:
		return math.ceil(
			self._collect_cooldown_secs -
			(time.time() - last_collect_time)
		)

	def check_will_hit(self) -> bool:
		return random.random() < self._accuracy_percentage / 100

	def hit(self) -> bool:
		self._num_been_hit += 1

		if random.random() < self._lose_snowballs_percentage / 100:
			self._snowball_count = 0
			self.save()
			return True

		return False

	def throw(self):
		self._snowball_count -= 1
		self._num_thrown += 1
		self.save()

	def mark_successful_throw(self):
		self._num_hits += 1
		self.save()

	def add_snowball(self) -> bool:
		if self._snowball_count < self._max_snowballs:
			self._snowball_count += 1
			self.save()
			return True

		return False

	def remove_snowball(self):
		self._snowball_count -= 1
		self.save()


class Player:
	def __init__(self, member: discord.Member):
		self.member = member
		self.stats = PlayerStats(member)

		self.last_collect_time: int | None = None

	def embed_stats(self, embed: discord.Embed):
		throw_stats = f"Thrown: `{self.stats.num_thrown}`\n"
		throw_stats += f"Hits: `{self.stats.num_hits}`\n"
		throw_stats += f"Misses: `{self.stats.num_thrown - self.stats.num_hits}`\n"
		throw_stats += f"Hit %: `{(round((self.stats.num_hits / self.stats.num_thrown) * 100, 1)) if self.stats.num_thrown != 0 else "N/A"}`"

		snowball_stats = f"Count: `{self.stats.num_snowballs}`\n"
		snowball_stats += f"Capacity: `{self.stats.max_snowballs}`\n"
		snowball_stats += f"Cooldown: `{self.stats.collect_cooldown}` secs\n"

		general_stats = f"Accuracy %: `{self.stats.accuracy}`\n"
		general_stats += f"Chance to lose balls %: `{self.stats.lose_snowballs_percentage}`\n"
		general_stats += f"Times hit: `{self.stats.num_been_hit}`"

		embed.add_field(name="Throws:", value=throw_stats, inline=True)
		embed.add_field(name="Snowballs:", value=snowball_stats, inline=True)
		embed.add_field(name="Stats:", value=general_stats, inline=True)

	async def collect(self, ctx: commands.Context):
		if self.last_collect_time is None or self.stats.can_collect(self.last_collect_time):
			if self.stats.add_snowball():
				self.last_collect_time = time.time()

				embed = discord.Embed(
					title=f"{self.member.name} collected a snowball",
					description=f"{self.member.mention} are up to `{self.stats.num_snowballs}` balls",
					color=discord.Color.teal()
				)

				await ctx.reply(embed=embed, allowed_mentions=NO_PING)
			else:
				await ctx.reply(f"{self.member.mention} is full", allowed_mentions=NO_PING)
		else:
			await ctx.reply(f"Cooldown has `{self.stats.get_collect_cooldown(self.last_collect_time)}` seconds remaining", ephemeral=True, delete_after=3)
			await ctx.message.delete(delay=3)

	async def throw(self, ctx: commands.Context, target: "Player"):
		if self.stats.num_snowballs == 0:
			await ctx.reply("You don't have any balls!", delete_after=3)
			await ctx.message.delete(delay=3)
			return

		self.stats.throw()

		balls_remaining_message = f"You have `{self.stats.num_snowballs}` balls remaining"

		if self.stats.check_will_hit():
			lost_balls = target.stats.hit()
			self.stats.mark_successful_throw()

			message = f"{self.member.mention} hit {target.member.mention}"
			if lost_balls:
				message += " and made them lose their balls!"
			message += "!\n" + balls_remaining_message

			embed = discord.Embed(
				title=f"{random.choice(("Splat", "Plop", "Thwack", "Smack", "Fwhap"))}!!",
				description=message,
				color=discord.Color.blue()
			)

			await ctx.reply(
				embed=embed,
				allowed_mentions=NO_PING,
			)
		else:
			embed = discord.Embed(
				title=f"{random.choice(("Whoosh", "Whiff", "Pfft"))}—",
				description=f"{self.member.mention} missed!\n" + balls_remaining_message,
				color=discord.Color.dark_red()
			)

			await ctx.reply(embed=embed, allowed_mentions=NO_PING)

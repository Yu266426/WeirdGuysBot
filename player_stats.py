import json
import random
import time
from typing import TYPE_CHECKING

import discord
import math

from consts import DATA_DIR

if TYPE_CHECKING:
	from player import Player


class PlayerStats:
	TOTAL_LEVELS = 5
	_XP_TO_NEXT_LEVEL = (3, 4, 5, 6)
	_STATS_FOR_LEVEL = {
		1: {
			"max_snowballs": 3,
			"collect_cooldown": 5,
			"accuracy": 70,
			"crit": 60,
		},
		2: {
			"max_snowballs": 4,
			"collect_cooldown": 4,
			"accuracy": 75,
			"crit": 70,
		},
		3: {
			"max_snowballs": 5,
			"collect_cooldown": 3,
			"accuracy": 80,
			"crit": 80,
		},
		4: {
			"max_snowballs": 6,
			"collect_cooldown": 2,
			"accuracy": 85,
			"crit": 85,
		},
		5: {
			"max_snowballs": 7,
			"collect_cooldown": 1,
			"accuracy": 90,
			"crit": 90,
		},
	}

	def __init__(self, member: discord.Member):
		# Sanity checks
		if len(self._XP_TO_NEXT_LEVEL) != self.TOTAL_LEVELS - 1:
			raise ValueError("Incorrect number of levels for _XP_TO_NEXT_LEVEL")
		if len(self._STATS_FOR_LEVEL) != self.TOTAL_LEVELS:
			raise ValueError("Incorrect number of levels for _STATS_FOR_LEVEL")

		self._member = member
		self._team_id = 0
		self._active = False

		self._level = 1
		self._xp = 0

		self._snowball_count = 0

		self._max_snowballs = 3
		self._collect_cooldown_secs = 5
		self._accuracy_percentage = 70
		self._crit_percentage = 60

		self._num_thrown = 0
		self._num_hits = 0
		self._num_been_hit = 0

		self._hit_by: dict[int, int] = {}
		self._has_hit: dict[int, int] = {}

		self.load()

	@staticmethod
	def _default_data() -> dict:
		data = {
			"team_id": 0,
			"active": False,
			"level": 1,
			"xp": 0,
			"snowball_count": 0,
			"num_thrown": 0,
			"num_hits": 0,
			"num_been_hit": 0,
			"hit_by": {},
			"has_hit": {}
		}

		data.update(PlayerStats._STATS_FOR_LEVEL[1])

		return data

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

		data["team_id"] = self._team_id
		data["active"] = self._active

		data["level"] = self._level
		data["xp"] = self._xp

		data["snowball_count"] = self._snowball_count
		data["max_snowballs"] = self._max_snowballs
		data["collect_cooldown"] = self._collect_cooldown_secs
		data["accuracy"] = self._accuracy_percentage
		data["crit"] = self._crit_percentage

		data["num_thrown"] = self._num_thrown
		data["num_hits"] = self._num_hits
		data["num_been_hit"] = self._num_been_hit

		data["hit_by"] = self._hit_by
		data["has_hit"] = self._has_hit

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

		self._team_id = data["team_id"]
		self._active = data["active"]

		self._level = data["level"]
		self._xp = data["xp"]

		self._snowball_count = data["snowball_count"]
		self._max_snowballs = data["max_snowballs"]
		self._collect_cooldown_secs = data["collect_cooldown"]
		self._accuracy_percentage = data["accuracy"]
		self._crit_percentage = data["crit"]

		self._num_thrown = data["num_thrown"]
		self._num_hits = data["num_hits"]
		self._num_been_hit = data["num_been_hit"]

		self._hit_by = {int(key): value for key, value in data["hit_by"].items()}
		self._has_hit = {int(key): value for key, value in data["has_hit"].items()}

	def set_active(self, value: bool = True):
		self._active = value
		self.save()

	def set_team(self, team_id: int):
		self._team_id = team_id
		self.save()

	@property
	def team_id(self) -> int:
		return self._team_id

	@property
	def active(self) -> bool:
		return self._active

	@property
	def level(self) -> int:
		return self._level

	@property
	def xp(self) -> int:
		return self._xp

	@property
	def xp_to_next_level(self) -> int:
		return self._XP_TO_NEXT_LEVEL[self._level - 1]

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
	def crit_chance(self) -> int:
		return self._crit_percentage

	@property
	def num_thrown(self) -> int:
		return self._num_thrown

	@property
	def num_hits(self) -> int:
		return self._num_hits

	@property
	def num_been_hit(self) -> int:
		return self._num_been_hit

	def get_hit_by_most(self) -> tuple[int, int]:
		if len(self._hit_by) != 0:
			return max(self._hit_by.items(), key=lambda e: e[1])

		return 0, 0

	def get_has_hit_most(self) -> tuple[int, int]:
		if len(self._has_hit) != 0:
			return max(self._has_hit.items(), key=lambda e: e[1])

		return 0, 0

	def add_xp(self, amount: int) -> bool:
		if self._level >= self.TOTAL_LEVELS:
			return False

		self._xp += amount
		self.save()

		if self._xp >= self.xp_to_next_level:
			self._xp -= self.xp_to_next_level

			return self._level_up()

	def _level_up(self) -> bool:
		if self._level >= self.TOTAL_LEVELS:
			return False

		self._level += 1

		level_stats = self._STATS_FOR_LEVEL[self._level]
		self._max_snowballs = level_stats["max_snowballs"]
		self._collect_cooldown_secs = level_stats["collect_cooldown"]
		self._accuracy_percentage = level_stats["accuracy"]
		self._crit_percentage = level_stats["crit"]

		self.save()

		return True

	def can_collect(self, last_collect_time: float, cooldown_reduction_percent: int) -> bool:
		return time.time() - last_collect_time > self._collect_cooldown_secs * (1 - cooldown_reduction_percent / 100)

	def get_collect_cooldown(self, last_collect_time: float, cooldown_reduction_percent: int) -> int:
		return math.ceil(
			(self._collect_cooldown_secs * (1 - cooldown_reduction_percent / 100)) -
			(time.time() - last_collect_time)
		)

	def hit(self, is_crit: bool, player: "Player"):
		self._num_been_hit += 1

		if player.member.id not in self._hit_by:
			self._hit_by[player.member.id] = 0

		self._hit_by[player.member.id] += 1

		if is_crit:
			self._snowball_count = 0

		self.save()

	def throw(self, player: "Player", crit_bonus_percentage: int) -> tuple[bool, bool]:
		"""
		:return: Bool (is crit)
		"""

		self._snowball_count -= 1
		self._num_thrown += 1

		is_successful = random.random() < self._accuracy_percentage / 100
		is_critical = random.random() < (self._crit_percentage / 100) * (1 + crit_bonus_percentage / 100)

		if is_successful:
			self._num_hits += 1

			# Set has hit
			if player.member.id not in self._has_hit:
				self._has_hit[player.member.id] = 0

			self._has_hit[player.member.id] += 1

		self.save()

		return is_successful, is_critical

	def add_snowball(self) -> bool:
		if self._snowball_count < self._max_snowballs:
			self._snowball_count += 1
			self.save()
			return True

		return False

	def remove_snowball(self):
		self._snowball_count -= 1
		self.save()

from typing import Mapping, Optional, List, Any

import discord
from discord.ext import commands

from consts import COMMAND_PREFIX


class CustomHelpCommand(commands.HelpCommand):
	async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]], /) -> None:
		embed = discord.Embed(
			title="Commands",
			description="",
			color=discord.Color.greyple()
		)

		total_commands = [e for bot_commands in mapping.values() for e in bot_commands]

		for index, command in enumerate(total_commands):
			tail = ""
			if index < len(total_commands) - 1:
				tail += "\n"
				tail += r"\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"

			embed.add_field(
				name=f"{COMMAND_PREFIX}{command.name}",
				value=f"`{command.help}`" + tail,
				inline=False
			)

		await self.get_destination().send(embed=embed)

	async def send_command_help(self, command: commands.Command):
		embed = discord.Embed(
			title=f"Command: {command.name}",
			description=command.help or "No description provided.",
			color=discord.Color.greyple()
		)
		# Show arguments dynamically
		embed.add_field(
			name="Usage",
			value=f"```{command.usage}```" if command.usage is not None else f"```{COMMAND_PREFIX}{command.name}```",
			inline=False
		)
		await self.get_destination().send(embed=embed)


def xp_bar(current: int, total: int, length: int = 10) -> str:
	ratio = current / total
	swap_point = round(length * ratio)

	result = ""
	for i in range(length):
		if i < swap_point:
			result += "🟩"
		else:
			result += "🟨"

	return result

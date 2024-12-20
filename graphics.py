import logging
from typing import Mapping, Optional, List, Any, TYPE_CHECKING

import discord
from discord.ext import commands

from consts import COMMAND_PREFIX, SIGN_UP_COMMAND_NAME, DISTRIBUTE_MEMBERS_COMMAND_NAME, HELP_COLOR

if TYPE_CHECKING:
	from team import TeamGroup


class CustomHelpCommand(commands.HelpCommand):
	async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]], /) -> None:
		embed = discord.Embed(
			title="Commands",
			description="",
			color=discord.Color.greyple()
		)

		total_commands = [e for bot_commands in mapping.values() for e in bot_commands]

		for index, command in enumerate(total_commands):
			if command.name in (SIGN_UP_COMMAND_NAME, DISTRIBUTE_MEMBERS_COMMAND_NAME):
				continue

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
			color=HELP_COLOR
		)
		# Show arguments dynamically
		embed.add_field(
			name="Usage",
			value=f"```{command.usage}```" if command.usage is not None else f"```{COMMAND_PREFIX}{command.name}```",
			inline=False
		)
		await self.get_destination().send(embed=embed)


class TeamSignUpView(discord.ui.View):
	def __init__(self, team_group: "TeamGroup"):
		super().__init__(timeout=None)

		self.team_group = team_group

	@discord.ui.button(label="Sign Up", style=discord.ButtonStyle.primary, custom_id="sign_up_button")
	async def sign_up_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		response: discord.InteractionResponse = interaction.response  # Typing issue # NoQA

		if not self.team_group.get_player(interaction.user).stats.active:
			self.team_group.mark_member_active(interaction.user)
			print(f"{interaction.user.name} has signed up ({interaction.user.id})")

			await response.send_message("You have signed up", ephemeral=True)
		else:
			print(f"{interaction.user.name} tried to sign up again ({interaction.user.id})")
			await response.send_message("You have already signed up", ephemeral=True)


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

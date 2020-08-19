import discord
from discord.ext import commands, tasks

from itertools import cycle
import asyncio
from datetime import datetime

import scripts.get_agendas as ga

def sprint(msg):
    print(datetime.today(), '|', msg)
    

with open('/home/slime/channel17_bot_token.txt', 'r') as file:
    TOKEN = file.readline()


if not TOKEN:
    print("No Token")
    exit()

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print("Bot Connected.")

@tasks.loop(seconds=5.0)
async def check_new_agendas():
    sprint("Checking for new agendas")
    if ga.check_new():
        sprint("New agenda found.")
        fetch_agendas()

async def fetch_agendas():
    agenda = ga.get_agendas()[-1]
    embed = discord.Embed(
            title = 'Latest Agenda',
            )
    embed.add_field(name=agenda[0], value=agenda[1], inline=False)
    embed.add_field(name='Link:', value=agenda[2])

    sprint("Fetching latest Sandown agenda")
    await ctx.send('Fetching...')
    await ctx.send(embed=embed)

@bot.command(aliases=['ga', 'agenda', 'latest agenda'])
async def latest_agenda(ctx):
    fetch_agendas()


check_new_agendas.start()
bot.run(TOKEN)

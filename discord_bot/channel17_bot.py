import discord, asyncio
from discord.ext import commands, tasks
from datetime import datetime
import scripts.get_agendas as ga

home_dir = os.getenv('HOME')
with open(f'{home_dir}/channel17_bot.token', 'r') as file:
    TOKEN = file.readline()

def sprint(msg):
    print(f'{datetime.today()} | {msg}')

if not TOKEN:
    print("Token Error.")
    exit(1)

bot = commands.Bot(command_prefix='.')

# Channel to for check_new_agenda loop
update_channel = None
# Latest agenda Discord embed object
latest_agenda = None

@bot.event
async def on_ready():
    global update_channel
    sprint("Bot Connected.")
    await bot.wait_until_ready()
    update_channel = bot.get_channel(745699017811296319)
    check_new_agendas.start()


# Fetches latest agenda and puts in Discord embed
async def fetch_agendas(amount=8):
    global latest_agenda
    agenda = ga.get_agendas(amount)
    embed = discord.Embed(title = 'Latest Agenda')
    for i in range(amount):
        embed.add_field(
                name=agenda[i][0], 
                value=f'Date: {agenda[i][1]}\nLink: {agenda[i][2]}',
                inline=False
                )

    sprint("Fetching latest agendas")
    latest_agenda = embed

# Checks if new agenda has been added.
@tasks.loop(hours=12)
async def check_new_agendas():
    sprint("Checking for new agendas")
    if ga.check_new():
        sprint("New agenda found.")
        await fetch_agendas()
        await update_channel.send(embed=latest_agenda)

# Show latest agenda.
@bot.command(aliases=['ga', 'agenda', 'latest agenda'])
async def latest_agenda(ctx, amount=5):
    await ctx.send('Fetching...')
    await fetch_agendas(amount)
    await ctx.send(embed=latest_agenda)


bot.run(TOKEN)

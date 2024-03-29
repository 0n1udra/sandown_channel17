import os
import sys
import random
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime

import discord
from discord.ext import commands, tasks

__version__ = "3.0"
__date__ = '02/11/2023'
__license__ = "GPL 3"
__author__ = 'github.com/0n1udra'
__email__ = "dt01@pm.me"

token_file = f'{os.getenv("HOME")}/keys/channel17_bot.token'
bot_path = os.path.dirname(os.path.abspath(__file__))
agenda_file = bot_path + '/latest_agendas.txt'
main_channel_id = 745699017811296319
priv_channel_id = 953008727814987887

if os.path.isfile(token_file):
    with open(token_file, 'r') as file: TOKEN = file.readline()
else:
    print("Missing Token File:", token_file)
    sys.exit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', case_insensitive=True, intents=intents)

def lprint(msg): print(f'{datetime.today()} | {msg}')


# ========== Web Scraper
def scrape_agendas(total=5):
    meetings = []

    # Requests sandown.us/minutes-and-agenda with random user agent.
    user_agents = ["Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
                   "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
                   "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
    ]
    headers = {'User-Agent': random.choice(user_agents)}
    sandown_website = requests.get('http://www.sandown.us/minutes-and-agendas', headers=headers)
    sandown_url = 'http://www.sandown.us'
    soup = BeautifulSoup(sandown_website.text, 'html.parser')
    # Only gets links for schedules in Agendas column.
    div_agenda = soup.find_all('div', class_='minutes-agendas-second-column')
    if not div_agenda: return False

    for i in div_agenda[0].find_all('a'):
        current_url = f"{i.get('href')}/{datetime.today().year}"

        # Extracts name and date of meeting.
        data = BeautifulSoup(requests.get(current_url, headers=headers).text, "html.parser")
        file_dates = data.find_all('div', class_='field-content')
        file_names = data.find_all('h3')

        for name, date in zip(file_names, file_dates):
            for url in name.find_all('a'):
                # Get's just the url str from tag
                file_url = sandown_url + url.get('href')
                # Converts string to datetime object
                agenda_date = datetime.strptime(date.text, '%B %d, %Y - %I:%M%p')
            meetings.append([name.text, agenda_date, file_url])

    meetings.sort(key=lambda x: x[1])

    # Format datetime look
    for i in range(len(meetings)):
        meetings[i][1] = meetings[i][1].strftime('%a %m/%d %H:%M')
    return meetings[-total:]

async def check_if_new(amount=5, force=False, *_):
    """Checks if there's a difference in latest_agenda.txt and newly pulled data from scrape_agendas."""

    agenda_data = scrape_agendas(amount)
    if not agenda_data:
        lprint("Error scraping site.")
        await priv_channel.send("**Error:** Problem scraping website.")
        return False  # If no data was recieved from scrape_agendas()
    if force: return agenda_data  # Returns data without checking against agenda_file.

    # Create file if not exist.
    if not os.path.isfile(agenda_file):
        new_file = open(agenda_file, 'w')
        new_file.close()

    # Read contents of file
    with open(agenda_file, 'r') as file: read_data = file.readlines()

    # Compares data to see if fetched anything new.
    if str(agenda_data) not in read_data:
        with open(agenda_file, 'w') as file:
            file.write(str(agenda_data))
        #with open(log_filepath, 'a') as file: file.write(f'\n{datetime.today()}\n{str(agenda_data)}')
        return agenda_data
    else: return False

# ========== Discord Bot
main_channel = priv_channel = None

@bot.event
async def on_ready():
    global main_channel, priv_channel
    lprint("Bot Connected")
    await bot.wait_until_ready()
    main_channel = bot.get_channel(main_channel_id)
    priv_channel = bot.get_channel(priv_channel_id)
    await priv_channel.send(f':white_check_mark: v{__version__} **Bot PRIMED** {datetime.now().strftime("%X")}')
    await show_buttons(priv_channel)
    check_hourly.start()

class Discord_Button(discord.ui.Button):
    """
    Create button from received list containing label, custom_id, and emoji.
    Uses custom_id with ctx.invoke to call corresponding function.
    """

    def __init__(self, label, custom_id, emoji=None, style=discord.ButtonStyle.grey):
        super().__init__(label=label, custom_id=custom_id, emoji=emoji, style=style)

    async def callback(self, interaction):
        await interaction.response.defer()
        custom_id = interaction.data['custom_id']

        # Runs function of same name as button's .custom_id variable. e.g. _teleport_selected()
        ctx = await bot.get_context(interaction.message)  # Get ctx from message.
        await ctx.invoke(bot.get_command(custom_id))

def new_buttons(buttons_list):
    """Create new discord.ui.View and add buttons, then return said view."""

    view = discord.ui.View(timeout=None)
    for button in buttons_list:
        if len(button) == 2: button.append(None)  # For button with no emoji.
        view.add_item(Discord_Button(label=button[0], custom_id=button[1], emoji=button[2]))
    return view


async def show_buttons(ctx):
    buttons = [['Check for new', 'check_agendas', '\U0001F504'], ['Get current agendas', 'get_agendas', '\U00002B07']]
    await ctx.send('Check for new agendas or show latest ones. Can also use `.check`.', view=new_buttons(buttons))


@tasks.loop(hours=2)
async def check_hourly():
    lprint('Check Task')
    try:
        message = await main_channel.fetch_message(main_channel.last_message_id)
    except: return
    ctx = await bot.get_context(message)

    await ctx.invoke(bot.get_command('check_agendas'), from_check_hourly=True)

@bot.command(aliases=['fetch', 'check'])
async def check_agendas(ctx, amount=5, force=False, from_check_hourly=False):
    """Shows current agendas in embed if new ones found."""

    found_agendas = False
    if agenda := await check_if_new(amount, force):
        found_agendas = True
        await ctx.send('New Agendas Found.')
        embed = discord.Embed(title='Latest Agendas')
        for i in range(len(agenda)):
            embed.add_field(name=agenda[i][0], value=f'Date: {agenda[i][1]}\nLink: {agenda[i][2]}', inline=False)
        await ctx.send(embed=embed)
        lprint("New agendas found")
    else:
        if not from_check_hourly:
            await ctx.send('No new agendas found.')

    if not from_check_hourly or found_agendas:
        await show_buttons(ctx)

    lprint("Fetched agenda")

@bot.command(aliases=['get', 'agendas'])
async def get_agendas(ctx):
    """Shows agendas even if no new ones found."""

    await ctx.invoke(bot.get_command('check_agendas'), force=True)

@bot.command(aliases=['rbot', 'rebootbot', 'botrestart', 'botreboot'])
async def restartbot(ctx, now=''):
    """Restart this bot."""

    lprint("Restarting bot...")
    os.chdir('/')
    os.chdir(bot_path)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.command(aliases=['updatebot', 'botupdate', 'git', 'update'])
async def gitupdate(ctx):
    """Gets update from GitHub."""

    await ctx.send("***Updating from GitHub...*** :arrows_counterclockwise:")
    os.chdir(bot_path)
    os.system('git pull')
    await ctx.invoke(bot.get_command("restartbot"))

bot.run(TOKEN, reconnect=True)

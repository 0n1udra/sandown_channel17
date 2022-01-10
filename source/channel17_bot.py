import requests, discord, sys, os
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle,  Select, SelectOption, ComponentsBot
from bs4 import BeautifulSoup
from datetime import datetime

token_file = f'{os.getenv("HOME")}/keys/channel17_bot.token'

if os.path.isfile(token_file):
    with open(token_file, 'r') as file: TOKEN = file.readline()
else:
    print("Missing Token File:", token_file)
    sys.exit()

channel_id = 745699017811296319

bot = ComponentsBot(command_prefix='.')

def lprint(msg): print(f'{datetime.today()} | {msg}')

# ========== Web Scraper
agenda_file = os.path.dirname(os.path.abspath(__file__)) + '/latest_agendas.txt'

def get_agendas(total=5):
    meetings = []

    # Requests sandown.us/minutes-and-agenda.
    sandown_website = requests.get('https://www.sandown.us/minutes-and-agendas')
    sandown_url = 'https://www.sandown.us'
    soup = BeautifulSoup(sandown_website.text, 'html.parser')
    # Only gets links for schedules in Agendas column.
    div_agenda = soup.find_all('div', class_='minutes-agendas-second-column')
    for i in div_agenda[0].find_all('a'):
        current_url = f"{i.get('href')}/{datetime.today().year}"

        # Extracts name and date of meeting.
        data = BeautifulSoup(requests.get(current_url).text, "html.parser")
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

def check_if_new(*_):
    """Checks if there's a difference in latest_agenda.txt and newly pulled data from get_agendas."""

    agenda_data = get_agendas()

    read_data = ''
    with open(agenda_file, 'r') as file:
        read_data = file.readlines()

    if str(agenda_data) not in read_data:
        with open(agenda_file, 'w') as file:
            file.write(str(agenda_data))
            return agenda_data
    else: return False

# ========== Discord Bot
channel = None

@bot.event
async def on_ready():
    global channel
    lprint("Bot Connected.")
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    await channel.send('**Bot PRIMED** :white_check_mark:')
    check_hourly.start()

@bot.event
async def on_button_click(interaction):
    # Need to respond with type=6, or proceeding code will execute twice.
    await interaction.respond(type=6)
    ctx = await bot.get_context(interaction.message)
    await ctx.invoke(bot.get_command(str(interaction.custom_id)))

# Fetches latest agenda and puts in Discord embed
@tasks.loop(hours=6)
async def check_hourly():
    ctx = await bot.get_context(channel.last_message)
    await ctx.invoke(bot.get_command('fetch_agendas'))

@bot.command(aliases=['check', 'ga', 'agenda', 'latest agenda', 'agendas', 'schedule', 'get', 'fetch'])
async def fetch_agendas(ctx, amount=5):
    lprint("Checking for new agendas...")
    await ctx.send('Checking...')
    if agenda := check_if_new(amount):  # Checks newly scraped data is different from latest_agendas.txt file.
        embed = discord.Embed(title='Latest Agendas')
        for i in range(len(agenda)):
            embed.add_field(name=agenda[i][0], value=f'Date: {agenda[i][1]}\nLink: {agenda[i][2]}', inline=False)
        await ctx.send(embed=embed)
        lprint("Agendas updated")
    else: await ctx.send('No new agendas found.')
    await channel.send(content='Click to check for new agendas, or use `.check`',
                       components=[Button(label="Check", emoji='\U0001F504', custom_id="fetch_agendas"), ])

bot.run(TOKEN)





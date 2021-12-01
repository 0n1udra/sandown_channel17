import requests, discord, sys, os
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from datetime import datetime

with open(f'{os.getenv("HOME")}/keys/channel17_bot.token', 'r') as file:
    TOKEN = file.readline()

def sprint(msg): print(f'{datetime.today()} | {msg}')

# ========== Web Scraper
agenda_file = '/sandown_channel17/source/latest_agendas.txt'

def get_agendas(total=3):
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

def check_new():
    """Checks if there's a difference in latest_agenda.txt and newly pulled data from get_agendas."""
    read_data = ''
    with open(agenda_file, 'r') as file:
        read_data = file.readlines()

    agenda_data = str(get_agendas())

    if agenda_data in read_data:
        return False
    else:
        with open(agenda_file, 'w') as file:
            file.write(str(agenda_data))
        return True


# ========== Discord Bot
if not TOKEN:
    print("Token Error.")
    sys.exit()

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
async def fetch_agendas(amount=5):
    global latest_agenda
    agenda = get_agendas(amount)
    embed = discord.Embed(title='Latest Agenda')
    for i in range(len(agenda)):
        embed.add_field(name=agenda[i][0], value=f'Date: {agenda[i][1]}\nLink: {agenda[i][2]}', inline=False)
    sprint("Fetching latest agendas")
    latest_agenda = embed

# Checks if new agenda has been added.
@tasks.loop(hours=12)
async def check_new_agendas():
    sprint("Checking for new agendas")
    if check_new():
        sprint("New agenda found.")
        await fetch_agendas()
        await update_channel.send(embed=latest_agenda)

# Show latest agenda.
@bot.command(aliases=['ga', 'agenda', 'latest agenda', 'agendas', 'schedule', 'get', 'fetch'])
async def latest_agenda(ctx, amount=5):
    await ctx.send('Fetching...')
    await fetch_agendas(amount)
    await ctx.send(embed=latest_agenda)

bot.run(TOKEN)

if __name__ == '__main__':
    if 'agendas' in sys.argv:
        for i in get_agendas(): print(f'{i[1]} | {i[0]}: {i[2]}')
        sys.exit()




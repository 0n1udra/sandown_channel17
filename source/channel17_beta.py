import requests, discord, random, sys, os
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle,  Select, SelectOption, ComponentsBot
from bs4 import BeautifulSoup
from datetime import datetime

token_file = f'{os.getenv("HOME")}/keys/channel17_beta.token'
bot_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(bot_path)
print(os.getcwd())
agenda_file = bot_path + '/latest_agendas.txt'
beta_channel_id = 745829311239553047

if os.path.isfile(token_file):
    with open(token_file, 'r') as file: TOKEN = file.readline()
else:
    print("Missing Token File:", token_file)
    sys.exit()

bot = ComponentsBot(command_prefix='.')

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
        lprint(ctx, "Error scraping site")
        await priv_channel.send("**Error:** Problem scraping website.")
        return False  # If no data was recieved from scrape_agendas()
    if force: return agenda_data  # Returns data without checking against agenda_file.

    if not os.path.isfile(agenda_file):
        new_file = open(agenda_file, 'w')
        new_file.close()

    read_data = ''
    with open(agenda_file, 'r') as file:
        read_data = file.readlines()

    if str(agenda_data) not in read_data:
        with open(agenda_file, 'w') as file:
            file.write(str(agenda_data))
            return agenda_data
    else: return False

# ========== Discord Bot
main_channel = priv_channel = None

@bot.event
async def on_ready():
    global main_channel, priv_channel
    lprint(ctx, "Bot Connected.")
    await bot.wait_until_ready()
    priv_channel = bot.get_channel(beta_channel_id)
    await priv_channel.send('**Bot PRIMED** :white_check_mark:')
    check_hourly.start()

@bot.event
async def on_button_click(interaction):
    # Need to respond with type=6, or proceeding code will execute twice.
    await interaction.respond(type=6)
    ctx = await bot.get_context(interaction.message)
    await ctx.invoke(bot.get_command(str(interaction.custom_id)))

@tasks.loop(hours=6)
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

    if agenda := await check_if_new(amount, force):
        await ctx.send('New Agendas Found.')
        embed = discord.Embed(title='Latest Agendas')
        for i in range(len(agenda)):
            embed.add_field(name=agenda[i][0], value=f'Date: {agenda[i][1]}\nLink: {agenda[i][2]}', inline=False)
        await ctx.send(embed=embed)
    else:
        if not from_check_hourly:
            await ctx.send('No new agendas found.')

    if not from_check_hourly:
        await ctx.send(content='Click to check for new agendas, or use `.check`',
                       components=[[Button(label="Check for new", emoji='\U0001F504', custom_id="check_agendas"),
                                    Button(label="Show current", emoji='\U00002B07', custom_id="get_agendas"), ]])

    lprint(ctx, "Fetched Agenda")

@bot.command(aliases=['get', 'agendas'])
async def get_agendas(ctx):
    """Shows agendas even if no new ones found."""

    await ctx.invoke(bot.get_command('check_agendas'), force=True)

@bot.command(aliases=['rbot', 'rebootbot', 'botrestart', 'botreboot'])
async def restartbot(ctx, now=''):
    """Restart this bot."""

    lprint(ctx, "Restarting bot...")
    #os.chdir(bot_path)
    #print(os.getcwd())
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.command(aliases=['updatebot', 'botupdate', 'git', 'update'])
async def gitupdate(ctx):
    """Gets update from GitHub."""

    await ctx.send("***Updating from GitHub...*** :arrows_counterclockwise:")
    os.chdir(os.getcwd())
    os.system('git pull')
    await ctx.invoke(bot.get_command("restartbot"))

bot.run(TOKEN)

import requests
from datetime import datetime as dt
from bs4 import BeautifulSoup

agenda_file = '/home/slime/git/sandown_channel17/discord_bot/scripts/latest_agendas.txt'

def get_agendas(total=5):
    meetings = []

    # Requests sandown.us/minutes-and-agenda.
    sandown_website = requests.get('https://www.sandown.us/minutes-and-agendas')
    sandown_url = 'https://www.sandown.us'
    soup = BeautifulSoup(sandown_website.text, 'html.parser')
    # Only gets links for schedules in Agendas column.
    div_agenda = soup.find_all('div', class_='minutes-agendas-second-column')
    for i in div_agenda[0].find_all('a'):
        current_url = f"{i.get('href')}/{dt.today().year}"

        #Extracts name and date of meeting.
        data = BeautifulSoup(requests.get(current_url).text, "html.parser")
        file_dates = data.find_all('div', class_='field-content')
        file_names = data.find_all('h3')

        for name, date in zip(file_names, file_dates):
            for url in name.find_all('a'):
                file_url = sandown_url + url.get('href')
            meetings.append([name.text, dt.strptime((date.text), '%B %d, %Y - %I:%M%p'), file_url])

    meetings.sort(key=lambda x: x[1])
    return meetings[-total:]


def check_new():
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


def show_agendas():
    for i in get_agendas():
        print(f'{i[1]} | {i[0]}, {i[2]}')


if __name__ == '__main__':
    if check_new():
        print("New agendas found")
    else:
        print("No new agendas.")
    

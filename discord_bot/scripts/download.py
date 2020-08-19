import requests
response = requests.get("https://www.sandown.us/minutes-and-agendas")

data = response.text
# Write data to file
filename = "sandown_us.txt"
file_ = open(filename, 'w')
file_.write(data)
file_.close()

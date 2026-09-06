import requests
from bs4 import BeautifulSoup

url = 'https://www.youtube.com/results?search_query=ICT+SMC+trading+strategy'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

soup = BeautifulSoup(response.text, 'html.parser')

for title in soup.find_all('a', id='video-title')[:5]:
    print(title.text.strip(), 'https://www.youtube.com' + title['href'])

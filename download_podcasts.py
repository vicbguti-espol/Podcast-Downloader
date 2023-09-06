from podcast import Podcast
import dateutil.parser
import requests
import re

def get_episodes_metadata(podcast_items):
    episode_urls = [podcast.find('enclosure')['url'] for podcast in podcast_items]
    episode_titles = [podcast.find('title').text for podcast in podcast_items]
    episode_release_dates = [parse_date(podcast.find('pubDate').text) for podcast in podcast_items]
    return list(zip(episode_urls, episode_titles, episode_release_dates))

def parse_date(date):
	return dateutil.parser.parse(date).strftime('%b-%d-%Y')

def get_mp3_file(url):
	# It redirects the url before you get the actual file
	redirect_url = requests.get(url).url
	file = requests.get(redirect_url)
	return file

def save_mp3_file(file, file_path):
    with open(file_path, 'wb') as f:
        f.write(file.content)

def simplify_title(title):
	file_name = re.sub(r'[%/&!@#\*\$\?\+\^\\.\\\\]', '', title)[:100].replace(' ', '-')
	# file_name = title.replace('/','-').replace('\\\\','-').replace('.',' ')[:100]
	return file_name

if __name__ == '__main__':
	print("\n--- Downloading podcasts... ---\n")
	podcast_list = [Podcast('psi-mammoliti', 'https://anchor.fm/s/28fef6f0/podcast/rss')]

	for podcast in podcast_list:
		podcast_items = podcast.search_items('Me sentí demasiado cansado, quisiera que no me vuelva a pasar', limit=2)
		# podcast_items = podcast.get_items()[:5]
		episodes_metadata = get_episodes_metadata(podcast_items)
		i = 1 ## 
		for episode in episodes_metadata:
			url, title, release_date = episode
			simple_title = simplify_title(title)
			file = get_mp3_file(url)
			# file_path = f'{podcast.download_directory}/{release_date}.mp3'
			file_path = f'{podcast.download_directory}/{simple_title}.mp3'
			# file_path = f'{podcast.download_directory}/E{i}.mp3' ## 
			save_mp3_file(file, file_path)
			print(file_path, "saved")
			i += 1

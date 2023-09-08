from podcast import Podcast
import dateutil.parser
import requests
import re
import json

def get_episodes_metadata(podcast_items):
    episode_urls = [podcast.find('enclosure')['url'] for podcast in podcast_items]
    episode_titles = [podcast.find('title').text for podcast in podcast_items]
    episode_release_dates = [parse_date(podcast.find('pubDate').text) for podcast in podcast_items]
    episode_descriptions = [podcast.find('description').text for podcast in podcast_items]
    return list(zip(episode_urls, episode_titles, episode_release_dates, episode_descriptions))

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
    return file_name

# def save_download_metadata(metadata, file_path='./download_metadata.json'):
#     with open(file_path,'w') as f:
#         json.dump(metadata, f)

def get_podcast_list(raw_podcast_list):
    podcast_list = []

    for raw_podcast in raw_podcast_list:
        podcast_list += [Podcast(raw_podcast['name'], raw_podcast['rss_feed_url'])]
    
    return podcast_list

def load_json(file_path):
    with open(file_path) as json_file:
        dictionary = json.load(json_file)
    return dictionary


if __name__ == '__main__':
    print("\n--- Downloading podcasts... ---\n")
    raw_podcast_list = load_json('./podcast_list.json')['podcast_list']
    podcast_list = get_podcast_list(raw_podcast_list)
    
    search = 'Me sentí demasiado cansado, quisiera que no me vuelva a pasar'
    download_metadata = {}
    for podcast in podcast_list:
        podcast_items = podcast.search_items(search, limit=2)
        episodes_metadata = get_episodes_metadata(podcast_items)
        for episode in episodes_metadata:
            url, title, release_date, description = episode
            simple_title = simplify_title(title)
            file = get_mp3_file(url)
            file_path = f'{podcast.download_directory}/{simple_title}.mp3'
            
            if (podcast.name not in download_metadata):
                download_metadata[podcast.name] = {f'{title}': description}
            else:
                download_metadata[podcast.name][f'{title}'] = description
            
            save_mp3_file(file, file_path)
            print(file_path, "saved")
    # save_download_metadata(download_metadata)

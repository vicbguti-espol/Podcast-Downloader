import requests
import os
import re
from bs4 import BeautifulSoup
import dateutil.parser
import openai
import numpy as np
from dotenv import load_dotenv, find_dotenv
import pickle
import time
import json

load_dotenv(find_dotenv())
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("API_BASE")

class Podcast:
    def __init__(self, name, rss_feed_url):
        self.name = name
        self.rss_feed_url = rss_feed_url
        
        self.download_directory = f'./downloads/{name}'
        if not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)

        self.transcription_directory = f'./transcripts/{name}'
        if not os.path.exists(self.transcription_directory):
            os.makedirs(self.transcription_directory)
            

    def get_items(self):
        page = requests.get(self.rss_feed_url)
        soup = BeautifulSoup(page.text, 'xml')
        return soup.find_all('item')

    # def search_items(self, search, limit=None):
    # 	matched_podcasts = []
    # 	items = self.get_items()
    # 	for podcast in items:
    # 		if re.search(search, podcast.find('description').text, re.I):
    # 			matched_podcasts.append(podcast)

    # 	return matched_podcasts[:limit]

    def get_embedding(self, text, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input = text, model=model)['data'][0]['embedding']
    
    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    def get_items_embeddings(self, last_items):
        # items_embeddings = []
        items_embeddings = {}
        # items_embeddings_path = f'{self.download_directory}/{self.name}.pickle'
        ITEMS_EMB_PATH = f'./items_embeddings/{self.name}.json'
        if not os.path.exists(ITEMS_EMB_PATH): 
            items = self.get_items()[:last_items]
            i = 0
            for podcast in items:
                
                item_embedding = {}
                if (i % 10 == 0):
                    time.sleep(8)
                description = podcast.find('description').text
                soup = BeautifulSoup(description, 'html.parser')
                description = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
                description_embedding = self.get_embedding(description)
                # items_embeddings.append((podcast, description_embedding))
                # items_embeddings[f'E{i}'] = {'title': podcast.find('title').text,
                #                               'podcast': podcast, 
                #                               'embedding': description_embedding}
                
                items_embeddings[f'E{i}'] = {'title': podcast.find('title').text,
                                              'embedding': description_embedding}
                i += 1          

            # Serializar items_embeddings
            # with open(items_embeddings_path, 'wb') as f:
            #     pickle.dump(items_embeddings, f)

            with open(ITEMS_EMB_PATH, 'w') as f:
                json.dump(items_embeddings, f)
        else:
            # with open(items_embeddings_path, 'rb') as f:
            #     items_embeddings = pickle.load(f)

            with open(ITEMS_EMB_PATH, 'r') as f:
               items_embeddings = json.load(f) 
        
        return items_embeddings

    def search_items(self, search, limit=2, last_items=10):
        # items_embeddings = []
        items = self.get_items()
        search_embedding = self.get_embedding(search)
        items_embeddings = self.get_items_embeddings(last_items)
        # for podcast in items:
        #     description = podcast.find('description').text
        #     soup = BeautifulSoup(description, 'html.parser')
        #     description = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
        #     description_embedding = self.get_embedding(description)
        #     items_embeddings.append((podcast, description_embedding))
        
        # items_embeddings.sort(key=lambda x: self.cosine_similarity(x[1], search_embedding))

        # matched_podcasts = [item[0] for item in items_embeddings[:limit]]

        sorted_items = sorted(items_embeddings.values(),
                                   key=lambda item: self.cosine_similarity(item['embedding'],
                                                                            search_embedding))[:limit]
        # Obtener los títulos de todos los podcasts
        items_titles = [podcast.find('title').text for podcast in items]
        matched_podcasts = []
        for item in sorted_items:
            # Buscar el item que tenga el mismo título, entre items y sorted_items
            ind_podcast = items_titles.index(item['title'])
            podcast = items[ind_podcast]
            matched_podcasts.append(podcast)
            
        # matched_podcasts = [sorted_item['podcast'] for sorted_item in sorted_items[:limit]]
        return matched_podcasts


            
        
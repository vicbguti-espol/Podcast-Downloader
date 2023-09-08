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

        self.description_embeddings_path = f'./description_embeddings/{self.simplify_title()}.json'
           

    def get_items(self):
        page = requests.get(self.rss_feed_url)
        soup = BeautifulSoup(page.text, 'xml')
        return soup.find_all('item')

    def get_embedding(self, text, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input = text, model=model)['data'][0]['embedding']
    
    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def simplify_title(self):
        file_name = re.sub(r'[%/&!@#\*\$\?\+\^\\.\\\\]', '', self.name)[:100].replace(' ', '-')
        return file_name
        
    # def get_items_embeddings(self, last_items):
    #     items_embeddings = {}
    #     ITEMS_EMB_PATH = f'./items_embeddings'
    #     JSON_PATH = f'{ITEMS_EMB_PATH}/{self.simplify_title()}.json'

    #     if not os.path.exists(ITEMS_EMB_PATH):
    #         os.mkdir(ITEMS_EMB_PATH)

    #     if not os.path.exists(JSON_PATH): 
    #         items = self.get_items()[:last_items]
    #         i = 0
    #         for podcast in items:
    #             if (i % 10 == 0):
    #                 time.sleep(8)
    #             description = podcast.find('description').text
    #             soup = BeautifulSoup(description, 'html.parser')
    #             description = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
    #             description_embedding = self.get_embedding(description)
                
    #             items_embeddings[f'E{i}'] = {'title': podcast.find('title').text,
    #                                           'embedding': description_embedding}
    #             i += 1          

    #         with open(JSON_PATH, 'w') as f:
    #             json.dump(items_embeddings, f)
    #     else:

    #         with open(JSON_PATH, 'r') as f:
    #            items_embeddings = json.load(f) 
        
    #     return items_embeddings

    def save_description_embeddings(self, description_embeddings):
        description_embeddings_json = {'description_embeddings':description_embeddings}
        with open(self.description_embeddings_path, 'w') as f:
                json.dump(description_embeddings_json, f)

    def add_description_embeddings(self, items_limit):
        # Obtener el arreglo de description_embeddings
        description_embeddings = self.get_description_embeddings()['description_embeddings']
        # Obtener los episodios del podcast
        items = self.get_items()

        i = 0
        for item in items:
            # Obtener la descripción del episodio
            description = item.find('description').text
            soup = BeautifulSoup(description, 'html.parser')
            description = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])

            if description not in [d['description'] for d in description_embeddings] and i < items_limit:
                # Dormir el lazo 8 segundos por cada 10 embeddings
                if (i % 9 == 0):
                    time.sleep(8)
                # Obtener el embedding de la descripción del episodio
                description_embedding = self.get_embedding(description)
                # Agregar la descripción del episodio con su embedding
                description_embeddings += [{'description': description, 'embedding': description_embedding}]
                i += 1
        # Actualizar description_embeddings
        self.save_description_embeddings(description_embeddings)

    def get_description_embeddings(self):
        description_embeddings = None

        # Declarar el archivo de embeddings de las descripciones de los episodios
        description_embeddings_dir = f'./description_embeddings'
        if not os.path.exists(description_embeddings_dir):
            os.mkdir(description_embeddings_dir)  
        
        if not os.path.exists(self.description_embeddings_path): 
            # Crear el json de description_embeddings 
            description_embeddings = [{"description": "", "embedding":""}]
            self.save_description_embeddings(description_embeddings)
        else:
            # Cargar el archivo json de description_embeddings
            with open(self.description_embeddings_path, 'r') as f:
                description_embeddings = json.load(f)

        return description_embeddings


    # def search_items(self, search, limit=2, last_items=10):
    #     items = self.get_items()
    #     search_embedding = self.get_embedding(search)
    #     items_embeddings = self.get_items_embeddings(last_items)

    #     sorted_items = sorted(items_embeddings.values(),
    #                                key=lambda item: self.cosine_similarity(item['embedding'],
    #                                                                         search_embedding))[:limit]
    #     # Obtener los títulos de todos los podcasts
    #     items_titles = [podcast.find('title').text for podcast in items]
    #     matched_podcasts = []
    #     for item in sorted_items:
    #         # Buscar el item que tenga el mismo título, entre items y sorted_items
    #         ind_podcast = items_titles.index(item['title'])
    #         podcast = items[ind_podcast]
    #         matched_podcasts.append(podcast)

    #     return matched_podcasts

    def search_items(self, search_embedding, top_limit=2, items_limit=10):
        items = self.get_items()
        items_embeddings = self.get_description_embeddings()

        sorted_items = sorted(items_embeddings.values(),
                                   key=lambda item: self.cosine_similarity(item['embedding'],
                                                                            search_embedding))[:top_limit]
        # Obtener los títulos de todos los podcasts
        items_titles = [podcast.find('title').text for podcast in items]
        matched_podcasts = []
        for item in sorted_items:
            # Buscar el item que tenga el mismo título, entre items y sorted_items
            ind_podcast = items_titles.index(item['title'])
            podcast = items[ind_podcast]
            matched_podcasts.append(podcast)

        return matched_podcasts

            
        
### version = 2.4

import re
import time
import urllib.parse as urlparse
import requests
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, SparseTextEmbedding
from groq import Groq
from markdownify import markdownify as md
from spellchecker import SpellChecker


class Widiscover:

    def __init__(self, 
        dense_model_name='sentence-transformers/all-MiniLM-L6-v2',
        sparse_model_name='prithivida/Splade_PP_en_v1',
        generative_model='llama-3.3-70b-versatile',
        groq_api_key=None,
    ):
        self.headers = {
                "User-Agent": "Widiscover 2.4"
            }
        self.ENGLISH = {
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "you're", "you've", "you'll", "you'd",
            "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "she's", "her", "hers", "herself",
            "it", "it's", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", 
            "this", "that", "that'll", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", 
            "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", 
            "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", 
            "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", 
            "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", 
            "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
            "t", "can", "will", "just", "don", "don't", "should", "should've", "now", "d", "ll", "m", "o", "re", "ve", "y", 
            "ain", "aren", "aren't", "couldn", "couldn't", "didn", "didn't", "doesn", "doesn't", "hadn", "hadn't", "hasn", 
            "hasn't", "haven", "haven't", "isn", "isn't", "ma", "mightn", "mightn't", "mustn", "mustn't", "needn", "needn't", 
            "shan", "shan't", "shouldn", "shouldn't", "wasn", "wasn't", "weren", "weren't", "won", "won't", "wouldn", "wouldn't"
        }
        self.database_client = None
        self.collection_name = 'Widiscover 2.4'
        self.DENSE_MODEL_DIMENSION = 384
        self.vectorizer = None
        self.sparse_vectorizer = None
        if groq_api_key:
            self.groq = Groq(
                    api_key=groq_api_key
                )
        else:
            self.groq = Groq()
        if not self.groq:
            raise Exception('Error: Groq client couldn\'t be loaded')
        self.database_client = QdrantClient(":memory:")
        if not self.database_client:
            raise Exception('Error: QDrant client couldn\'t be loaded')
        time.sleep(0.02)
        if not self.database_client.collection_exists(collection_name=self.collection_name):
            self.database_client.create_collection(
                    collection_name= self.collection_name,
                    vectors_config={'dense': models.VectorParams(
                        size=self.DENSE_MODEL_DIMENSION,
                        distance=models.Distance.COSINE
                    )},
                    sparse_vectors_config={
                        'sparse': models.SparseVectorParams()
                    }
                )
        self.dense_model_name = dense_model_name
        self.sparse_model_name = sparse_model_name
        self.vectorizer = TextEmbedding(model_name=dense_model_name)
        self.sparse_vectorizer = SparseTextEmbedding(model_name=sparse_model_name)
        if not self.vectorizer:
            raise Exception('Error: FastEmbed vectorizer couldn\'t be loaded')
        self.generative_model = generative_model
        self.language_code = 'en'


    def extract_keywords(self, text: str):
        '''
            Extracts a list of words from a given string excluding stopwords.
                Args:
                    text (str): The input string from which to extract keywords.
                Returns:
                    list: A list of keywords extracted from the input string.
        '''

        keywords = text.lower().replace(',', ' ').replace('.',' ').replace(':', ' ').replace('?', ' ').split(' ')
        stripped_keywords = [keyword.strip() for keyword in keywords if keyword]

        return [keyword for keyword in stripped_keywords if keyword not in self.ENGLISH and keyword]


    def extract_text(self, keys: list[str]):
        '''
            Extract Wikipedia page content as markdown for given page titles.
            Args:
                keys: List of Wikipedia page titles/keys to fetch.
            Yields:
                Markdown-formatted content for each successfully fetched page.
        '''

        for key in keys:
            response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/html/{}".format(key),
                headers=self.headers)
            if response.ok:
                yield md(response.text, autolinks=False, )
            time.sleep(0.5)


    def wikisearch(self, search_keywords, result_number_per_page = 3):
        '''
            Searches over the wikipedia API for topics related to the keywords and returns the results in URL form.
                Args:
                    search_keywords (str or list): The keywords to search for.
                    result_number_per_page (int): The number of results to return.
                    language_code (str): The language code for the Wikipedia site.
                Returns:
                    list: A list of URLs of the search results.
        '''

        search_keywords = [search_keywords] if type(search_keywords) == str else search_keywords
        params = {
            'q': '+'.join(search_keywords),
            'limit': result_number_per_page + 1
        }

        request = "https://{}.wikipedia.org/w/rest.php/v1/search/page".format(self.language_code)
        
        response = requests.get(request, headers=self.headers, params=params)
        if response.status_code == 200:
            search_results = response.json()
        else:
            return
        urls = []
        cnt = 0
        for result in search_results['pages']:
            if result.get('description') == 'Topics referred to by the same term':
                continue
            urls.append(
                result['key']
            )
            cnt+=1
            if cnt == result_number_per_page:
                break
        return urls
    

    def process_docs(self, docs: list, sources: list, length=1800, overlap=180):
        
        chunks = []
        for text, source in zip(docs, sources):
            offset = 0
            text_len = len(text)
            while True:
                chunk = text[offset:offset+length]
                chunks.append({
                    'metadata':{
                        'text':chunk,
                        'source':source
                        },
                    'vectors':{
                        'dense': models.Document(text=chunk, model=self.dense_model_name),
                        'sparse': models.Document(text=chunk, model=self.sparse_model_name)
                    }
                })
                if offset + length >= text_len:
                    break
                offset += length - overlap
        return chunks


    def search_chunks(self, query, chunks, top_k=4, threshold=0.3):
        if chunks.__len__() < top_k:
            top_k = chunks.__len__()
            
        self.database_client.upload_collection(
            collection_name=self.collection_name,
            vectors=[chunk['vectors'] for chunk in chunks],
            payload=[chunk['metadata'] for chunk in chunks],
            parallel=4)
        search_results = self.database_client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=models.Document(text=query, model=self.dense_model_name),
                    using='dense',
                    limit=32
                ),
            ],
            query=models.Document(text=query, model=self.sparse_model_name),
            using='sparse',
            with_payload=True,
            limit=top_k
            )
            
        return [search_results.points[k].payload for k in range(top_k) if search_results.points[k].score >= threshold]
        

    def clear_data(self):
        self.database_client.delete_collection(self.collection_name)


    def answer(self, query: str, context: list[dict], spelling=0):
        '''
        Generates an answer based on the retrieved context.

            Params:
                * **query (str)**: The query string to search for in the database.
                * **context (list[str])**: A list of dictionaries containing `text` and `source` fields.

            Returns:
                A dictionary containing the generated answer, its sources and usage statistics.
        '''

        def check_spelling(query):
            spell = SpellChecker(distance=spelling)
            words = query.strip().split()
            # If a word contains at least one upper case character or is inside quotes ignore correction for this word
            corrected_words = [spell.correction(word) or word 
                            if (word.islower() or word[0] == "'" or word[0] == '"') else word 
                            for word in words]
            return " ".join(corrected_words)
            
        def generate(query: str, context: list[str], model=self.generative_model):
            assert type(context) == list
            system_prompt = '''
You are an assistant that answers questions strictly based on the CONTEXTS below.
Do not use external knowledge or guess. If the answer is missing, say: "I don't know the answer."
Keep responses concise (1-2 sentences unless more detail is needed).
'''
            system_prompt += ''.join(['\n\n<CONTEXT>\n' + item + '\n</CONTEXT>' for item in context])
            
            response = self.groq.chat.completions.create(
                messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                ],
                model=model,
            )
            return {
                'answer' : response.choices[0].message.content,
                'usage' : {
                    'completion_time': response.usage.completion_time,
                    'prompt_time': response.usage.prompt_time,
                    'total_time': response.usage.total_time,

                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens,
                }
            }
        
        if not query:
            return
        if int(spelling):
            query = check_spelling(query)
        text_results = [item['text'] for item in context]
        sources = {item['source'] for item in context}
        results = generate(query=query, context=text_results)
        return {
            'answer': results['answer'],
            'sources': ["https://{}.wikipedia.org/wiki/".\
                format(self.language_code) + source for source in sources],
            'usage': results['usage'],
        }
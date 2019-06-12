import bs4 as bs
import urllib.request
import re
import heapq
import nltk

from plugin import Plugin


def load(data_dir, bot):
    return Summary(data_dir, bot)


"""
Created by Matthew Klawitter 5/16/2019
Last Updated: 5/16/2019
Version: v1.0.0.0
"""


class Summary(Plugin):
    def __init__(self, data_dir, bot):
        self.data_dir = data_dir
        self.bot = bot

    def create_summary(self, command):
        url = command.args

        scraped_article = urllib.request.urlopen(url)
        article = scraped_article.read()
        parsed_article = bs.BeautifulSoup(article,'lxml')

        paragraphs = parsed_article.find_all('p')
        article_text = ""

        for p in paragraphs:
            article_text += p.text

        # Some preprossesing
        article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)  
        article_text = re.sub(r'\s+', ' ', article_text)

        formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )  
        formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)  

        sentence_list = nltk.sent_tokenize(article_text) 

        stopwords = nltk.corpus.stopwords.words('english')

        word_frequencies = {}  
        for word in nltk.word_tokenize(formatted_article_text):  
            if word not in stopwords:
                if word not in word_frequencies.keys():
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1

        maximum_frequncy = max(word_frequencies.values())

        for word in word_frequencies.keys():  
            word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)

        sentence_scores = {}  
        for sent in sentence_list:  
            for word in nltk.word_tokenize(sent.lower()):
                if word in word_frequencies.keys():
                    if len(sent.split(' ')) < 30:
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word]
                        else:
                            sentence_scores[sent] += word_frequencies[word]

        summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)

        summary = ' '.join(summary_sentences)
        return "Article Summary:\n" + summary

    def on_command(self, command):
        if command.command == "summary" or command.command == "s":
            return {"type": "message", "message": self.create_summary(command)}

    def get_commands(self):
        return {"summary", "s"}

    def get_name(self):
        return "Summarize"

    def get_help(self):
        return "'/summary [url]' or '/s [url]' to view a summary of an article"

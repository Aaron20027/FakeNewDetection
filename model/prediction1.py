from tensorflow.keras.preprocessing.text import Tokenizer
import re
import bisect
import numpy as np
import pandas as pd
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator
from nltk import download

class Prediction1():
    pass





    


class Prediction():
    def __init__(self, text):
        self.text=text
        self.model = load_model("static/BiLSTMModel_VADER.h5")

        with open("static/BiLSTMModel_VADER_TOKENIZER.pkl", "rb") as file:
            self.tokenizer = pickle.load(file)
            
        self.sentiment=None
        self.intensity=None
        self.intensity_encoded=None
        self.padded_text=None
        self.prediction=None
        self.label=None

    def analyze(self):
        self.translate_text(self.text)
        self.preprocess_text()
        self.get_sentiment()
        num_features = np.hstack(([self.sentiment], self.intensity_encoded[0]))
        num_features = np.expand_dims(num_features, axis=0)
        self.pad_text()
        self.prediction = self.model.predict([self.padded_text, num_features])
        self.label = "Real" if self.prediction[0] >= 0.5 else "Fake"
        return self.label

    def split_text(self, text, max_length=4000):
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    def translate_text(self, text, target_lang='en'):
        if not text:  
            return "" 
        translator = GoogleTranslator(source='auto', target=target_lang)
        chunks = self.split_text(text)
        translated_chunks = [translator.translate(chunk) for chunk in chunks]
        self.text=" ".join(translated_chunks)
        
        
    def preprocess_text(self):
        #download('stopwords')
        stop_words = set(stopwords.words('english'))
        text = self.text.lower()
        text = re.sub(r"http\S+|www\S+|@\w+|#\w+", "", text)
        text = re.sub(r"[^\w\s]", "", text) 
        text= re.sub(r"\d+", "<num>", text)
        text = re.sub(r"[^a-zA-Z\s<>]", "", text)
        words = text.split()
        words = [word for word in words if word not in stop_words]
        #words = [lemmatizer.lemmatize(word) for word in words]
        self.text=" ".join(words)

    def pad_text(self, max_len=3000):
        sequence = self.tokenizer.texts_to_sequences([self.text])
        self.padded_text = pad_sequences(sequence,
                           maxlen = max_len,
                           padding = 'post',
                           truncating = 'post')

    def get_sentiment(self):
        my_analyzer = SentimentIntensityAnalyzer()
        scores = my_analyzer.polarity_scores(self.text)
        
        compound_score = scores['compound']

        bins = [-float('inf'), -0.5, -0.00001, 0.00001, 0.5, float('inf')]
        labels = ['Strongly Negative', 'Weakly Negative', 'Neutral', 'Weakly Positive', 'Strongly Positive']
       
        index = bisect.bisect_right(bins, compound_score) - 1

        self.intensity=labels[index]
        self.intensity_encoded = pd.get_dummies([self.intensity], dtype=int).reindex(labels, axis=1, fill_value=0).to_numpy()
        
        if compound_score >= 0.05:
            self.sentiment=1
        elif compound_score <= -0.05:
            self.sentiment=-1
        else:
            self.sentiment=0

    def return_sentiment(self):
        return self.sentiment

    def return_intensity(self):
        return self.intensity


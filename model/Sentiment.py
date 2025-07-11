import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


def analyze_sentiment(text):
        my_analyzer = SentimentIntensityAnalyzer()
        scores = my_analyzer.polarity_scores(text)
        compound_score = scores['compound']


        if compound_score >= 0.05:
            sentiment = 'positive'
        elif compound_score <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        if compound_score <= -0.5:
            intensity_category = 'Strongly Negative'
        elif compound_score < -0.00001:
            intensity_category = 'Weakly Negative'
        elif compound_score <= 0.00001:
            intensity_category = 'Neutral'
        elif compound_score < 0.5:
            intensity_category = 'Weakly Positive'
        else:
            intensity_category = 'Strongly Positive'

        return {
            'sentiment': sentiment,
            'intensity': compound_score,
            'intensity_category': intensity_category
        }
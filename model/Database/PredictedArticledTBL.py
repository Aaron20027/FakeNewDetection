
#from model.extensions import engine
from sqlalchemy import text
from model.Utils import DatabaseError

from model.Sentiment import analyze_sentiment

class PredictedArticlesTable():
    def __init__(self, db_connection):
        self.engine = db_connection

    def add_predicted_article(self, article_text, label):
        query = text("""
            INSERT INTO predicted_articles_tbl (article_text, label, sentiment, sentiment_intensity, predicted_at)
            VALUES (:article_text, :label ,:sentiment, :sentiment_intensity, NOW() )
        """)


        sentiment=analyze_sentiment(article_text)


        try:
            with self.engine.connect() as conn:
                conn.execute(query, {
                    "article_text": article_text,
                    "label": label,
                    "sentiment": sentiment['sentiment'],
                    "sentiment_intensity":  sentiment['intensity_category'],
                })
                conn.commit()
        except Exception as e:
            print(f"Error logging predicted article: {e}")
            raise DatabaseError(e)
        
        

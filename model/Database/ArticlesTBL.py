
#from model.extensions import engine
from sqlalchemy import text
from model.Utils import DatabaseError

from model.Sentiment import analyze_sentiment

from model.Articles import Articles

class ArticlesTable():
    def __init__(self, db_connection):
        self.engine = db_connection

    def add_article(self, title,  article_text, label ,sources, submitted_by):
        query = text("""
            INSERT INTO articles_tbl (title, article_text, label, sources, sentiment, sentiment_intensity, submitted_by)
            VALUES (:title, :article_text, :label, :sources ,:sentiment, :sentiment_intensity, :submitted_by)
        """)

        if not sources or sources.strip() == "":
            sources = None

        sentiment=analyze_sentiment(article_text)


        try:
            with self.engine.connect() as conn:
                conn.execute(query, {
                    "title": title,
                    "article_text": article_text,
                    "label": label,
                    "sources": sources,
                    "sentiment": sentiment['sentiment'],
                    "sentiment_intensity":  sentiment['intensity_category'],
                    "submitted_by": submitted_by
                })
                conn.commit()
        except Exception as e:
            print(f"Error logging article: {e}")
            raise DatabaseError(e)
        
        

    def update_article(self, article_id , factchecker, **fields_to_update):
        if not fields_to_update:
            print("No fields to update.")
            return
        
        set_clauses = [f"{key} = :{key}" for key in fields_to_update]
        fields_to_update["article_id"] = article_id 

        if 'article_text' in fields_to_update:
            set_clauses.append("sentiment = :sentiment")
            set_clauses.append("sentiment_intensity = :sentiment_intensity")


            article_text = fields_to_update['article_text']
            sentiment=analyze_sentiment(article_text)


            fields_to_update["sentiment"] = sentiment['sentiment']
            fields_to_update["sentiment_intensity"] = sentiment['intensity_category']

        if 'status' in fields_to_update:
            set_clauses.append("factchecked_by = :factchecked_by")
            set_clauses.append("factchecked_at = CURRENT_TIMESTAMP")
            fields_to_update["factchecked_by"] = factchecker



        query = text(f"""
            UPDATE articles_tbl
            SET {', '.join(set_clauses)}
            WHERE article_id  = :article_id 
        """)

        try:
            with self.engine.connect() as conn:
                conn.execute(query, fields_to_update)
                conn.commit()
        except Exception as e:
            print(f"Error updating article: {e}")
            raise DatabaseError(e)


    def get_articles(self, offset=0, limit=10):
        params = {"limit": limit, "offset": offset}

        count_query = text(f"""
            SELECT COUNT(*) FROM articles_tbl
        """)

        query=text("""
            SELECT *, usr.username as username FROM articles_tbl AS art LEFT JOIN users_tbl AS usr ON art.submitted_by=usr.user_id
                   ORDER BY submitted_at DESC 
                   LIMIT :limit OFFSET :offset
        """)

       

        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                articles = []

                if result:
                    for row in result:
                        article = Articles(
                            article_id=row["article_id"],
                            title=row["title"],
                            article_text=row["article_text"],
                            label=row["label"],
                            sentiment=row["sentiment"],
                            sentiment_intensity=row["sentiment_intensity"],
                            sources=row["sources"],
                            submitted_by=row["username"],
                            submitted_at=row["submitted_at"],
                            factchecked_by=row["factchecked_by"],
                            factchecked_at=row["factchecked_at"],
                            status=row["status"],
                            updated_at=row["updated_at"]
                        )
                        articles.append(article)
                    
                    return articles, total_result
                else: 
                    return articles, 0
                
        except Exception as e:
            print(f"Error getting articles: {e}")
            raise DatabaseError(e)
        


    def search_articles(self, user_input, offset=0, limit=10):
        search_term = f"%{user_input.strip()}%"  # sanitize user input
        params = {
            "search": search_term,
            "limit": limit,
            "offset": offset
        }

        #CHANGE FACKCHECD BY TO USERNAME
        count_query = text(f"""
            SELECT COUNT(*)
            FROM articles_tbl AS art 
            LEFT JOIN users_tbl AS usr ON art.submitted_by=usr.user_id
            WHERE
                title LIKE :search
                OR article_text LIKE :search
                OR label LIKE :search
                OR sentiment LIKE :search
                OR sentiment_intensity LIKE :search
                OR sources LIKE :search
                OR CAST(username AS CHAR) LIKE :search
                OR CAST(submitted_at AS CHAR) LIKE :search
                OR CAST(factchecked_by AS CHAR) LIKE :search
                OR CAST(factchecked_at AS CHAR) LIKE :search
                OR status LIKE :search
        """)

        query = text("""
            SELECT
            *, usr.username as username
            FROM articles_tbl AS art 
            LEFT JOIN users_tbl AS usr ON art.submitted_by=usr.user_id
            WHERE 
                title LIKE :search
                OR article_text LIKE :search
                OR label LIKE :search
                OR sentiment LIKE :search
                OR sentiment_intensity LIKE :search
                OR sources LIKE :search
                OR CAST(username AS CHAR) LIKE :search
                OR CAST(submitted_at AS CHAR) LIKE :search
                OR CAST(factchecked_by AS CHAR) LIKE :search
                OR CAST(factchecked_at AS CHAR) LIKE :search
                OR status LIKE :search
            ORDER BY submitted_at DESC
            LIMIT :limit OFFSET :offset
        """)



        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query,params).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                articles = []

                if result:
                    for row in result:
                        article = Articles(
                            article_id=row["article_id"],
                            title=row["title"],
                            article_text=row["article_text"],
                            label=row["label"],
                            sentiment=row["sentiment"],
                            sentiment_intensity=row["sentiment_intensity"],
                            sources=row["sources"],
                            submitted_by=row["username"],
                            submitted_at=row["submitted_at"],
                            factchecked_by=row["factchecked_by"],
                            factchecked_at=row["factchecked_at"],
                            status=row["status"],
                            updated_at=row["updated_at"]
                        )
                        articles.append(article)
                    
                    return articles, total_result
                else: 
                    return articles, 0
                
        except Exception as e:
            print(f"Error getting articles: {e}")
            raise DatabaseError(e)
        


    def get_article_by_id(self, input_article_id):
        query=text("""
            SELECT * FROM articles_tbl
            WHERE article_id= :article_id
        """)


        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"article_id": input_article_id}).mappings().fetchone()
                #print(result[0])

                if result:
                    article = Articles(
                            result["article_id"],
                            result["title"],
                            result["article_text"],
                            result["label"],
                            result["sentiment"],
                            result["sentiment_intensity"],
                            result["sources"],
                            result["submitted_by"],
                            result["submitted_at"],
                            result["factchecked_by"],
                            result["factchecked_at"],
                            result["status"],
                            result["updated_at"])
                    return article 
                else: 
                    return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            raise DatabaseError(e)
        
    
    def get_approved_articles(self, offset=0, limit=10):
        params = {"limit": limit, "offset": offset}

        count_query = text(f"""
            SELECT COUNT(*) FROM articles_tbl  WHERE status='approved'
        """)

        query=text("""
            SELECT * FROM articles_tbl WHERE status='approved'
                   ORDER BY submitted_at DESC 
                   LIMIT :limit OFFSET :offset
        """)

       

        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                articles = []

                if result:
                    for row in result:
                        article = Articles(
                            article_id=row["article_id"],
                            title=row["title"],
                            article_text=row["article_text"],
                            label=row["label"],
                            sentiment=row["sentiment"],
                            sentiment_intensity=row["sentiment_intensity"],
                            sources=row["sources"],
                            submitted_by=row["submitted_by"],
                            submitted_at=row["submitted_at"],
                            factchecked_by=row["factchecked_by"],
                            factchecked_at=row["factchecked_at"],
                            status=row["status"],
                            updated_at=row["updated_at"]
                        )
                        articles.append(article)
                    
                    return articles, total_result
                else: 
                    return articles, 0
                
        except Exception as e:
            print(f"Error getting articles: {e}")
            raise DatabaseError(e)
        

    def get_all_approved_articles(self):
        query=text("""
            SELECT * FROM articles_tbl WHERE status='approved'  
        """)

       

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query).mappings().fetchall()
                articles = []

                if result:
                    for row in result:
                        article = Articles(
                            article_id=row["article_id"],
                            title=row["title"],
                            article_text=row["article_text"],
                            label=row["label"],
                            sentiment=row["sentiment"],
                            sentiment_intensity=row["sentiment_intensity"],
                            sources=row["sources"],
                            submitted_by=row["submitted_by"],
                            submitted_at=row["submitted_at"],
                            factchecked_by=row["factchecked_by"],
                            factchecked_at=row["factchecked_at"],
                            status=row["status"],
                            updated_at=row["updated_at"]
                        )
                        articles.append(article)
                    
                    return articles
                else: 
                    return articles
                
        except Exception as e:
            print(f"Error getting articles: {e}")
            raise DatabaseError(e)
        
        
        

    
            
            

'''

search_term = f"%{user_input.strip()}%"  # sanitize user input
params = {
    "search": search_term,
    "limit": limit,
    "offset": offset
}

query = text("""
    SELECT * FROM articles_tbl
    WHERE title LIKE :search
       OR article_text LIKE :search
       OR sources LIKE :search
       OR sentiment LIKE :search
       OR sentiment_intensity LIKE :search
       OR status LIKE :search
    ORDER BY submitted_at DESC
    LIMIT :limit OFFSET :offset
""")

'''







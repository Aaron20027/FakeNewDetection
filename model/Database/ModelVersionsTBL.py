
#from model.extensions import engine
from sqlalchemy import text

from model.Utils import DatabaseError

from model.Models import Model


class ModelVersionsTable():
    def __init__(self, db_connection):
        self.engine = db_connection

    def add_model(self, file_path, trained_by , model_accuracy, model_precision, model_recall, model_f1_score, is_active):
        query = text("""
            INSERT INTO model_versions_tbl (file_path, trained_by, model_accuracy, model_precision, model_recall, model_f1_score, is_active)
            VALUES (:file_path, :trained_by, :model_accuracy, :model_precision, :model_recall, :model_f1_score, :is_active)
        """)

        #maybe auto activate newly trained model and disabled old models

        try:
            with self.engine.connect() as conn:
                conn.execute(query, {
                    "file_path": file_path,
                    "trained_by": trained_by,
                    "model_accuracy": model_accuracy,
                    "model_precision": model_precision,
                    "model_recall": model_recall,
                    "model_f1_score": model_f1_score,
                    "is_active": is_active,
                })
                conn.commit()
        except Exception as e:
            print(f"Error logging model: {e}")
            raise DatabaseError(e)



    def update_active(self, model_id): # default 0 not active

        is_active=1

        query1 = text("""
            UPDATE model_versions_tbl SET is_active = 0
        """)

        query2 = text("""
            UPDATE model_versions_tbl SET is_active= :is_active
            WHERE model_id= :model_id
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(query1)
                conn.execute(query2, {
                    "model_id": model_id,
                    "is_active": is_active
                })
                conn.commit()
        except Exception as e:
            print(f"Error updating active model: {e}")
            raise DatabaseError(e)


    def get_models(self, offset=0, limit=10):
        params = {"limit": limit, "offset": offset}

        count_query = text(f"""
            SELECT COUNT(*) FROM model_versions_tbl
        """)

        query=text("""
            SELECT *, usr.username as username FROM model_versions_tbl AS mov LEFT JOIN users_tbl AS usr ON mov.trained_by=usr.user_id
                   ORDER BY trained_at DESC 
                   LIMIT :limit OFFSET :offset
        """)
       

        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                models = []

                if result:
                    for row in result:
                        model = Model(
                            model_id=row["model_id"],
                            file_path=row["file_path"],
                            trained_by=row["username"],
                            trained_at=row["trained_at"],
                            model_accuracy=row["model_accuracy"],
                            model_precision=row["model_precision"],
                            model_recall=row["model_recall"],
                            model_f1_score=row["model_f1_score"],
                            is_active=row["is_active"]
                        )
                        models.append(model)
                    
                    return models, total_result
                else: 
                    return models, 0
                
        except Exception as e:
            print(f"Error getting models: {e}")
            raise DatabaseError(e)
        




        

    def search_models(self,user_input, offset=0, limit=10):
        search_term = f"%{user_input.strip()}%"  # sanitize user input
        params = {
            "search": search_term,
            "limit": limit,
            "offset": offset
        }

        count_query = text(f"""
            SELECT COUNT(*)
            FROM model_versions_tbl AS mov 
            LEFT JOIN users_tbl AS usr ON mov.trained_by=usr.user_id
            WHERE
                file_path LIKE :search
                OR CAST(username AS CHAR) LIKE :search
                OR CAST(trained_at AS CHAR) LIKE :search
                OR CAST(model_accuracy AS CHAR) LIKE :search
                OR CAST(model_precision AS CHAR) LIKE :search
                OR CAST(model_recall AS CHAR) LIKE :search
                OR CAST(model_recall AS CHAR) LIKE :search
               
        """)


        query=text("""
            SELECT *, User.username AS username 
                   FROM model_versions_tbl AS mov 
                   INNER JOIN users_tbl AS User ON mov.trained_by=User.user_id
                   WHERE
                        file_path LIKE :search
                        OR CAST(username AS CHAR) LIKE :search
                        OR CAST(trained_at AS CHAR) LIKE :search
                        OR CAST(model_accuracy AS CHAR) LIKE :search
                        OR CAST(model_precision AS CHAR) LIKE :search
                        OR CAST(model_recall AS CHAR) LIKE :search
                        OR CAST(model_recall AS CHAR) LIKE :search
                   ORDER BY trained_at DESC 
                   LIMIT :limit OFFSET :offset
        """)



        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query,params).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                #print(result[0])
                models = []

                if result:
                    for row in result:
                        model = Model(
                            model_id=row["model_id"],
                            file_path=row["file_path"],
                            trained_by=row["username"],
                            trained_at=row["trained_at"],
                            model_accuracy=row["model_accuracy"],
                            model_precision=row["model_precision"],
                            model_recall=row["model_recall"],
                            model_f1_score=row["model_f1_score"],
                            is_active=row["is_active"]
                        )
                        
                        models.append(model)
                    
                    return models, total_result
                else: 
                    return models, 0
            
        except Exception as e:
            print(f"Error getting models: {e}")
            raise DatabaseError(e)
        

    def toggle_model(self, model_id):
        query = text("""
            UPDATE model_versions_tbl SET is_active=0
        """)

        query1 = text("""
            UPDATE model_versions_tbl SET is_active=1 WHERE model_id = :model_id
        """)

        try:
            with self.engine.connect() as conn:
                conn.execute(query)
                conn.execute(query1, {
                    "model_id": model_id,
                })
                conn.commit()
        except Exception as e:
            print(f"Error toggling model: {e}")
            raise DatabaseError(e)
        

    def get_active_model(self):
        query=text("""
            SELECT * FROM model_versions_tbl
            WHERE is_active= 1
        """)


        try:
            with self.engine.connect() as conn:
                result=conn.execute(query).mappings().fetchone()
                #print(result[0])

                if result:
                    model=Model(
                        result["model_id"],
                        result["file_path"],
                        result["trained_by"],
                        result["model_accuracy"],
                        result["model_precision"],
                        result["model_recall"],
                        result["model_f1_score"],
                        result["is_active"])
                
                    return model 
                else: 
                    return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            raise DatabaseError(e)










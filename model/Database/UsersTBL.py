
#from model.extensions import engine
from sqlalchemy import text
from model.User import User
import bcrypt
from flask import flash
from model.Utils import DatabaseError


class UserTable():
    def __init__(self, db_connection):
        self.engine = db_connection

    def add_user(self, username, first_name, last_name, email, password, role):
        query1 = text("""
            SELECT username FROM users_tbl
            WHERE username = :username
        """)

        query2 = text("""
            SELECT email FROM users_tbl
            WHERE email = :email
        """)
        
        query3 = text("""
            INSERT INTO users_tbl (username, first_name, last_name, email, password_hash, role)
            VALUES (:username, :first_name, :last_name, :email, :password_hash, :role)
        """)

        password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query1, {"username": username}).fetchone()

                if result:
                    return "Username is already taken!"
                
                result=conn.execute(query2, {"email": email}).fetchone()

                if result:
                    return  "Email is already taken!"
                
                conn.execute(query3, {"username": username,
                                      "first_name": first_name,
                                      "last_name": last_name,
                                      "email": email,
                                      "password_hash": password_hash,
                                      "role": role,
                                      })
                conn.commit()

                return True
            
        except Exception as e:
            print(f"Error logging user: {e}")
            raise

    def check_username(self, username):
        query = text("""
            SELECT username FROM users_tbl
            WHERE username = :username
        """)

        
        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"username": username}).fetchone()

                if result:
                    return "Username is already taken!"
                
        
                return True
            
        except Exception as e:
            print(f"Error logging user: {e}")
            raise

    def check_email(self, email):

        query = text("""
            SELECT email FROM users_tbl
            WHERE email = :email
        """)
        
        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"email": email}).fetchone()

                if result:
                    return  "Email is already taken!"
                
                return True
            
        except Exception as e:
            print(f"Error logging user: {e}")
            raise

    def update_user(self, user_id , updater, **fields_to_update):
        if not fields_to_update:
            print("No fields to update.")
            return
        
        set_clauses = [f"{key} = :{key}" for key in fields_to_update]
        fields_to_update["user_id"] = user_id 

        if 'password_hash' in fields_to_update:
            raw_password = fields_to_update['password_hash']
            password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

            fields_to_update['password_hash'] = password_hash

        query = text(f"""
            UPDATE users_tbl
            SET {', '.join(set_clauses)}
            WHERE user_id  = :user_id 
        """)

        try:
            with self.engine.connect() as conn:
                conn.execute(query, fields_to_update)
                conn.commit()
        except Exception as e:
            print(f"Error updating user: {e}")
            raise DatabaseError(e)


    
    '''#creatte 1 update statement- updateable by admin
    def update_user(self, user_id, first_name, last_name, email, enabled, password, role): #email???
        fields = []
        params = {"user_id": user_id}

        if first_name is not "":
            fields.append("first_name = :first_name")
            params["first_name"] = first_name
        if last_name is not "":
            fields.append("last_name = :last_name")
            params["last_name"] = last_name
        if email is not "":
            fields.append("email = :email")
            params["email"] = email
        if enabled is not "":
            fields.append("enabled = :enabled")
            params["enabled"] = enabled
        if password is not "":
            password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) # validate password outside sql func
            fields.append("password_hash = :password_hash")
            params["password_hash"] = password_hash
        if role is not "":
            fields.append("role = :role")
            params["role"] = role
        if not fields:
            print("No fields to update.")
            return

        query = text(f"""
            UPDATE users_tbl SET {', '.join(fields)} WHERE user_id = :user_id
        """)

        try:
            with self.engine.connect() as conn:
                conn.execute(query, params)
                conn.commit()
        except Exception as e:
            print(f"Error updating user: {e}")
            raise

    # updateable by system
    def update_last_login(self,user_id):
        query = text("""
            UPDATE users_tbl SET last_login= NOW()
            WHERE user_id= :user_id
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(query, {
                    "user_id": user_id
                })
                conn.commit()
        except Exception as e:
            print(f"Error updating last login: {e}")
            raise

    def update_n_password_failures(self):
        pass
    def update_locked_until(self):
        pass'''
    

    # create get users by emal name and lastname username etc


    def delete_user(self, user_id):
        query1=text("""
            SELECT role FROM users_tbl
            WHERE user_id= :user_id
        """)

        query2=text("""
            DELETE FROM users_tbl
            WHERE user_id= :user_id
        """)

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query1, {"user_id": user_id}).fetchone() 

                if result and result.role == "A":
                        return False
                
                result=conn.execute(query2, {"user_id": user_id})
                conn.commit()

                return True

        except Exception as e:
            print(f"Error deleting user: {e}")
            raise

    

    def get_user_by_username(self, input_username):
        query=text("""
            SELECT * FROM users_tbl
            WHERE username= :username
        """)


        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"username": input_username}).mappings().fetchone()
                #print(result[0])

                if result:
                    user=User(
                        result["user_id"],
                        result["username"],
                        result["first_name"],
                        result["last_name"],
                        result["email"],
                        result["enabled"],
                      
                        result["password_hash"],
                    
                        result["role"],
                        result["data_created"],
                        result["updated_at"])
                
                    return user 
                else: 
                    return None
            
        except Exception as e:
            print(f"Error getting username and password: {e}")
            raise DatabaseError(e)
        
    def get_user_by_id(self, input_user_id):
        query=text("""
            SELECT * FROM users_tbl
            WHERE user_id= :user_id
        """)


        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"user_id": input_user_id}).mappings().fetchone()
                #print(result[0])

                if result:
                    user=User(
                        result["user_id"],
                        result["username"],
                        result["first_name"],
                        result["last_name"],
                        result["email"],
                        result["enabled"],
                      
                        result["password_hash"],
                        
                        result["role"],
                        result["data_created"],
                        result["updated_at"])
                
                    return user 
                else: 
                    return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            raise DatabaseError(e)
    
    def get_users(self, offset=0, limit=10):
        params = {"limit": limit, "offset": offset}

        count_query = text(f"""
            SELECT COUNT(*) FROM users_tbl
        """)

        query=text("""
            SELECT * FROM users_tbl LIMIT :limit OFFSET :offset
        """)


        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                #print(result[0])
                users = []

                if result:
                    for row in result:
                        user=User(
                            row["user_id"],
                            row["username"],
                            row["first_name"],
                            row["last_name"],
                            row["email"],
                            row["enabled"],
                          
                            row["password_hash"],
                        
                            row["role"],
                            row["data_created"],
                            row["updated_at"])
                        users.append(user)
                    
                    return users, total_result
                else: 
                    return users, 0
            
        except Exception as e:
            print(f"Error getting users: {e}")
            raise DatabaseError(e)
        

    def search_users(self, search_input, offset=0, limit=10 ):
        search_input = f"{search_input}%"
        params = {"search": search_input, "limit": limit, "offset": offset}

        count_query = text(f"""
            SELECT COUNT(*) FROM users_tbl 
            WHERE 
                username LIKE :search
                OR first_name LIKE :search
                OR last_name LIKE :search
                OR email LIKE :search
                OR enabled LIKE :search
                OR
                CASE 
                    WHEN enabled = 1 THEN 'Enabled'
                    WHEN enabled = 2 THEN 'Disabled'
                    ELSE ''
                END LIKE :search
                OR role LIKE :search
                OR
                CASE 
                    WHEN role = 'A' THEN 'Admin'
                    WHEN role = 'C' THEN 'Collaborator'
                    ELSE ''
                END LIKE :search
                OR CAST(data_created AS CHAR) LIKE :search

        """)

        query=text("""
            SELECT * FROM users_tbl 
            WHERE 
                username LIKE :search
                OR first_name LIKE :search
                OR last_name LIKE :search
                OR email LIKE :search
                OR enabled LIKE :search
                OR
                CASE 
                    WHEN enabled = 1 THEN 'Enabled'
                    WHEN enabled = 2 THEN 'Disabled'
                    ELSE ''
                END LIKE :search
                OR role LIKE :search
                OR
                CASE 
                    WHEN role = 'A' THEN 'Admin'
                    WHEN role = 'C' THEN 'Collaborator'
                    ELSE ''
                END LIKE :search
                OR CAST(data_created AS CHAR) LIKE :search
            LIMIT :limit OFFSET :offset
        """)    


        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query, params).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                #print(result[0])
                users = []

                if result:
                    for row in result:
                        user=User(
                            row["user_id"],
                            row["username"],
                            row["first_name"],
                            row["last_name"],
                            row["email"],
                            row["enabled"],
                           
                            row["password_hash"],
                         
                            row["role"],
                            row["data_created"],
                            row["updated_at"])
                        users.append(user)
                    
                    return users, total_result
                else: 
                    return users, 0
            
        except Exception as e:
            print(f"Error searching user: {e}")
            raise DatabaseError(e)    
        
    def search_users_with_filter(self, search_input, filter, offset=0, limit=10):

        search_input = f"{search_input}%"

        allowed_filters = {
            "1": "username",
            "2": "first_name",
            "3": "email",
            "4": "data_created"
        }

        allowed_directions = {
            "A": "ASC",
            "D": "DESC"
        }

        filter_input = "ORDER BY username ASC"
        if filter[0] in allowed_filters and filter[1] in allowed_directions:
            filter_input=f"ORDER BY {allowed_filters[filter[0]]} {allowed_directions[filter[1]]}"

        params = {"limit": limit, "offset": offset}

        where_input=""
        if (search_input!=""):
            where_input="WHERE username LIKE :username"
            params["username"] = search_input

        count_query = text(f"""
            SELECT COUNT(*) FROM users_tbl {where_input}
        """)

        query=text(f"""
            SELECT * FROM users_tbl {where_input} {filter_input} LIMIT :limit OFFSET :offset
        """)


        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query, params).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                #print(result[0])
                users = []

                if result:
                    for row in result:
                        user=User(
                            row["user_id"],
                            row["username"],
                            row["first_name"],
                            row["last_name"],
                            row["email"],
                            row["enabled"],
                          
                            row["password_hash"],
                           
                            row["role"],
                            row["data_created"],
                            row["updated_at"])
                        users.append(user)
                    
                    return users, total_result
                else: 
                    return users, 0
            
        except Exception as e:
            print(f"Error searching user: {e}")
            raise DatabaseError(e)    
          
          
























            #DELETE
    def get_username_and_password(self, input_username):
        query=text("""
            SELECT username, password_hash FROM users_tbl
            WHERE username= :username
        """)

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"username": input_username}).fetchone()
                return (result.username, result.password_hash) if result else (None, None)
            
        except Exception as e:
            print(f"Error getting username and password: {e}")
            raise
        
    def get_enabled(self, user_id):
        query=text("""
            SELECT enabled FROM users_tbl
            WHERE user_id= :user_id
        """)

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"user_id": user_id}).fetchone()
                return result.enabled if result else None
            
        except Exception as e:
            print(f"Error getting  enabled status: {e}")
            raise

             #DELETE
    def get_role(self, user_id):
        query=text("""
            SELECT role FROM users_tbl
            WHERE user_id= :user_id
        """)

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"user_id": user_id}).fetchone()
                return result.role if result else None
            
        except Exception as e:
            print(f"Error getting role: {e}")
            raise

    def get_password_failures(self,user_id):
        query=text("""
            SELECT n_password_failures FROM users_tbl
            WHERE user_id= :user_id
        """)

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"user_id": user_id}).fetchone()
                return result.n_password_failures if result else None
            
        except Exception as e:
            print(f"Error getting number of failures: {e}")
            raise

    def get_locked_until(self,user_id):
        query=text("""
            SELECT locked_until FROM users_tbl
            WHERE user_id= :user_id
        """)

        try:
            with self.engine.connect() as conn:
                result=conn.execute(query, {"user_id": user_id}).fetchone()
                return result.locked_until if result else None
            
        except Exception as e:
            print(f"Error getting locked until: {e}")
            raise

         

  








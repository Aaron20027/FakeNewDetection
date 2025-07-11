#from model.extensions import engine
from sqlalchemy import text
from model.Audit import Audit

from flask import request
from model.Utils import DatabaseError


class AuditLogsTable():
    def __init__(self, db_connection):
        self.engine = db_connection

    def add_audit_log(self, performed_by, action):
        query = text("""
            INSERT INTO audit_logs_tbl (performed_by, action, user_agent, ip_address)
            VALUES (:performed_by, :action, :user_agent, :ip_address)
        """)


        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip_address = request.remote_addr

        user_agent = request.headers.get('User-Agent')

        try:
            with self.engine.connect() as conn:
                conn.execute(query, {
                    "performed_by": performed_by,
                    "action": action,
                    "user_agent": user_agent,
                    "ip_address": ip_address
                })
                conn.commit()
        except Exception as e:
            print(f"Error logging audit: {e}")
            raise DatabaseError(e)
        


    def get_audits(self, offset=0, limit=10):
        params = {"limit": limit, "offset": offset}

        count_query = text(f"""
            SELECT COUNT(*) FROM audit_logs_tbl
        """)

        query=text("""
            SELECT * FROM audit_logs_tbl ORDER BY timestamp DESC LIMIT :limit OFFSET :offset
        """)

        query=text("""
            SELECT Audit.audit_log_id, User.username AS performed_by ,Audit.action , Audit.user_agent ,Audit.ip_address, Audit.timestamp
                   FROM audit_logs_tbl AS Audit 
                   INNER JOIN users_tbl AS User ON Audit.performed_by=User.user_id
                   ORDER BY timestamp DESC 
                   LIMIT :limit OFFSET :offset
        """)



        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                #print(result[0])
                audits = []

                if result:
                    for row in result:
                        audit=Audit(
                            row["audit_log_id"],
                            row["performed_by"],
                            row["action"],
                            row["user_agent"],
                            row["ip_address"],
                            row["timestamp"]
                            )
                        audits.append(audit)
                    
                    return audits, total_result
                else: 
                    return audits, 0
            
        except Exception as e:
            print(f"Error getting audits: {e}")
            raise DatabaseError(e)
        
    def search_audits(self,user_input, offset=0, limit=10):
        search_term = f"%{user_input.strip()}%"  # sanitize user input
        params = {
            "search": search_term,
            "limit": limit,
            "offset": offset
        }

        count_query = text(f"""
            SELECT COUNT(*)
            FROM audit_logs_tbl AS aud 
            LEFT JOIN users_tbl AS usr ON aud.performed_by=usr.user_id
            WHERE
                username LIKE :search
                OR action LIKE :search
                OR user_agent LIKE :search
                OR ip_address LIKE :search
                OR CAST(timestamp AS CHAR) LIKE :search
        """)

        query=text("""
            SELECT * FROM audit_logs_tbl ORDER BY timestamp DESC LIMIT :limit OFFSET :offset
        """)

        query=text("""
            SELECT *, User.username AS performed_by_name 
                   FROM audit_logs_tbl AS Audit 
                   INNER JOIN users_tbl AS User ON Audit.performed_by=User.user_id
                   WHERE
                        username LIKE :search
                        OR action LIKE :search
                        OR user_agent LIKE :search
                        OR ip_address LIKE :search
                        OR CAST(timestamp AS CHAR) LIKE :search
                   ORDER BY timestamp DESC 
                   LIMIT :limit OFFSET :offset
        """)



        try:
            with self.engine.connect() as conn:
                total_result = conn.execute(count_query,params).scalar()
                result=conn.execute(query, params).mappings().fetchall()
                #print(result[0])
                audits = []

                if result:
                    for row in result:
                        audit=Audit(
                            row["audit_log_id"],
                            row["performed_by_name"],
                            row["action"],
                            row["user_agent"],
                            row["ip_address"],
                            row["timestamp"]
                            )
                        audits.append(audit)
                    
                    return audits, total_result
                else: 
                    return audits, 0
            
        except Exception as e:
            print(f"Error getting audits: {e}")
            raise DatabaseError(e)
        






from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import create_engine

from dotenv import load_dotenv
import os

load_dotenv()

mail = Mail() 

limiter = Limiter(key_func=get_remote_address)

DB_URL = os.getenv("DATABASE_URI")
#hide in env
engine = create_engine(
    DB_URL,
    pool_size=10,         
    max_overflow=20,      
    pool_timeout=30,       
    pool_recycle=1800      
)


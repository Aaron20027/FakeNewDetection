from model.Database.UsersTBL import UserTable
from flask import flash
import bcrypt

class Login():
    def __init__(self, username, password,engine):
        self.username=username
        self.password=password
        self.user=None
        self.engine=engine

    def validate_credentials(self):
        userTBL=UserTable(self.engine)


        self.user=userTBL.get_user_by_username(self.username)

        if not self.user: 
            #flash("User doesn't exist.", 'danger')
            return False 
        
        if bcrypt.checkpw(self.password.encode('utf-8'), self.user.password_hash.encode('utf-8')):
            return True
        else:
            #flash("Invalid credentials.", 'danger')
            return False 
        
    def get_user(self):
        return self.user
    

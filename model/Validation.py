import re
from model.Database.UsersTBL import UserTable
from model.extensions import mail, limiter, engine
from urllib.parse import urlparse

class Validation():

    #doesnt already exist
    #maximum of 5- 64 characters.
    #no space
    #lowercase letters (a–z), digits (0–9), underscores (_), and periods (.)
    #reserved word : admin, root, or system 
    #immutable
    def validate_username(self, input):
        #check if already exists

        result = self.check_blank("Username", input)
        if result is not True:
            return result
        
        userTable=UserTable(engine)
        result=userTable.check_username(input)
        if result is not True:
            return result

        result = self.check_length("Username", input, 5, 64)
        if result is not True:
            return result
        
        result = self.check_characters("Username", input, r'^[a-zA-Z0-9_.]+$')
        if result is not True:
            return result
        
        result = self.check_reserved("Username", input)
        if result is not True:
            return result
        
        result = self.check_start_and_end("Username", input, char_list=[".","_"])
        if result is not True:
            return result
        
        return True
       

    # must be between 2-50
    #Letters (a-z, A-Z) hyphen -, apostrophe ', and space internationl
    # not reserved word 
    #auto title the names   
    #No leading/trailing spaces, hyphens, or apostrophes
    #updatteable
    def validate_firstname(self,input):

        result = self.check_blank("Firstname", input)
        if result is not True:
            return result
        
        result = self.check_length("Firstname", input, 2, 50)
        if result is not True:
            return result
        
        result = self.check_characters("Firstname", input, r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")
        if result is not True:
            return result
        
        result = self.check_reserved("Firstname", input)
        if result is not True:
            return result
        
        result = self.check_start_and_end("Firstname", input, char_list=["-","'"," "])
        if result is not True:
            return result
    
        return True
    
    def validate_lastname(self,input):
        result = self.check_blank("Lastname", input)
        if result is not True:
            return result
        
        result = self.check_length("Lastname", input, 2, 50)
        if result is not True:
            return result
        
        result = self.check_characters("Lastname", input, r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")
        if result is not True:
            return result
        
        result = self.check_reserved("Lastname", input)
        if result is not True:
            return result
        
        result = self.check_start_and_end("Lastname", input, char_list=["-","'"," "])
        if result is not True:
            return result
        
        return True
       
       
    # 8-254 characters
    #valid email regex
    #only one @
    #uniques
    #leading and trailinng symbols [not done]
    #updateable
    def validate_email(self,input):
        #check unique

        result = self.check_blank("Email", input)
        if result is not True:
            return result
        
        userTable=UserTable(engine)
        result=userTable.check_email(input)
        if result is not True:
            return result

        
        result = self.check_length("Email", input, 8, 254)
        if result is not True:
            return result
        
        result = self.check_characters("Email", input, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if result is not True:
            return result
        
        result = self.check_reserved("Email", input)
        if result is not True:
            return result
        
        """result = self.check_start_and_end("Email", input, char_list=[".","_"])
        if result is not True:
            return result
        """

        return True
    
    #validate password
    #Must be 12 to 64 characters long
    #Must include at least one uppercase letter (A–Z
    #Must include at least one lowercase letter (a–z)
    #Must include at least one digit (0–9)
    #Must include at least one special character (e.g., !, $, #, %)
    def validate_password(self,input):
        result = self.check_blank("Password", input)
        if result is not True:
            return result
        
        result = self.check_length("Password", input, 8, 64)
        if result is not True:
            return result
        
        result = self.check_characters_count("Password", input)
        if result is not True:
            return result
        
        result = self.check_reserved("Password", input)
        if result is not True:
            return result
        

        return True
    
    def validate_confirm_password(self,password,input):

        result = self.check_same_pass("Confirm Password", password, input)
        if result is not True:
            return result

        return True
    
    
 
    
    #either a or c
    def validate_role(self,input):
        result = self.check_radio("Role", input, ["A","C"], "admin or collaborator")
        if result is not True:
            return result
        
        return True
    

    # must be between 10-150
    # not blank
    def validate_title(self,input):

        result = self.check_blank("Title", input)
        if result is not True:
            return result
        
        result = self.check_length("Title", input, 10, 150)
        if result is not True:
            return result
   
    
        return True
    
    # must be between 10-150
    # not blank
    def validate_content(self,input):

        result = self.check_blank("Content", input)
        if result is not True:
            return result
        
        result = self.check_length("Content", input, 40)
        if result is not True:
            return result
   
        return True


    def is_valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    

    #either r or f
    def validate_label(self,input):
        result = self.check_radio("Label", input, [1,0], "real or fake")
        if result is not True:
            return result
        
        return True
    
    def validate_label_radio(self,input):
        result = self.check_radio("Label", input, ["F","R"], "real or fake")
        if result is not True:
            return result
        
        return True
    
    def validate_enabled(self,input): #change
        result = self.check_radio("Label", input, ["1","0"], "enabled or disabled")
        if result is not True:
            return result
        
        return True
    
   
    def check_taken():
        pass

    
    def check_blank(self,field,input):
        if not (input.strip()!=""):
            return f"{field} must not be blank!"
        return True
    

    def check_length(self,field,input, min, max=None):
        if len(input) < min:
            return f"{field} must be at least {min} characters long!"
        if max is not None and len(input) > max:
            return f"{field} must be no more than {max} characters long!"
        return True
    
    def check_characters(self,field,input, pattern):
        patterns_info = {
            r'^[a-zA-Z0-9_.]+$': "must contain letters, numbers, underscores (_), and periods (.)",
            r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$": "must contain letters, spaces, hyphens (-), and apostrophes (')",
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$': "must be a valid email format"}

        if not(bool(re.fullmatch(pattern, input))):
             return f"{field} {patterns_info[pattern]}!"
        
        return True
    

    def check_characters_count(self,field,input):
        if not(bool(re.search(r'[a-z]', input))):
            return f"{field}  must contain atleast one lowercase character!"
        if not(bool(re.search(r'[A-Z]', input))):
            return f"{field}  must contain atleast one uppercase character!"
        if not(bool(re.search(r'\d', input))):
            return f"{field}  must contain atleast one digit!"
        if not (bool(re.search(r'[@_!#$%^&*()<>?/\|}{~:]', input))):
            return f"{field} must contain atleast one special character!"

        return True
    
    def check_same_pass(self,field, password, input):
        if not(password==input):
            return f"{field} must match password!"
        
        return True
    
    
    def check_reserved(self,field,input):
        reserved_words=["admin", "root", "system", "superuser", "support", "help", "contact",
                        "system", "null", "undefined", "none", "owner",
                        "login", "logout", "signin", "signup", "register", "user",
                        "username", "profile", "account", "settings", "config",
                        "dashboard", "console", "status", "update", "delete",
                        "api", "internal", "backend", "server", "client", "about", "home"]
        
        lower_input = input.lower()

        for word in reserved_words:
            if word in lower_input:
                return f"{field} cannot contain reserved words!"
            
        return True
    
    def check_start_and_end(self,field, input, char_list):
        """char_list=[".","_"]
        char_list=["-","'"," "]"""


        if input[0] in char_list or input[-1] in char_list:
            return f"{field} cannot begin or end with special characters!"
        
        return True
        

    def check_radio(self,field, input, char_list, text):
        if not(input in char_list or input in char_list):
            return f"{field} must be either {text}!"
        
        return True


    def check_password_match(self,password, confirm_password):
        if password != confirm_password:
            return "Passwords do not match!"
        return True





       

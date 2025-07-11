
class User():
    def __init__(self, user_id, username, first_name, last_name, email, enabled, password_hash, 
                 role, data_created, updated_at
 ):
        self.user_id=user_id
        self.username=username
        self.first_name=first_name
        self.last_name=last_name
        self.email=email
        self.enabled=enabled
      
        self.password_hash=password_hash
     
        self.role=role
        self.data_created=data_created
        self.updated_at=updated_at

    def to_dict(self):
      
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name':self.first_name,
            'last_name':self.last_name,
            'email':self.email,
            'enabled':self.enabled,
      
            'password_hash':self.password_hash,
       
            'role':self.role,
            'data_created':self.data_created.isoformat(),
            'updated_at':self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["user_id"],
                        data["username"],
                        data["first_name"],
                        data["last_name"],
                        data["email"],
                        data["enabled"],
                      
                        data["password_hash"],
                  
                        data["role"],
                        data["data_created"],
                        data["updated_at"])

import pymongo
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mongo = myclient["blogdb"]

class UserModel:
    def __init__(self,name) -> str:
        self.username = name
    
    def save_to_db(self): #在mongodb中暂时无用
        mongo.users.insert_one(self)
    
    def check_user_exist(self):
        return mongo.users.count_documents({
            "username" : self.username
        })
    
    def return_all():
        return {'users':list(mongo.users.find({},{'username':1,'_id':0}))}

    def find_by_username(self):
        return mongo.users.find_one({"username" : self.username})

class RevokedTokenModel:

    def __init__(self,jti) -> None:
        self.jti = jti

    def add(self):
        new_jti = {
            'revoked_tokens':self.jti
        }
        mongo.tokens.insert_one(new_jti)

    def is_jti_blacklisted(self):
        if mongo.tokens.count_documents({'revoked_tokens' : self.jti}) == 0:
            return False
        else:
            return True

# print(list(mongo.users.find({},{'username':1,'_id':0})))
# print(list(mongo.articles.find())[0])

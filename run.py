from flask import Flask
from flask_restful import Api
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from models import RevokedTokenModel

app = Flask(__name__)
api = Api(app)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/blogdb'  # MongoDB连接URI
mongo = PyMongo(app)
app.config['SECRET_KEY'] = '123456'
app.config['JWT_SECRET_KEY'] = '123456'
jwt = JWTManager(app)
app.config['JWT_BLOCKLIST_TOKEN_CHECKS'] = ['access','refresh']

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header,decrypted_token):
    jti = RevokedTokenModel(decrypted_token['jti'])
    return jti.is_jti_blacklisted()

import views, models, resources

api.add_resource(resources.UserRegistration, '/registration')
api.add_resource(resources.UserLogin, '/login')
api.add_resource(resources.UserLogoutAccess, '/logout/access')
api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.TokenRefresh, '/token/refresh')
api.add_resource(resources.AllUsers, '/users')
api.add_resource(resources.SecretResource, '/secret')
api.add_resource(resources.ArticlesList,'/api/articles')
api.add_resource(resources.TagsUpdate,'/api/addtags')
api.add_resource(resources.CommentUpdate,'/api/comment')


from flask_restful import Resource
from flask_restful import Resource, reqparse
from models import RevokedTokenModel, UserModel
from run import mongo
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from flask import jsonify, request
from bson import ObjectId
import json
import datetime

# parser = reqparse.RequestParser()
# parser.add_argument('username', help = 'This field cannot be blank', required = True)


class UserRegistration(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "username", help="This field cannot be blank", required=True
        )

        data = parser.parse_args()
        new_user = UserModel(username=data["username"])  ## 还没有做key-value映射，直接存对象报500
        if mongo.db.users.count_documents({"username": data["username"]}) != 0:
            return {"message": "User already exist!"}, 500

        else:
            try:
                # new_user.save_to_db()
                mongo.db.users.insert_one({"username": data["username"]})
                access_token = create_access_token(identity=data["username"])
                refresh_token = create_refresh_token(identity=data["username"])
                return {
                    "message": "User {} was created".format(data["username"]),
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
            except:
                return {"message": "Something wrong"}, 500


class UserLogin(Resource):
    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument(
            "username", help="This field cannot be blank", required=True
        )
        data = parser.parse_args()
        print(data)
        new_user = UserModel(data["username"])
        check = new_user.check_user_exist()
        if check != 0:
            current_user = new_user
            access_token = create_access_token(identity=data["username"])
            refresh_token = create_refresh_token(identity=data["username"])
            return {
                "message": "Login as {}".format(current_user.username),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        else:
            return {"message": "User {} doesn't exist!".format(data["username"])}


class UserLogoutAccess(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        try:
            revoked_token = RevokedTokenModel(jti)
            revoked_token.add()
            return {"message": "Access token has been revoked."}
        except:
            return {"message": "Something wrong."}


class UserLogoutRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        jti = get_jwt()["jti"]
        try:
            revoked_token = RevokedTokenModel(jti)
            revoked_token.add()
            return {"message": "Refresh token has been revoked."}
        except:
            return {"message": "Something wrong."}, 500


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {"access_token": access_token}


class AllUsers(Resource):
    def get(self):
        return UserModel.return_all()

    def delete(self):
        return {"message": "Delete all users"}


class SecretResource(Resource):
    @jwt_required()
    def get(self):
        return jsonify({"answer": 42})


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


# 添加jwt认证，添加文章功能，文章json附带作者id、发布时间、标签功能，初次启动查询数据库所有的文章，
class ArticlesList(Resource):
    # def put(self):
    #     articles = parser.parse_args()
    #     result = mongo.db.articles.insert_one(articles) #添加进数据库
    #     return {result.inserted_id : articles}

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument("title", help="This field cannot be blank", required=True)
        parser.add_argument("content", help="This field cannot be blank", required=True)
        parser.add_argument("tags", type=list, location="json")

        data = parser.parse_args()
        data.datetime = datetime.datetime.now()
        # print(type(data["comments"]))
        result = mongo.db.articles.insert_one(data)
        return {"message": "Article {id} Posted!".format(id=result.inserted_id)}

    # @jwt_required()
    def get(self):
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        article_id = request.args.get("article_id")
        tags = request.args.get("tags")

        if article_id != None:
            try:
                all_article = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
                all_comment = mongo.db.comments.find(
                    {"blog_id": ObjectId(article_id)}
                )

                all_article["comment"] = []
                for x in all_comment:
                    all_article["comment"].append(
                        {
                            "author": x["author"], "content": x["comment"]
                        }
                    )

                post = json.loads(json.dumps(all_article, cls=JSONEncoder))
                return jsonify(post)
            except:
                return ({"message": "Articles not found!"},)

        elif tags != None:
            try:
                tags = tags.split(",")
                posts = list(mongo.db.articles.find({"tags": {"$all": tags}}))

                total_post = len(posts)
                total_pages = (total_post + per_page - 1) // per_page
                start_index = (page - 1) * per_page
                end_index = start_index + per_page
                final_post = json.loads(
                    json.dumps(posts[start_index:end_index], cls=JSONEncoder)
                )

                response = {
                    "articles": final_post,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "total_post": total_post,
                }

                return jsonify(response)
            except:
                return {"message": "Tags not found!"}
        else:
            all_posts_1 = list(mongo.db.articles.find())
            total_post = len(all_posts_1)
            total_pages = (total_post + per_page - 1) // per_page

            start_index = (page - 1) * per_page
            end_index = start_index + per_page

            posts = json.loads(
                json.dumps(all_posts_1[start_index:end_index], cls=JSONEncoder)
            )

            response = {
                "articles": posts,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_post": total_post,
            }

            return jsonify(response)


class TagsUpdate(Resource):
    def put(self):
        parser = reqparse.RequestParser()

        parser.add_argument("tags", help="This field cannot be blank", required=True)
        article_id = request.args.get("article_id")
        tags = parser.parse_args()["tags"]
        # 判断标签是否存在
        result = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
        judge = 0
        for x in result["tags"]:
            if x == tags:
                judge += 1
            else:
                continue
        if judge >= 1:
            return {"Message": "Tags already existed!"}
        else:
            mongo.db.articles.update_one(
                {"_id": ObjectId(article_id)}, {"$addToSet": {"tags": tags}}
            )
            return {"Message": "Tags updated!"}

    def delete(self):
        parser = reqparse.RequestParser()

        parser.add_argument("tags", help="This field cannot be blank", required=True)
        article_id = request.args.get("article_id")
        tags = parser.parse_args()["tags"]
        result = mongo.db.articles.update_one(
            {"_id": ObjectId(article_id)}, {"$pull": {"tags": tags}}
        )
        return {"Message": "Tags {} removed!".format(tags)}


class CommentUpdate(Resource):
    @jwt_required()
    def put(self):
        parser = reqparse.RequestParser()

        name = get_jwt()["sub"]  # 应该改成用户唯一识别id
        parser.add_argument("comment", help="This field cannot be blank", required=True)
        article_id = request.args.get("article_id")
        comment = parser.parse_args()["comment"]
        result = mongo.db.comments.insert_one(
            {"blog_id": ObjectId(article_id), "author": name, "comment": comment}
        )
        return {"Message": "Comment updated!"}

    @jwt_required()
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "comment_id", help="This field cannot be blank", required=True
        )
        comment_id = parser.parse_args()["comment_id"]
        result = mongo.db.comments.delete_one({"_id": ObjectId(comment_id)})
        return {"Message": "Comment removed!"}


# 数据可视化，统计博客数量，词云等
# 单元测试，使用测试框架如unittest或pytest来进行单元测试或者集成测试

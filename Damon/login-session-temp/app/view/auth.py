from flask import Flask, render_template, request, session, Blueprint, make_response
from flask_restful import Api, Resource, reqparse

from marshmallow import ValidationError

from ..model.user import UserModel, UserSchema
from .. import db
from .abort_msg import abort_msg

auth = Blueprint('auth', __name__)
api = Api(auth)

users_schema = UserSchema()


class Signup(Resource):
    def post(self):
        try:
            # 資料驗證
            # 接收前端 Form 表單傳過來的使用者帳號和密碼，並且使用 Flask 擴充套件 Marshmallow 的 users_schema.load 語法進行資料驗證
            user_data = users_schema.load(request.form, partial=True)
            # 註冊
            # 驗證過後的帳號密碼放入 UserModel(user_data) ，實例化新的使用者後存入 db new_user.save_db() 和設定使用者的 session new_user.save_session()。
            new_user = UserModel(user_data) # 實例化新使用者
            new_user.save_db() # 將新使用者存入 db
            new_user.save_session() # 設定新使用者的 session
            # 沒有發生錯誤，則結束並返回註冊成功 {'msg': 'registration success'} 訊息。
            return {'msg': 'registration success'}, 200
        # 驗證錯誤 (密碼少於 6 碼、或缺少帳號/密碼欄位) 則會在 except ValidationError as error: 觸發。
        except ValidationError as error:
            return {'errors': error.messages}, 400
        # 是其他錯誤訊息則會在這邊觸發 except Exception as e:，並且將錯誤訊息清理過後回覆給前端 {'errors': abort_msg(e)}
        except Exception as e:
            return {'errors': abort_msg(e)}, 500

    def get(self):
        return make_response(render_template('signup.html'))


class Login(Resource):
    def post(self):
        try:
            # 資料驗證
            user_data = users_schema.load(request.form)
            name = user_data['name']
            password = user_data['password']

            # 登入
            query = UserModel.get_user(name)
            if query != None and query.verify_password(password):
                query.save_session()
                return {'msg': 'ok'}, 200
            else:
                return {'errors': 'incorrect username or password'}, 400

        except ValidationError as error:
            return {'errors': error.messages}, 400

        except Exception as e:
            return {'errors': abort_msg(e)}, 500

    def get(self):
        return make_response(render_template('login.html'))


class Logout(Resource):
    def get(self):
        UserModel.remove_session()
        return {'msg': 'logout'}, 200


api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')

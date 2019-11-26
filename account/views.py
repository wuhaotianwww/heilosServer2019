import json
from django.http import HttpResponse
from django.contrib.auth.models import User
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

SECRET_KEY = "548D859ADA8B084E76730CCEFA052EE1"


def login(request):
    data = json.loads(request.body)
    try:
        user = User.objects.get(username=data['username'])
        if user.check_password(data['password']):
            res = {
                'code': 1,
                'message': '登录成功',
                'data': {
                    'user': data['username'],
                    'token': jwt.encode({
                        'exp': datetime.utcnow() + timedelta(days=1),
                        'iat': datetime.utcnow(),
                        'data': {
                            'username': data['username']
                        },
                    }, settings.SECRET_KEY, algorithm='HS256').decode('utf-8'),
                },
            }
            response = HttpResponse(json.dumps(res), content_type='application/json')
            # if data['autologin']:
            #     is_login = make_password(
            #         data['username']+data['password'], None, 'pbkdf2_sha256')
            #     print(is_login)
            #     response.set_cookie('isLogin', is_login +
            #                         '&' + data['username'], max_age=3600*2)
            return response
        else:
            return HttpResponse(json.dumps({'code': -1,
                                            'message': '密码错误', }), content_type='application/json')
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'code': -1,
                                        'message': '不存在该用户', }), content_type='application/json')


def auto_login(request):
    auth = request.META.get('HTTP_AUTHORIZATION').split()
    token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
    username = token.get('data').get('username')
    res = {
        'code': 1,
        'message': '登录成功',
        'data': {'user': username},
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


def register(request):
    data = json.loads(request.body)
    try:
        User.objects.get(username=data['username'])
        res = {
            'code': -1,
            'message': '用户已存在'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except User.DoesNotExist:
        User.objects.create_user(
            username=data['username'], password=data['password'], email=data['mail'])
        res = {
            'code': '1',
            'message': '注册成功'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')

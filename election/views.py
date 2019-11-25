import json
from django.http import HttpResponse
from django.contrib.auth.models import User
from election import models
import jwt
from django.conf import settings
from .utils.SendEmail import EmailSender
import parameters


# ################################创建、获取、修改、删除选举##################################
def create_election(request):
    """
    创建新选举：
    1.解析提交数据，将本次选举信息记录到数据库中。
    """
    data = json.loads(request.body)
    auth = request.META.get('HTTP_AUTHORIZATION').split()
    token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
    username = token.get('data').get('username')
    data['author'] = User.objects.get(username=username)
    data['status'] = '0'
    # voters = data['voters']
    # if voters == 'everyone':
    #     users = User.objects.all()
    #     username_list = []
    #     for user in users:
    #         username_list.append(user.username)
    #     print(username_list)
    #     # data['voters'] = ','.join(username_list)
    #     data['isPrivate'] = False
    # elif voters == 'private':
    #     # data['voters'] = ''
    #     data['isPrivate'] = True
    temp = {'author': data['author'], 'status': data['status'], 'name': data['name'], 'shortName': data['shortName']}
    if models.Elections.objects.create(**temp):
        res = {
            'code': 1,
            'message': '创建成功'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    else:
        res = {
            'code': -1,
            'message': '创建失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


def fetch_elections(request):
    """
    获取用户创建的所有选举：
    1.按照用户名从数据库中过滤出该用户创建的所有选票，返回给前端。
    """
    if parameters.flag:
        print("停止选举！")
    else:
        print("开始选举！")
    auth = request.META.get('HTTP_AUTHORIZATION').split()
    token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
    username = token.get('data').get('username')
    author = User.objects.get(username=username)
    try:
        elections = models.Elections.objects.filter(author=author)
        elections_list = []
        for election in elections:
            election_dict = election.to_dict()
            elections_list.append(election_dict)
        res = {
            'code': 1,
            'electionList': elections_list,
            'message': '该用户创建的所有投票'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '请求投票列表失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


def update_elections(request):
    parameters.flag = True
    data = json.loads(request.body)
    id = data['id']
    author = data['author']
    try:
        election = models.Elections.objects.get(id=id)
        if election.description != data['description']:
            election.description = data['description']
        if election.name != data['name']:
            election.name = data['name']
        if election.shortName != data['shortName']:
            election.shortName = data['shortName']
        if election.startTime != data['startTime']:
            election.startTime = data['startTime']
        if election.endTime != data['endTime']:
            election.endTime = data['endTime']
        if election.isPrivate != data['isPrivate']:
            print(data['isPrivate'])
            # 原来是False，公开状态那么现在改成保密就要把voters变成‘’
            if data['isPrivate'] == True:
                print('isPrivate == True')
                election.voters = ''
            # 原来是True，保密状态那么现在改成公开就要把voters变成所有用户
            elif data['isPrivate'] == False:
                print('isPrivate == False')
                users = User.objects.all()
                username_list = []
                for user in users:
                    username_list.append(user.username)
                election.voters = ','.join(username_list)
                print(election.voters)
            election.isPrivate = data['isPrivate']
        election.save()
        elections = models.Elections.objects.filter(author=author)
        elections_list = []
        for elect in elections:
            election_dict = elect.to_dict()
            elections_list.append(election_dict)
        return HttpResponse(json.dumps({
            'code': 1,
            'electionList': elections_list,
            'message': '更新用户创建的投票成功'
        }), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '更新投票列表失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
        # Create your views here.


def delete_elections(request):
    data = json.loads(request.body)
    id = data['id']
    author = data['author']
    try:
        election = models.Elections.objects.get(id=id)
        election.status = data['status']
        election.save()
        elections = models.Elections.objects.filter(author=author)
        elections_list = []
        for elect in elections:
            election_dict = elect.to_dict()
            elections_list.append(election_dict)
        return HttpResponse(json.dumps({
            'code': 1,
            'electionList': elections_list,
            'message': '删除用户创建的投票成功'
        }), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '删除投票列表失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


# ################################设置投票人名单，设置选举内容##################################
def fetch_voters(request):
    data = json.loads(request.body)
    user_list = data['userList']
    try:
        voters_list = []
        for username in user_list:
            user = User.objects.get(username=username)
            voter = {
              'username':username,
              'email':user.email,
              'firstname':user.first_name,
              'lastname':user.last_name
            }
            voters_list.append(voter)
        res = {
            'code': 1,
            'message': '获取投票者列表成功',
            'votersList': voters_list
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '获取投票者列表失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
        # Create your views here.


def setting_election_content():
    pass


# ################################开启选票，冻结选票, 恢复选票##################################
def start_voting():
    receivers = ['2480850946@qq.com']
    usernames = ['htwu']
    passwords = ['123456']
    urls = 'http://localhost:3000/user/login'
    emailSender = EmailSender(receivers, usernames, passwords, urls)
    emailSender.send_emails()
    pass


def suspend_voting():
    pass


def restart_voting():
    pass


# ################################返回投票中的加密包，接收最终投票结果##################################
def fetch_vote_functions():
    pass


def collect_votes():
    pass


# ################################相应BBS请求##################################
def response_bbc():
    pass


# ################################生成投票结果##################################
def anonymous_result():
    pass


def real_name_result():
    pass


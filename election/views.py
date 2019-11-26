import json
import os
from django.http import HttpResponse, Http404, FileResponse
from django.contrib.auth.models import User
from .models import Elections, VoterList, TempVoterList
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

    if Elections.from_dict(data, User.objects.get(username=username)):
        # 添加投票人到临时数据库
        temp_election = Elections.objects.get(author=User.objects.get(username=username))[-1]
        for i in range(len(data['voterlist'])):
            temp_voters={}
            temp_voters['voter'] = data['voterlist'][i]
            temp_voters['email'] = data['emaillist'][i]
            temp_voters['election'] = temp_election
            if not TempVoterList.objects.create(**temp_voters):
                TempVoterList.objects.filter(election=temp_election).delete()
                temp_election.delete()
                res = {
                    'code': -1,
                    'message': '创建失败'
                }
                return HttpResponse(json.dumps(res), content_type='application/json')

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
    auth = request.META.get('HTTP_AUTHORIZATION').split()
    token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
    username = token.get('data').get('username')
    author = User.objects.get(username=username)

    try:
        elections = Elections.objects.filter(author=author)
        elections_list = []
        for election in elections:
            election_dict = election.to_dict()
            elections_list.append(election_dict)
        res = {
            'code': 1,
            'data': elections_list,
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
    data = json.loads(request.body)
    id = data['id']
    try:
        election = Elections.objects.get(id=id)
        election.update(data)
        TempVoterList.objects.filter(election=election).delete()
        for i in range(len(data['voterlist'])):
            temp_voters={}
            temp_voters['voter'] = data['voterlist'][i]
            temp_voters['email'] = data['emaillist'][i]
            temp_voters['election'] = election
            TempVoterList.objects.create(**temp_voters)
        return HttpResponse(json.dumps({
            'code': 1,
            'data': Elections.objects.filter(id=id).to_dict(),
            'message': '更新用户创建的投票成功'
        }), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '更新投票列表失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


def delete_elections(request):
    data = json.loads(request.body)
    id = data['electionid']
    status = data['status']
    try:
        election = Elections.objects.get(id=id)
        election.status = 6
        election.save()
        return HttpResponse(json.dumps({
            'code': 1,
            'electionid': id,
            'status': 6,
            'message': '删除用户创建的投票成功'
        }), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '删除投票列表失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


# ################################开启选票，冻结选票, 恢复选票##################################
def start_voting(request):
    """
    启动选票：修改选举状态， 给选举投票者列表中的所有人员创建用户并发送邮件。
    :param request:
    :return:
    """
    data = json.loads(request.body)
    id = data['electionid']
    status = data['status']
    print("是否是第一次启动(0表示是)：", status)
    try:
        election = Elections.objects.get(id=id)
        election.status = 1
        election.save()
    except Exception:
        res = {
            'code': -1,
            'message': '选举启动失败！'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')

    if status == 0:
        try:
            voters = TempVoterList.objects.filter(Elections=election)
            receivers = []
            usernames = []
            passwords = []
            for each in voters:
                usernames.append(each.voter)
                receivers.append(each.email)
                try:
                    User.objects.get(username=each.voter)
                    passwords.append('your own passwords!')
                except User.DoesNotExist:
                    User.objects.create_user(username=each.voter, password='123456', email=each.email)
                    passwords.append('123456')
                VoterList.objects.create(voter=User.objects.get(username=each.voter), email=each.email, elections=election)
            urls = 'http://localhost:3000/user/login'
            emailSender = EmailSender(receivers, usernames, passwords, urls)
            emailSender.send_emails()
        except Exception:
            pass
    res = {
        'code': 1,
        'data': {'electionid': id, 'status': 1},
        'message': '选举启动成功！'
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


def suspend_voting(request):
    """
    冻结选举：修改选举状态
    :return:
    """
    data = json.loads(request.body)
    id = data['electionid']
    try:
        election = Elections.objects.get(id=id)
        election.status = 2
        election.save()
    except Exception:
        pass
    res = {
        'code': 1,
        'data': {'electionid': id, 'status': 2},
        'message': '冻结选举成功！'
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


def stop_voting(request):
    """
    结束选举：修改选举状态
    :param request:
    :return:
    """
    data = json.loads(request.body)
    id = data['electionid']
    try:
        election = Elections.objects.get(id=id)
        election.status = 4
        election.save()
    except Exception:
        pass
    res = {
        'code': 1,
        'data': {'electionid': id, 'status': 4},
        'message': '结束选举成功！'
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


# ################################相应BBS请求##################################
def read_from_verify(path):
    result = []
    return result


def response_bbc(request):
    """
    相应BBS请求：将能够填充的数据段都填充完整，发送给客户端
    :return:
    """
    data = json.loads(request.body)
    id = data['electionid']
    election = Elections.objects.filter(id=id)
    result = {}
    if election.isAnonymous:
        result['publicmessage'] = election.publicKey
        result['privatemessage'] = "证明文件下载地址：" + election.verifyFile
    else:
        result['publicmessage'] = "非加密投票中无需产生公钥"
        result['privatemessage'] = "非加密投票中无需产生证明文件"
    voter_list = VoterList.objects.filter(election=election).value_list('voter', 'voteResult')
    privatemessage = []
    for each in voter_list:
        if each[1] is not None:
            privatemessage.append({'user': each[0], 'vote': each[1]})
    result['privatemessage'] = privatemessage
    if election.status == 5:
        result_list = read_from_verify(election.verifyFile)
        resshow = []
        for each in result_list:
            resshow.append({'plainvote': each[0], 'verifyinfo': each[1]})
        result['resshow'] = resshow
        result['resstatistics'] = election.voteResult
    else:
        result['resshow'] = ""
        result['resstatistics'] = ""

    res = {
        'code': 1,
        'data': result,
        'message': '更新数据成功！'
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


# ################################生成投票结果##################################
def generate_result(request):
    pass


def anonymous_result():
    pass


def real_name_result():
    pass


# ################################返回投票中的加密包，接收最终投票结果##################################
def fetch_vote_functions(request):
    pass


def fetch_vote_info(request):
    pass


def collect_votes(request):
    pass


# ################################提供文件下载服务##################################
def file_response_download(request, file_path):
    root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    folder = os.path.join(root, 'election\\verifyfiles\\')
    try:
        response = FileResponse(open(folder + file_path, 'rb'))
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
        return response
    except Exception:
        raise Http404
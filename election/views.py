import os
import jwt
import json
import parameters
from django.db.models import Q
from django.conf import settings
from .utils.SendEmail import EmailSender
from django.http import HttpResponse, Http404, FileResponse
from django.contrib.auth.models import User
from .models import Elections, VoterList, TempVoterList
from .utils.CryptoTools import GenerateParameters, HashTools, MixNet, str2integer


# ################################创建、获取、修改、删除选举##################################
def create_election(request):
    """
    创建新选举：
    1.解析提交数据，将本次选举信息记录到数据库中。
    """
    data = json.loads(request.body)
    if parameters.Istest:
        username = 'admin'
    else:
        auth = request.META.get('HTTP_AUTHORIZATION').split()
        token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
        username = token.get('data').get('username')

    temp_election = Elections.from_dict(data, User.objects.get(username=username))

    if temp_election:
        for i in range(len(data['voterslist'])):
            temp_voters = {}
            temp_voters['voter'] = data['voterslist'][i]['username']
            temp_voters['firstName'] = data['voterslist'][i]['firstname']
            temp_voters['lastName'] = data['voterslist'][i]['lastname']
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
    if parameters.Istest:
        author = User.objects.get(username='admin')
    else:
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
            'data': {'electionList': elections_list},
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
        for i in range(len(data['voterslist'])):
            temp_voters={}
            temp_voters['voter'] = data['voterslist'][i]['username']
            temp_voters['firstName'] = data['voterslist'][i]['firstname']
            temp_voters['lastName'] = data['voterslist'][i]['lastname']
            temp_voters['email'] = data['emaillist'][i]
            temp_voters['election'] = election
            TempVoterList.objects.create(**temp_voters)
        election = Elections.objects.get(id=id)
        dictlist = election.to_dict()

        res = {
            'code': 1,
            'data': {'election': dictlist},  # election.to_dict(),
            'message': '更新投票成功'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
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
            'data': {'electionid': id, 'status': "6"},
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
    status = int(data['status'])
    print("是否是第一次启动(0表示是)：", status)
    try:
        election = Elections.objects.get(id=id)
        election.status = 1
        if status == 0:
            # 生成公钥 私钥
            key = GenerateParameters(256)
            election.publicKey = key.get_public_key()
            election.privateKey = key.get_private_key()
            # 给每个选项生成hash码
            selectionlist = [each.split('&') for each in election.selections.split('@')[1:]]

            def covert(lists):
                dic = {}
                h = HashTools(256)
                for each in lists:
                    dic[each] = h.get_hash(each)
                return str(dic)

            strlist = [covert(item) for item in selectionlist]
            hashvalue = strlist[0]
            for i in range(len(strlist)-1):
                hashvalue += "&&" + strlist[i+1]
            election.selectionsHash = hashvalue

            voters = TempVoterList.objects.filter(election=election)
            election.save()
            receivers = []
            usernames = []
            passwords = []
            print("jie guo baocun chenggong ")
            for each in voters:
                usernames.append(each.voter)
                receivers.append(each.email)
                try:
                    User.objects.get(username=each.voter)
                    passwords.append('your own passwords!')
                except User.DoesNotExist:
                    User.objects.create_user(username=each.voter, password='123456', email=each.email)
                    passwords.append('123456')
                VoterList.objects.create(voter=User.objects.get(username=each.voter), email=each.email, election=election)
            urls = 'http://localhost:3000/user/login'
            print("jie guo baocun chenggong ")
            emailSender = EmailSender(receivers, usernames, passwords, urls)
            emailSender.send_emails()
    except Exception:
        res = {
            'code': -1,
            'message': '选举启动失败！'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    res = {
        'code': 1,
        'data': {'electionid': id, 'status': "1"},
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
        'data': {'electionid': id, 'status': "2"},
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
        'data': {'electionid': id, 'status': "4"},
        'message': '结束选举成功！'
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


# ################################相应BBS请求##################################
def read_from_verify(abspath):
    result = []
    with open(abspath, 'r') as f:
        data = json.load(f)
        for item in data:
            if 'encoder' in item:
                result.append(item)
            else:
                break
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
        result['provemessage'] = "证明文件下载地址：" + election.verifyFile
    else:
        result['publicmessage'] = "非加密投票中无需产生公钥"
        result['provemessage'] = "非加密投票中无需产生证明文件"

    voter_list = VoterList.objects.filter(election=election).value_list('voter', 'voteResult')
    privatemessage = []
    for each in voter_list:
        if each[1] is not None:
            privatemessage.append({'user': each[0], 'vote': each[1]})
    result['privatemessage'] = privatemessage

    if election.status == 5:
        result['resshow'] = read_from_verify(election.verifyFile)
        result['resstatistics'] = eval(election.voteResult)
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
    data = json.loads(request.body)
    election = Elections.objects.filter(id=data['electionid'])
    election.status = 3
    if election.isAnonymous:
        return anonymous_result(request)
    else:
        return real_name_result(request)


def anonymous_result(request):
    data = json.loads(request.body)
    try:
        election = Elections.objects.filter(id=data['electionid'])
        voterlist = VoterList.objects.filter(election=election)
        publickey = eval(election.publicKey)
        p = str2integer(publickey['p'])
        g = str2integer(publickey['g'])
        h = str2integer(publickey['h'])
        x = str2integer(election.privateKey)
        selections = election.selectionsHash
        votes = []
        votegrs = []
        for item in voterlist:
            votes.append(item.voteResult.split("&&"))
            votegrs.append(item.voterKey.split("&&"))
        mymix = MixNet(p, g, x, h, votes, votegrs, len(votes), selections)
        message = mymix.get_plain_message()
        folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'election\\verifyfiles\\')
        path = folder + "verify_for_election_" + data['id'] + ".json"
        mymix.verify_file_generate(path)
        result = []
        for item in message:
            for each in item:
                if each in result:
                    result[each] = result[each] + 1
                else:
                    result[each] = 1
        election.voteResult = str(result)
        election.verifyFile = path
        election.status = 5
        election.save()

        res = {
            'code': 1,
            'data': {'electionid': data['electionid'], 'status': "5"},
            'message': '统计结果成功！'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '统计结果失败！'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


def real_name_result(request):
    data = json.loads(request.body)
    election = Elections.objects.filter(id=data['electionid'])
    out = VoterList.objects.filter(election=election).value_list('voteResult')
    result = {}
    for item in out:
        for each in item:
            if each in result:
                result[each] = result[each] + 1
            else:
                result[each] = 1
    election.voteResult = str(result)
    election.status = 5
    election.save()
    res = {
        'code': 1,
        'data': {'electionid': data['electionid'], 'status': "5"},
        'message': '统计结果成功！'
    }
    return HttpResponse(json.dumps(res), content_type='application/json')


# ################################返回投票中的加密包，接收最终投票结果##################################
def fetch_vote_functions(request):
    data = json.loads(request.body)
    election = Elections.objects.get(id=int(data['electionid']))
    print(election)
    publickey = {}
    hashvalue = []
    if election.isAnonymous:
        publickey = eval(election.publicKey)
        hashvalue = [eval(each) for each in election.selectionsHash.split('&&')]
    try:
        res = {
            'code': 1,
            'data': {'publickey': publickey, 'selectionhash': hashvalue},
            'message': '获取投票函数成功'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '获取投票函数失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


def fetch_vote_info(request):
    if parameters.Istest:
        user = User.objects.get(username='admin')
    else:
        auth = request.META.get('HTTP_AUTHORIZATION').split()
        token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
        username = token.get('data').get('username')
        user = User.objects.get(username=username)
    try:
        voters = VoterList.objects.filter(voter=user)
        elections = []
        for each in voters:
            item = each.election
            election = item.to_dict()
            election['isvoted'] = each.isVote
            elections.append(election)
        res = {
            'code': 1,
            'data': {'votesList': elections},
            'message': '获取选举信息成功'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '获取投票信息失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


def collect_votes(request):
    data = json.loads(request.body)
    if parameters.Istest:
        user = 'admin'
    else:
        auth = request.META.get('HTTP_AUTHORIZATION').split()
        token = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
        username = token.get('data').get('username')
        user = User.objects.get(username=username)

    try:
        election = Elections.objects.get(id=data['electionid'])
        voterlist = VoterList.objects.filter(election=election).filter(voter=user)
        for item in voterlist:
            pm = data['privatemessage'][0]
            for i in range(len(data['privatemessage'])-1):
                pm += "&&" + data['privatemessage'][i+1]
            item.voteResult = pm
            if election.isAnonymous:
                td = data['trapdoor'][0]
                for i in range(len(data['trapdoor'])-1):
                    td += "&&" + data['trapdoor'][i+1]
                item.voterKey = td
            item.isVote = True
            item.save()
        res = {
            'code': 1,
            'message': '投票成功'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')
    except Exception:
        res = {
            'code': -1,
            'message': '投票失败'
        }
        return HttpResponse(json.dumps(res), content_type='application/json')


# ################################提供文件下载服务##################################
def file_response_download(request, file_path):
    folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'election\\verifyfiles\\')
    try:
        response = FileResponse(open(folder + file_path, 'rb'))
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
        return response
    except Exception:
        raise Http404
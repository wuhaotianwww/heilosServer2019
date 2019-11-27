from django.test import TestCase
from django.contrib.auth.models import User
from .models import Elections, VoterList, TempVoterList
import json


class MyTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='admin', password='admin', email='2480850946@qq.com')
        data = {
                'shortname': 'test',
                'fullname': 'test',
                'isprivate': True,
                'isanonymous': True,
                'info': 'test',
                'starttime': '2019-11-27 15:32:12',
                'endtime': '2019-11-27 15:32:12',
                'questionlist': ['早上吃什么？', '中午吃什么？', '晚上吃什么？'],
                'selectionlist': [['牛奶', '豆浆', '粥'], ['米饭', '面条', '饼'], ['馒头', '包子', '面包']],
                'voterslist': ['zhangsan', 'lisi', 'wangwu', 'heliu', 'admin'],
                'emaillist': ['2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com'],
            }
        temp_election = Elections.from_dict(data, user)
        res = VoterList.objects.create(voter='admin', email='2480850946@qq.com', voteResult="1", voterKey="1", election=temp_election)
        for i in range(len(data['voterslist'])):
            temp_voters = {}
            temp_voters['voter'] = data['voterslist'][i]
            temp_voters['email'] = data['emaillist'][i]
            temp_voters['election'] = temp_election
            if not TempVoterList.objects.create(**temp_voters):
                print("数据创建失败")
        voters = TempVoterList.objects.filter(election=temp_election).values_list('voter')
        print(voters)


    # def test_create_election(self):
    #     data = {
    #         'shortname': 'test',
    #         'fullname': 'test',
    #         'isprivate': True,
    #         'isanonymous': True,
    #         'info': 'test',
    #         'starttime': '2019-11-27 15:32:12',
    #         'endtime': '2019-11-27 15:32:12',
    #         'questionlist': ['早上吃什么？', '中午吃什么？', '晚上吃什么？'],
    #         'selectionlist': [['牛奶', '豆浆', '粥'], ['米饭', '面条', '饼'], ['馒头', '包子', '面包']],
    #         'voterslist': ['zhangsan', 'lisi', 'wangwu', 'heliu', 'laoqi'],
    #         'emaillist': ['2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com'],
    #     }
    #     response = self.client.post('/election/createElection/', json.dumps(data), content_type="application/json")
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_fetch_elections(self):
    #     response = self.client.get('/election/fetchElections/')
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_update_elections(self):
    #     data = {
    #         'id': 1,
    #         'shortname': 'test',
    #         'fullname': 'test',
    #         'isprivate': True,
    #         'isanonymous': True,
    #         'info': 'test',
    #         'starttime': '2019-11-27 15:32:12',
    #         'endtime': '2019-11-27 15:32:12',
    #         'questionlist': ['早上吃什么？', '中午吃什么？', '晚上吃什么？'],
    #         'selectionlist': [['牛奶', '豆浆', '粥'], ['米饭', '面条', '饼'], ['馒头', '包子', '面包']],
    #         'voterslist': ['zhangsan', 'lisi', 'wangwu', 'heliu', 'laoqi'],
    #         'emaillist': ['2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com', '2480850946@qq.com',
    #                       '2480850946@qq.com'],
    #     }
    #     response = self.client.post('/election/updateElection/', json.dumps(data), content_type="application/json")
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_delete_elections(self):
    #     data = {
    #         'electionid': 1,
    #         'status': 5
    #     }
    #     response = self.client.post('/election/deleteElection/', json.dumps(data), content_type="application/json")
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_start_voting(self):
    #     response = self.client.get('http://otherserver/foo/bar/')

    # def test_suspend_voting(self):
    #     data = {
    #         'electionid': 1,
    #         'status': 5
    #     }
    #     response = self.client.post('/election/freezeElection/', json.dumps(data), content_type="application/json")
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_stop_voting(self):
    #     data = {
    #         'electionid': 1,
    #         'status': 5
    #     }
    #     response = self.client.post('/election/endElection/', json.dumps(data), content_type="application/json")
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_response_bbc(self):
    #     response = self.client.get('http://otherserver/foo/bar/')
    #
    # def test_generate_result(self):
    #     response = self.client.get('http://otherserver/foo/bar/')

    # def test_fetch_vote_info(self):
    #     response = self.client.get('/election/fetchVotings/')
    #     print(response)
    #     print(str(json.loads(response.content)))

    # def test_fetch_vote_functions(self):
    #     data = {
    #             'electionid': 1,
    #         }
    #     response = self.client.post('/election/fetchVotingInfo/', json.dumps(data), content_type="application/json")
    #     print(response)
    #     print(str(json.loads(response.content)))

    def test_collect_votes(self):
        data = {
            'electionid': 1,
            'privatemessage': "236543746129847192385346283917259634723451252341543",
            'trapdoor': "68549721643937162538968125691"
        }
        response = self.client.post('/election/reportVoting/', json.dumps(data), content_type="application/json")
        print(response)
        print(str(json.loads(response.content)))



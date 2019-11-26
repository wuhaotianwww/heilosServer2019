from django.utils.deprecation import MiddlewareMixin
import parameters


class AuthMD(MiddlewareMixin):
    if not parameters.Istest:
        balck_list = ['/election/createElection/',
                      '/election/fetchElections/',
                      '/election/updateElection/',
                      '/election/deleteElection/',
                      '/election/startElection/',
                      '/election/freezeElection/',
                      '/election/endElection/',
                      '/election/fetchBbs/',
                      '/election/resultElection/',
                      '/election/fetchVotings/',
                      '/election/fetchVotingInfo/',
                      '/account/reportVoting/']  # 黑名单
    else:
        balck_list = []

    def process_request(self, request):
        from django.http import HttpResponse
        import jwt
        from django.conf import settings
        from django.contrib.auth.models import User
        import json

        next_url = request.path_info
        print(next_url)

        if next_url in self.balck_list:
            try:
                auth = request.META.get('HTTP_AUTHORIZATION').split()
            except AttributeError:
                response = HttpResponse(json.dumps(
                    {"code": 401, "message": "No authenticate header"}), content_type='application/json')
                response.status_code = 401
                return response

            if auth[0].lower() == 'token':
                try:
                    token = jwt.decode(
                        auth[1], settings.SECRET_KEY, algorithms=['HS256'])
                    username = token.get('data').get('username')
                except jwt.ExpiredSignatureError:
                    response = HttpResponse(json.dumps(
                        {"code": 401, "message": "Token expired"}), content_type='application/json')
                    response.status_code = 401
                    return response
                except jwt.InvalidTokenError:
                    response = HttpResponse(json.dumps(
                        {"code": 401, "message": "Invalid token"}), content_type='application/json')
                    response.status_code = 401
                    return response
                except Exception:
                    response = HttpResponse(json.dumps(
                        {"code": 401, "message": "Can not get user object"}), content_type='application/json')
                    response.status_code = 401
                    return response

                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    response = HttpResponse(json.dumps(
                        {"code": 401, "message": "User Does not exist"}), content_type='application/json')
                    response.status_code = 401
                    return response

                if not user.is_active:
                    response = HttpResponse(json.dumps(
                        {"code": 401, "message": "User inactive or deleted"}), content_type='application/json')
                    response.status_code = 401
                    return response

            else:
                response = HttpResponse(json.dumps(
                    {"code": 401, "message": "Not support auth type"}), content_type='application/json')
                response.status_code = 401
                return response
        return None

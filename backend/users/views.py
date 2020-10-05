import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from users.actions import get_user_data
from users.models import Profile


@csrf_exempt
def signup(request):
    response = {
        'success': False,
        'debug': ''
    }
    try:
        if request.method == 'POST':
            request_data = request.body
            request_json = json.loads(request_data)
            if 'email' in request_json and 'username' in request_json and 'password' in request_json:
                if request_json['email'] and request_json['username'] and request_json['password']:

                    new_user = User()
                    new_user.email = request_json['email']
                    new_user.username = request_json['username']
                    new_user.set_password(request_json['password'])
                    new_user.save()

                    response['success'] = True
                else:
                    response['debug'] = 'Invalid Argument'
            else:
                response['debug'] = 'Missing Argument'
        else:
            response['debug'] = 'Request Method is not allowed.'
    except Exception as e:
        response['debug'] = str(e)
    return JsonResponse(response, safe=False)


@csrf_exempt
def signin(request):
    response = {
        'success': False,
        'token': '',
        'username': '',
        'debug': ''
    }
    try:
        if request.method == 'POST':
            request_data = request.body
            request_json = json.loads(request_data)

            if 'username' in request_json and 'password' in request_json:
                user = authenticate(username=request_json['username'], password=request_json['password'])
                if user is not None:
                    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                    jwt_endcode_handler = api_settings.JWT_ENCODE_HANDLER
                    payload = jwt_payload_handler(user)
                    token = jwt_endcode_handler(payload)
                    response['success'] = True
                    response['token'] = token
                    response['username'] = user.username
                else:
                    response['debug'] = 'Invalid Credential'
            else:
                response['debug'] = 'Missing Argument'
        else:
            response['debug'] = 'Request Method is not allowed.'
    except Exception as e:
        response['debug'] = str(e)
    return JsonResponse(response, safe=False)


@api_view(['GET'], )
def getUser(request):
    response = {
        'success': False,
        'username': '',
        'debug': '',
    }
    try:
        response['success'] = True
        response['username'] = request.user.username
    except Exception as e:
        response['debug'] = str(e)
    return Response(response)


@api_view(['GET'], )
def getUserData(request):
    response = {
        'success': False,
        'user': '',
        'debug': '',
    }
    try:
        response['success'] = True
        response['user'] = get_user_data(request.user)
    except Exception as e:
        response['debug'] = str(e)
    return Response(response)


@api_view(['POST'], )
def updateUser(request):
    response = {
        'success': False,
        'username': request.user.username,
        'debug': '',
    }

    try:
        request_json = json.loads(request.body)
        try:
            profile = Profile.objects.get(owner=request.user)
        except Exception as e:
            print(e)
            profile = Profile()
            profile.owner = request.user

        if 'push_token' in request_json and request_json['push_token']:
            profile.push_token = request_json['push_token']

        if 'push_notification' in request_json:
            profile.push_notification = request_json['push_notification']

        if 'telegram_notification' in request_json:
            profile.telegram_notification = request_json['telegram_notification']

        if 'email_notification' in request_json:
            profile.email_notification = request_json['email_notification']

        if 'notification_message' in request_json and request_json['notification_message']:
            profile.notification_message = request_json['notification_message']

        profile.save()
        response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)

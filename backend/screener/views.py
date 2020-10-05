import datetime
import json
import time
from threading import Thread

from rest_framework.decorators import api_view
from rest_framework.response import Response

from screener.actions import model_to_json, update_dashboard_screener, get_dashboard_screener_json, delete_dashboard_screener, update_price_action
from screener.models import Screener, DashBoardScreener


def update_dashboard():
    while True:
        screener_list = Screener.objects.filter(is_active=True)
        if len(screener_list) > 0:
            for screener in screener_list:
                update_dashboard_screener(screener)
                time.sleep(3)
        else:
            print("There is no active screener")
        time.sleep(300)


def update_price():
    while True:
        screener_list = DashBoardScreener.objects.all()
        if len(screener_list) > 0:
            for screener in screener_list:
                update_price_action(screener)
                time.sleep(1)
        else:
            print("There is no active screener")
        time.sleep(2)


thread_update_dashboard = Thread(target=update_dashboard)
# thread_update_dashboard.start()
print("Dashboard Thread started!")

thread_update_price = Thread(target=update_price)
# thread_update_price.start()
print("Price Thread started!")


@api_view(['GET'], )
def list_screener(request, pk=0):
    response = {
        'success': False,
        'data': [],
        'debug': '',
    }

    try:
        if not pk:
            screeners = Screener.objects.filter(owner=request.user)
        else:
            screeners = [Screener.objects.get(id=pk)]

        if screeners:
            for item in screeners:
                response['data'].append(model_to_json(item))
            response['success'] = True
        else:
            response['debug'] = 'No Data'
            response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['POST'], )
def create_screener(request):
    response = {
        'success': False,
        'data': [],
        'debug': ''
    }

    try:
        request_json = json.loads(request.body)

        if 'name' in request_json and 'exchange' in request_json and 'base_pair' in request_json and 'rule' in request_json and 'parameters' in request_json:
            if request_json['name'] and request_json['exchange'] and request_json['base_pair'] and request_json['rule'] and request_json['parameters']:

                new_screener = Screener()
                new_screener.name = request_json['name']
                new_screener.security_type = request_json['security_type']
                new_screener.exchange = request_json['exchange']
                new_screener.base_pair = request_json['base_pair']
                new_screener.rule = request_json['rule']
                new_screener.parameters = request_json['parameters']
                new_screener.owner = request.user
                new_screener.save()

                response['success'] = True
                response['data'].append(model_to_json(new_screener))
            else:
                response['debug'] = 'Invalid Argument'
        else:
            response['debug'] = 'Missing Argument'
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['PUT'], )
def update_screener(request, pk=0):
    response = {
        'success': False,
        'data': [],
        'debug': '',
    }

    try:
        request_json = json.loads(request.body)
        current_screener = Screener.objects.get(id=pk)

        if 'name' in request_json and request_json['name']:
            current_screener.name = request_json['name']
        if 'security_type' in request_json and request_json['security_type']:
            current_screener.security_type = request_json['security_type']
        if 'exchange' in request_json and request_json['exchange']:
            current_screener.exchange = request_json['exchange']
        if 'base_pair' in request_json and request_json['base_pair']:
            current_screener.base_pair = request_json['base_pair']
        if 'rule' in request_json and request_json['rule']:
            current_screener.rule = request_json['rule']
        if 'parameters' in request_json and request_json['parameters']:
            current_screener.parameters = request_json['parameters']
        if 'is_active' in request_json:
            current_screener.is_active = request_json['is_active']

        current_screener.updated_at = datetime.datetime.now()
        current_screener.save()

        if current_screener.is_active:
            update_dashboard_screener(current_screener)
        else:
            delete_dashboard_screener(current_screener)

        response['success'] = True
        response['data'].append(model_to_json(current_screener))

    except Exception as e:
        print(e)
        response['debug'] = str(e)

    return Response(response)


@api_view(['DELETE'], )
def delete_screener(request, pk=0):
    response = {
        'success': False,
        'data': [],
        'debug': '',
    }

    try:
        if pk != "0":
            Screener.objects.get(id=pk).delete()
        else:
            Screener.objects.all().delete()
        response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['GET'], )
def dashboard_screener(request):
    response = {
        'success': False,
        'data': [],
        'debug': ''
    }
    try:
        dashboard_screeners = DashBoardScreener.objects.filter(screener__owner=request.user)
        for item in dashboard_screeners:
            response['data'].append(get_dashboard_screener_json(item))
        response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)

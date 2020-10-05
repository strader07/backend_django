import datetime
import json
import time
from threading import Thread

from rest_framework.decorators import api_view
from rest_framework.response import Response

from alert.actions import alert_to_json, update_dashboard_alert, get_dashboard_alert_json, check_min_max
from alert.models import Alert, DashBoardAlert


def update_dashboard_alert_thread():
    while True:
        alert_list = Alert.objects.filter(is_active=True)
        if len(alert_list) > 0:
            for alert in alert_list:
                update_dashboard_alert(alert)
                time.sleep(3)
        else:
            print("There is no active screener")
        time.sleep(300)


thread_update_dashboard_alert = Thread(target=update_dashboard_alert_thread)
# thread_update_dashboard_alert.start()
print("Dashboard Alert Thread started!")


@api_view(['GET'], )
def list_alert(request, pk=0):
    response = {
        'success': False,
        'data': [],
        'debug': '',
    }

    try:
        if not pk:
            alerts = Alert.objects.filter(owner=request.user)
        else:
            alerts = [Alert.objects.get(id=pk)]

        if alerts:
            for item in alerts:
                response['data'].append(alert_to_json(item))
            response['success'] = True
        else:
            response['debug'] = 'No Data'
            response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['POST'], )
def create_alert(request):
    response = {
        'success': False,
        'data': [],
        'debug': ''
    }

    try:
        request_json = json.loads(request.body)

        if 'name' in request_json and 'exchange' in request_json and 'base_pair' in request_json and 'rule' in request_json and 'symbols' in request_json and 'parameters' in request_json:
            if request_json['name'] and request_json['exchange'] and request_json['base_pair'] and request_json['rule'] and request_json['symbols'] and request_json['parameters']:

                new_alert = Alert()
                new_alert.name = request_json['name']
                new_alert.security_type = request_json['security_type']
                new_alert.exchange = request_json['exchange']
                new_alert.base_pair = request_json['base_pair']
                new_alert.symbols = request_json['symbols']
                new_alert.rule = request_json['rule']
                new_alert.parameters = request_json['parameters']
                new_alert.owner = request.user
                new_alert.save()

                symbol_list = json.loads(request_json['symbols'])
                for symbol in symbol_list:
                    check_min_max(new_alert, symbol['value'])

                response['success'] = True
                response['data'].append(alert_to_json(new_alert))
            else:
                response['debug'] = 'Invalid Argument'
        else:
            response['debug'] = 'Missing Argument'
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['PUT'], )
def update_alert(request, pk=0):
    response = {
        'success': False,
        'data': [],
        'debug': '',
    }

    try:
        request_json = json.loads(request.body)
        current_alert = Alert.objects.get(id=pk)

        if 'name' in request_json and request_json['name']:
            current_alert.name = request_json['name']
        if 'security_type' in request_json and request_json['security_type']:
            current_alert.security_type = request_json['security_type']
        if 'exchange' in request_json and request_json['exchange']:
            current_alert.exchange = request_json['exchange']
        if 'base_pair' in request_json and request_json['base_pair']:
            current_alert.base_pair = request_json['base_pair']
        if 'symbols' in request_json and request_json['symbols']:
            current_alert.symbols = request_json['symbols']
        if 'rule' in request_json and request_json['rule']:
            current_alert.rule = request_json['rule']
        if 'parameters' in request_json and request_json['parameters']:
            current_alert.parameters = request_json['parameters']
        if 'is_active' in request_json:
            current_alert.is_active = request_json['is_active']

        current_alert.updated_at = datetime.datetime.now()
        current_alert.save()

        if current_alert.is_active:
            update_dashboard_alert(current_alert)

        response['success'] = True
        response['data'].append(alert_to_json(current_alert))

    except Exception as e:
        print(e)
        response['debug'] = str(e)

    return Response(response)


@api_view(['DELETE'], )
def delete_alert(request, pk=0):
    response = {
        'success': False,
        'data': [],
        'debug': '',
    }

    try:
        if pk != "0":
            Alert.objects.get(id=pk).delete()
        else:
            Alert.objects.filter(owner=request.user).delete()
        response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['GET'], )
def dashboard_alert(request):
    response = {
        'success': False,
        'data': [],
        'debug': ''
    }
    try:
        dashboard_alert_list = DashBoardAlert.objects.filter(alert__owner=request.user)
        for item in dashboard_alert_list:
            response['data'].append(get_dashboard_alert_json(item))
        response['success'] = True
    except Exception as e:
        response['debug'] = str(e)

    return Response(response)


@api_view(['DELETE'], )
def delete_all_dashboard_alert(request):
    response = {
        'success': False,
        'debug': ''
    }
    try:
        DashBoardAlert.objects.filter(alert__owner=request.user).delete()
        response['success'] = True
    except Exception as e:
        response['debug'] = str(e)
    return Response(response)

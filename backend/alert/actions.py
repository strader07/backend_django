import datetime
import json

import requests
from django.core.mail import EmailMultiAlternatives

from alert.models import DashBoardAlert, MinMaxPrice
from backend.settings import FRONTEND_URL, FIREBASE_NOTIFICATION_SERVER_KEY, EMAIL_FROM, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, API_KEY
from screener.actions import get_rule_obj
from users.models import Profile


def get_price_value(symbol):
    try:
        url = 'https://api.twelvedata.com/time_series?symbol=' + symbol + '&interval=1day&apikey=' + API_KEY + '&source=docs'
        response = requests.request('GET', url).json()
        return response['values']
    except Exception as e:
        print(e)
        return None


def get_week(price_value, _monday):
    min_week = 99999999
    max_week = 0
    for item in price_value:
        datetime_string = item['datetime'] + ' 00:00:00'
        current_datetime = datetime.datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
        if current_datetime >= _monday:
            if float(item['high']) > max_week:
                max_week = float(item['high'])
            if float(item['low']) < min_week:
                min_week = float(item['low'])
    return min_week, max_week


def get_month(price_value, _month):
    min_month = 99999999
    max_month = 0
    for item in price_value:
        datetime_string = item['datetime'] + ' 00:00:00'
        current_datetime = datetime.datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
        if current_datetime >= _month:
            if float(item['high']) > max_month:
                max_month = float(item['high'])
            if float(item['low']) < min_month:
                min_month = float(item['low'])
    return min_month, max_month


def check_min_max(alert, symbol):
    _now = datetime.datetime.now()
    _monday = _now - datetime.timedelta(days=_now.weekday())
    _monday = _monday.replace(hour=0, minute=0, second=0, microsecond=0)
    _month = _now
    if _month.day > 25:
        _month += datetime.timedelta(7)
    _month = _month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    try:
        current_symbol = MinMaxPrice.objects.get(alert=alert, symbol=symbol)
        if current_symbol.current_month == _month and current_symbol.current_week == _monday:
            return
        else:
            if current_symbol.current_month == _month:
                price_value = get_price_value(symbol)
                if price_value:
                    min_week, max_week = get_week(price_value, _monday)
                    current_symbol.min_price_week = min_week
                    current_symbol.max_price_week = max_week
                    current_symbol.current_week = _monday
                    current_symbol.save()
            else:
                price_value = get_price_value(symbol)
                if price_value:
                    min_month, max_month = get_month(price_value, _month)
                    min_week, max_week = get_week(price_value, _monday)
                    new_min_max_price = MinMaxPrice()
                    new_min_max_price.symbol = symbol
                    new_min_max_price.max_price_week = max_week
                    new_min_max_price.min_price_week = min_week
                    new_min_max_price.max_price_month = max_month
                    new_min_max_price.min_price_month = min_month
                    new_min_max_price.current_week = _monday
                    new_min_max_price.current_month = _month
                    new_min_max_price.save()

    except Exception as e:
        print(e)

        price_value = get_price_value(symbol)
        if price_value:
            min_month, max_month = get_month(price_value, _month)
            min_week, max_week = get_week(price_value, _monday)
            new_min_max_price = MinMaxPrice()
            new_min_max_price.alert = alert
            new_min_max_price.symbol = symbol
            new_min_max_price.max_price_week = max_week
            new_min_max_price.min_price_week = min_week
            new_min_max_price.max_price_month = max_month
            new_min_max_price.min_price_month = min_month
            new_min_max_price.created_at = _now
            new_min_max_price.current_week = _monday
            new_min_max_price.current_month = _month
            new_min_max_price.save()


def alert_to_json(alert):
    symbol_list = json.loads(alert.symbols)
    symbol_txt = ''
    for symbol in symbol_list:
        symbol_txt += symbol['label'] + ', '
    return {
        'id': alert.id,
        'name': alert.name,
        'security_type': alert.security_type,
        'exchange': alert.exchange,
        'base_pair': alert.base_pair,
        'symbols': alert.symbols,
        'symbol_txt': symbol_txt[:-2],
        'rule': alert.rule,
        'parameters': alert.parameters,
        'is_active': alert.is_active,
        'created_at': alert.created_at.strftime('%m/%d/%Y %H:%M'),
        'updated_at': alert.updated_at.strftime('%m/%d/%Y %H:%M'),
        'owner': alert.owner.username
    }


def get_dashboard_alert_json(dashboard_alert):
    dif_date = datetime.datetime.now() - dashboard_alert.created_at

    if dashboard_alert.optional_str:
        trigger = dashboard_alert.optional_str
    else:
        trigger = dashboard_alert.alert.rule

    return {
        'id': dashboard_alert.id,
        'alert_name': dashboard_alert.alert.name,
        'pair_name': dashboard_alert.pair_name,
        'trigger': trigger,
        'triggered_when': str(dif_date).split('.')[0]
    }


def get_price(symbol):
    try:
        url = 'https://api.twelvedata.com/quote?symbol=' + symbol + '&apikey=' + API_KEY
        print(url)
        response = requests.request('GET', url)
        price_json = response.json()
        return True, price_json['high'], price_json['low']
    except Exception as e:
        print(e)
        return False, None, None


def send_notification(alert, rule, pair_name):
    try:
        profile = Profile.objects.get(owner=alert.owner)
        message = profile.notification_message + '\n' + 'pair: ' + pair_name + '\n' + 'rule: ' + rule
        if profile.push_notification:
            print('Sending push notification...')
            payload = {
                "notification": {
                    "title": "Alert Notification",
                    "body": message,
                    "click_action": FRONTEND_URL,
                },
                "to": profile.push_token,
            }
            headers = {
                "Authorization": "key=" + FIREBASE_NOTIFICATION_SERVER_KEY,
                "Content-Type": "application/json",
            }
            url = 'https://fcm.googleapis.com/fcm/send'

            response = requests.request('POST', url, data=json.dumps(payload), headers=headers)
            print("Firebase Notification: ", response.status_code)

        if profile.email_notification:
            print('Sending email notification...')
            subject = "Alert notification"
            message = message
            email_from = "Screener Support<" + EMAIL_FROM + ">"
            recipient_list = [alert.owner.email, ]

            message_object = EmailMultiAlternatives(subject, message, email_from, recipient_list)
            message_object.send()

        if profile.telegram_notification:
            print('Sending telegram notification...')

            url = 'https://api.telegram.org/bot' + TELEGRAM_BOT_TOKEN + '/sendMessage?chat_id=@' + TELEGRAM_CHAT_ID + '&text=' + message
            response = requests.request('GET', url)
            print("Telegram notification: ", response.status_code)

    except Exception as e:
        print(e)
        return False


def update_dashboard_alert(alert):
    if not alert.is_active:
        return

    base_url = 'https://api.twelvedata.com/INDICATORNAME?symbol=SYMBOLNAME'

    rule_obj = get_rule_obj(alert.rule)
    parameter_obj = json.loads(alert.parameters)
    output_dict = json.loads(alert.symbols)

    if len(output_dict):
        for item in output_dict:
            try:
                rule_condition = ""
                rule_condition_result = True
                for i in range(len(rule_obj)):
                    current_condition = True

                    time_frame = [x for x in parameter_obj[i]['first_indicator'] if x['name'] == 'Timeframe']

                    parameters = [x for x in parameter_obj[i]['first_indicator'] if x['name'] != 'Timeframe']
                    param_argument = ''

                    for param in parameters:
                        param_argument += '&' + param['name'].lower().replace(' ', '_') + '=' + str(param['value'])

                    rule_value_obj = rule_obj[i]
                    url = base_url.replace('INDICATORNAME', rule_value_obj['first_indicator'].lower()).replace('SYMBOLNAME', item['value'])
                    url += param_argument
                    url += '&interval=' + time_frame[0]['value'] + '&apikey=' + API_KEY

                    r = requests.get(url)
                    print(url)
                    try:
                        response_json = r.json()
                        if response_json['status'] == "ok":
                            response_first_indicator = response_json['values']
                        else:
                            rule_condition_result = False
                            break
                    except Exception as e:
                        print(e)
                        rule_condition_result = False
                        break

                    time_frame = [x for x in parameter_obj[i]['second_indicator'] if x['name'] == 'Timeframe']

                    parameters = [x for x in parameter_obj[i]['second_indicator'] if x['name'] != 'Timeframe']
                    param_argument = ''

                    for param in parameters:
                        param_argument += '&' + param['name'].lower().replace(' ', '_') + '=' + str(param['value'])

                    url = base_url.replace('INDICATORNAME', rule_value_obj['second_indicator'].lower()).replace('SYMBOLNAME', item['value'])
                    url += param_argument
                    url += '&interval=' + time_frame[0]['value'] + '&apikey=' + API_KEY

                    r = requests.get(url)
                    print(url)
                    try:
                        response_json = r.json()
                        if response_json['status'] == "ok":
                            response_second_indicator = response_json['values']
                        else:
                            rule_condition_result = False
                            break
                    except Exception as e:
                        print(e)
                        rule_condition_result = False
                        break

                    if rule_value_obj['condition'] == 'Above':
                        if float(response_first_indicator[0][rule_obj[i]['first_indicator'].lower()]) < float(response_second_indicator[0][rule_obj[i]['second_indicator'].lower()]):
                            current_condition = False
                    elif rule_value_obj['condition'] == 'Below':
                        if float(response_first_indicator[0][rule_obj[i]['first_indicator'].lower()]) > float(response_second_indicator[0][rule_obj[i]['second_indicator'].lower()]):
                            current_condition = False
                    elif rule_value_obj['condition'] == 'Cross Up':
                        if float(response_first_indicator[0][rule_obj[i]['first_indicator'].lower()]) < float(response_second_indicator[0][rule_obj[i]['second_indicator'].lower()]):
                            current_condition = False
                        if float(response_first_indicator[len(response_first_indicator) - 1][rule_obj[i]['first_indicator'].lower()]) > float(response_second_indicator[len(response_first_indicator) - 1][rule_obj[i]['second_indicator'].lower()]):
                            current_condition = False
                    elif rule_value_obj['condition'] == 'Cross Down':
                        if float(response_first_indicator[0][rule_obj[i]['first_indicator'].lower()]) > float(response_second_indicator[0][rule_obj[i]['second_indicator'].lower()]):
                            current_condition = False
                        if float(response_first_indicator[len(response_first_indicator) - 1][rule_obj[i]['first_indicator'].lower()]) < float(response_second_indicator[len(response_first_indicator) - 1][rule_obj[i]['second_indicator'].lower()]):
                            current_condition = False
                    else:
                        if float(response_first_indicator[len(response_first_indicator) - 1][rule_obj[i]['first_indicator'].lower()]) < float(response_second_indicator[len(response_first_indicator) - 1][rule_obj[i]['second_indicator'].lower()]):
                            if float(response_first_indicator[0][rule_obj[i]['first_indicator'].lower()]) < float(response_second_indicator[0][rule_obj[i]['second_indicator'].lower()]):
                                current_condition = False
                        if float(response_first_indicator[len(response_first_indicator) - 1][rule_obj[i]['first_indicator'].lower()]) > float(response_second_indicator[len(response_first_indicator) - 1][rule_obj[i]['second_indicator'].lower()]):
                            if float(response_first_indicator[0][rule_obj[i]['first_indicator'].lower()]) > float(response_second_indicator[0][rule_obj[i]['second_indicator'].lower()]):
                                current_condition = False
                    rule_condition += str(current_condition)
                    if rule_value_obj['operator'] != 'NOT_SET':
                        rule_condition += ' ' + rule_value_obj['operator'].lower() + ' '

                print(eval(rule_condition))

                if rule_condition_result:

                    success, high_price, low_price = get_price(item['value'])

                    if success:
                        _now = datetime.datetime.now()
                        if eval(rule_condition):
                            try:
                                old_alert = DashBoardAlert.objects.get(alert=alert, pair_name=item['value'], optional_str=alert.rule)
                                old_alert.low_price = float(low_price)
                                old_alert.high_price = float(high_price)
                                old_alert.updated_at = _now
                                old_alert.save()

                                if old_alert.low_price != float(low_price) or old_alert.high_price != float(high_price):
                                    send_notification(alert, old_alert.optional_str, item['value'])

                            except Exception as e:
                                print(e, "Create a new Dashboard Alert")
                                new_dashboard_alert = DashBoardAlert()
                                new_dashboard_alert.alert = alert
                                new_dashboard_alert.pair_name = item['value']
                                new_dashboard_alert.low_price = float(low_price)
                                new_dashboard_alert.high_price = float(high_price)
                                new_dashboard_alert.optional_str = alert.rule
                                new_dashboard_alert.created_at = _now
                                new_dashboard_alert.updated_at = _now
    
                                new_dashboard_alert.save()

                                send_notification(alert, alert.rule, item['value'])

                        min_max_value = MinMaxPrice.objects.get(alert=alert, symbol=item['value'])
                        if float(high_price) > min_max_value.max_price_week:
                            try:
                                high_week = DashBoardAlert.objects.get(alert__owner=alert.owner, pair_name=item['value'], optional_str='High in week')
                                high_week.alert = alert
                                high_week.pair_name = item['value']
                                high_week.high_price = float(high_price)
                                high_week.low_price = float(low_price)
                                high_week.updated_at = _now
                                high_week.save()

                                min_max_value.max_price_week = float(high_price)

                                send_notification(alert, 'High in week', item['value'])
                            except Exception as e:
                                print(e)
                                new_high_week = DashBoardAlert()
                                new_high_week.alert = alert
                                new_high_week.pair_name = item['value']
                                new_high_week.high_price = float(high_price)
                                new_high_week.low_price = float(low_price)
                                new_high_week.created_at = _now
                                new_high_week.updated_at = _now
                                new_high_week.optional_str = 'High in week'
                                new_high_week.save()

                                min_max_value.max_price_week = float(high_price)

                                send_notification(alert, 'High in week', item['value'])
                        if float(low_price) < min_max_value.min_price_week:
                            try:
                                low_week = DashBoardAlert.objects.get(alert__owner=alert.owner, pair_name=item['value'], optional_str='Low in week')
                                low_week.alert = alert
                                low_week.pair_name = item['value']
                                low_week.high_price = float(high_price)
                                low_week.low_price = float(low_price)
                                low_week.updated_at = _now
                                low_week.save()

                                min_max_value.min_price_week = float(low_price)

                                send_notification(alert, 'Low in week', item['value'])
                            except Exception as e:
                                print(e)
                                new_low_week = DashBoardAlert()
                                new_low_week.alert = alert
                                new_low_week.pair_name = item['value']
                                new_low_week.high_price = float(high_price)
                                new_low_week.low_price = float(low_price)
                                new_low_week.created_at = _now
                                new_low_week.updated_at = _now
                                new_low_week.optional_str = 'Low in week'
                                new_low_week.save()

                                min_max_value.min_price_week = float(low_price)

                                send_notification(alert, 'Low in week', item['value'])
                        if float(high_price) > min_max_value.max_price_month:
                            try:
                                high_month = DashBoardAlert.objects.get(alert__owner=alert.owner, pair_name=item['value'], optional_str='High in month')
                                high_month.alert = alert
                                high_month.pair_name = item['value']
                                high_month.high_price = high_price
                                high_month.low_price = float(low_price)
                                high_month.updated_at = _now
                                high_month.save()

                                min_max_value.max_price_month = float(high_price)

                                send_notification(alert, 'High in month', item['value'])
                            except Exception as e:
                                print(e)
                                new_high_month = DashBoardAlert()
                                new_high_month.alert = alert
                                new_high_month.pair_name = item['value']
                                new_high_month.high_price = float(high_price)
                                new_high_month.low_price = float(low_price)
                                new_high_month.created_at = _now
                                new_high_month.updated_at = _now
                                new_high_month.optional_str = 'High in month'
                                new_high_month.save()

                                min_max_value.max_price_month = float(high_price)

                                send_notification(alert, 'High in month', item['value'])

                        if float(low_price) < min_max_value.min_price_month:
                            try:
                                low_month = DashBoardAlert.objects.get(alert__owner=alert.owner, pair_name=item['value'], optional_str='Low in month')
                                low_month.alert = alert
                                low_month.pair_name = item['value']
                                low_month.high_price = float(high_price)
                                low_month.low_price = float(low_price)
                                low_month.updated_at = _now
                                low_month.save()

                                min_max_value.min_price_month = float(low_price)

                                send_notification(alert, 'Low in month', item['value'])
                            except Exception as e:
                                print(e)
                                new_low_month = DashBoardAlert()
                                new_low_month.alert = alert
                                new_low_month.pair_name = item['value']
                                new_low_month.high_price = float(high_price)
                                new_low_month.low_price = float(low_price)
                                new_low_month.created_at = _now
                                new_low_month.updated_at = _now
                                new_low_month.optional_str = 'Low in month'
                                new_low_month.save()

                                min_max_value.min_price_month = float(low_price)

                                send_notification(alert, 'Low in month', item['value'])

            except Exception as e:
                print(e)

    else:
        print("no symbols")

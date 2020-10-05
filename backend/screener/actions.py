import datetime
import json
import requests

from backend.settings import MEDIA_ROOT
from screener.models import DashBoardScreener


def model_to_json(screener):
    return {
        'id': screener.id,
        'name': screener.name,
        'security_type': screener.security_type,
        'exchange': screener.exchange,
        'base_pair': screener.base_pair,
        'rule': screener.rule,
        'parameters': screener.parameters,
        'is_active': screener.is_active,
        'created_at': screener.created_at.strftime('%m/%d/%Y %H:%M'),
        'updated_at': screener.updated_at.strftime('%m/%d/%Y %H:%M'),
        'owner': screener.owner.username
    }


def get_dashboard_screener_json(dashboard_screener):
    if dashboard_screener.initial_price == 0:
        price_change = 0
    else:
        price_change = ((dashboard_screener.current_price - dashboard_screener.initial_price) / dashboard_screener.initial_price) * 100
    if price_change >= 0:
        price_direction = 'plus'
    else:
        price_direction = 'minus'

    dif_date = datetime.datetime.now() - dashboard_screener.created_at

    return {
        'id': dashboard_screener.id,
        'screener_name': dashboard_screener.screener.name,
        'exchange': dashboard_screener.screener.exchange,
        'pair_name': dashboard_screener.pair_name,
        'price': dashboard_screener.current_price,
        'price_change': round(abs(price_change), 4),
        'price_direction': price_direction,
        'listed_when': str(dif_date).split('.')[0]
    }


def get_rule_obj(rule):
    rule_array_tmp = rule.split(" ")
    rule_array = []
    rule_dict = []
    cross_state = False
    for item in rule_array_tmp:
        if item == 'Cross':
            cross_state = True
        else:
            if cross_state:
                rule_array.append('Cross ' + item)
            else:
                rule_array.append(item)
            cross_state = False

    rule_array.append('NOT_SET')
    for i in range(0, len(rule_array) - 1, 4):
        tmp_dict = {
            'first_indicator': rule_array[i],
            'condition': rule_array[i + 1],
            'second_indicator': rule_array[i + 2],
            'operator': rule_array[i + 3]
        }
        rule_dict.append(tmp_dict)
    return rule_dict


def get_price(symbol):
    try:
        url = 'https://api.twelvedata.com/price?symbol=' + symbol + '&apikey=' + '365d64328b304bdcafd61695a2557c8f'
        print(url)
        response = requests.request('GET', url)
        price_json = response.json()
        return price_json['price']
    except Exception as e:
        print(e)
        return False


def update_dashboard_screener(screener):
    if not screener.is_active:
        return

    with open(MEDIA_ROOT + 'Symbols.json') as f:
        data = f.read()
        data = json.loads(data)
    token = '365d64328b304bdcafd61695a2557c8f'
    base_url = 'https://api.twelvedata.com/INDICATORNAME?symbol=SYMBOLNAME'

    rule_obj = get_rule_obj(screener.rule)
    parameter_obj = json.loads(screener.parameters)
    output_dict = [x for x in data if x['SecType'] == screener.security_type and x['Exchange'] == screener.exchange and x['BasePair'] == screener.base_pair]

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
                    url = base_url.replace('INDICATORNAME', rule_value_obj['first_indicator'].lower()).replace('SYMBOLNAME', item['Pair'])
                    url += param_argument
                    url += '&interval=' + time_frame[0]['value'] + '&apikey=' + token

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

                    url = base_url.replace('INDICATORNAME', rule_value_obj['second_indicator'].lower()).replace('SYMBOLNAME', item['Pair'])
                    url += param_argument
                    url += '&interval=' + time_frame[0]['value'] + '&apikey=' + token

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

                if eval(rule_condition) and rule_condition_result:

                    price = get_price(item['Pair'])

                    if price:
                        _now = datetime.datetime.now()
                        try:
                            old_screener = DashBoardScreener.objects.get(screener=screener, pair_name=item['Pair'])
                            old_screener.current_price = float(price)
                            old_screener.updated_at = _now
                            old_screener.save()
                        except Exception as e:
                            print(e)
                            new_dashboard_screener = DashBoardScreener()
                            new_dashboard_screener.screener = screener
                            new_dashboard_screener.pair_name = item['Pair']
                            new_dashboard_screener.initial_price = float(price)
                            new_dashboard_screener.current_price = float(price)
                            new_dashboard_screener.created_at = _now
                            new_dashboard_screener.updated_at = _now

                            new_dashboard_screener.save()
                else:
                    try:
                        DashBoardScreener.objects.get(screener=screener, pair_name=item['Pair']).delete()
                    except Exception as e:
                        print("delete old screener: ", e)
            except Exception as e:
                print(e)

    else:
        print("no symbols")


def update_price_action(screener):
    try:
        price = get_price(screener.pair_name)

        if price:
            _now = datetime.datetime.now()
            screener.current_price = float(price)
            screener.updated_at = _now
            screener.save()
    except Exception as e:
        print(e)


def delete_dashboard_screener(screener):
    DashBoardScreener.objects.filter(screener=screener).delete()

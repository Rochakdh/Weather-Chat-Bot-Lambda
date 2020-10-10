import json
import logging
import requests
import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def dt(u):
    return datetime.datetime.utcfromtimestamp(u).date()  # dt(1602461041).date()--->date yyyy-mm-dd


def dt_time(u):
    utc = datetime.datetime.utcfromtimestamp(u)
    local = datetime.datetime.utcfromtimestamp(u) + datetime.timedelta(hours=5, minutes=45)
    return local.time()


def get_seventh_days():
    x = datetime.datetime.now() + datetime.timedelta(days=7)
    return x.date()


def get_celcius(temp):
    return round(temp - 273)


def get_lat_long(city):
    location = {}
    PARAMS = {
        'key': config('key'),
        'format': 'json',
        'q': city
    }
    URLS = 'https://us1.locationiq.com/v1/search.php'
    response = requests.get(url=URLS, params=PARAMS).json()
    lat = response[0]['lat']
    lon = response[0]['lon']
    display_name = response[0]['display_name']
    location['lat'] = lat
    location['lon'] = lon
    location['display_name'] = display_name
    return location


def captured_date_to_date_obj(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


def check_date_data_exist(date):
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    if date_obj == datetime.datetime.now().date():
        return True
    if date_obj > datetime.datetime.now().date() and date_obj < get_seventh_days():
        return True
    else:
        return False


def lambda_handler(event, context):
    logger.debug(event)
    date_captured = event['currentIntent']['slots'].get('Date')
    weather_available = check_date_data_exist(date_captured)
    if weather_available:
        location_captured = event['currentIntent']['slots'].get('Location')
        try:
            geolocation = get_lat_long(location_captured)
        except:
            return {
                "sessionAttributes": event["sessionAttributes"],
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Failed",
                    "message": {
                        "contentType": "PlainText",
                        "content": "Sorry No city Found",
                    }
                }
            }

        # print(event)
        PARAMS = {
            'lat': geolocation['lat'],
            'lon': geolocation['lon'],
            'exclude': '',
            'appid': config('api_key')
        }
        URLS = 'https://api.openweathermap.org/data/2.5/onecall'
        response = requests.get(url=URLS, params=PARAMS).json()
        place_description = geolocation.get('display_name').split(',')[-1]
        for each in response["daily"]:
            if dt(each['dt']) == datetime.datetime.strptime(date_captured, '%Y-%m-%d').date():
                content = each['weather'][0].get('description')
                sunrise = dt_time(each['sunrise'])
                sunset = dt_time(each['sunset'])
                min_temp = get_celcius((each['temp']['min']))
                max_temp = get_celcius(each['temp']['max'])
                pressure = each['pressure']
                return {
                    "sessionAttributes": event["sessionAttributes"],
                    "dialogAction": {
                        "type": "Close",
                        "fulfillmentState": "Fulfilled",
                        "message": {
                            "contentType": "PlainText",
                            "content": f'Country : {place_description},'
                                       f'Weather : {content},'
                                       f'Sunries : {sunrise},'
                                       f'Sunset: {sunset},'
                                       f'Minimum Temperature:{min_temp}C,'
                                       f'Maximum Temperature: {max_temp}C,'
                                       f'Pressure :{pressure}mm of Hg,'
                        }
                    }
                }

    else:
        # TODO: write code...
        return {
            "sessionAttributes": event["sessionAttributes"],
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Failed",
                "message": {
                    "contentType": "PlainText",
                    "content": "Sorry We have information of next seven days only",
                }
            }
        }
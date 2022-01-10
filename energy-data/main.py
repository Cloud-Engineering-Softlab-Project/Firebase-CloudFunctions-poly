import datetime
import time
from firebase_admin import firestore, initialize_app

times = {}

start = time.time()

# Initialize Firestore DB
initialize_app()
db = firestore.client()

end = time.time()
times['db'] = end - start

def measure_time(func):
    def wrap(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        times[func.__name__] = end - start
        # print(func.__name__, end - start)
        return result

    return wrap

@measure_time
def query_energy_data(zone_code: [int], date_from: str, duration: int, join: bool, light: bool) -> [dict]:

    # Initialize dicts which will be used for join
    reference_zones = {}
    resolution_codes = {}

    # Refactor DateTimes from string to date object and calculate the "date_to"
    date_from = datetime.datetime.strptime(date_from, '%d-%m-%Y')
    date_to = date_from + datetime.timedelta(days=duration)

    # Query Data from Firestore
    data_ref = db.collection(u'total_load_data')
    query = data_ref \
        .where(u'entsoeAreaReference_FK', u'in', zone_code) \
        .where(u'DateTime', u'>=', date_from) \
        .where(u'DateTime', u'<=', date_to)
    # .order_by(u'time')
    results = query.stream()

    # Join energy data with information about resolution codes and reference zones
    final = []
    for result in results:
        doc = result.to_dict()

        if join:
            # Join Reference Zone (caching technique)
            zone_code = doc['entsoeAreaReference_FK']
            if zone_code not in reference_zones.keys():
                ref_zone_doc = db.collection('reference-zones').document(str(zone_code)).get().to_dict()
                reference_zones[zone_code] = ref_zone_doc
            doc['ReferenceZoneInfo'] = reference_zones[zone_code]

            # Join Resolution Codes (caching technique)
            resolution_code = doc['ResolutionCode_FK']
            if resolution_code not in resolution_codes.keys():
                res_code_doc = db.collection('resolution_codes').document(
                    str(resolution_code)).get().to_dict()
                resolution_codes[resolution_code] = res_code_doc
            doc['ResolutionCodeInfo'] = resolution_codes[resolution_code]

        if light:
            keys = ['TotalLoadValue',
                    'DateTime',
                    'ResolutionCode_FK',
                    'ResolutionCodeInfo',
                    'entsoeAreaReference_FK',
                    'ReferenceZoneInfo']
            doc = {k: v for k, v in doc.items() if k in keys}

        final.append(doc)

    return final

@measure_time
def energy_data(request):

    if request.method == 'POST':

        # Get parameters
        payload = request.get_json()
        zone_codes = payload['zone_codes']
        date_from = payload['date_from']
        duration = payload['duration']
        join = payload['join']
        light = payload['light']

        # Get data
        data = query_energy_data(zone_codes, date_from, duration, join, light)

        # Make them JSON serializable
        for i in range(len(data)):
            doc = data[i]

            # Refactor datetime from str to date-objects
            datetime_keys = ['EntityCreatedAt', 'EntityModifiedAt', 'DateTime', 'UpdateTime']
            for key in datetime_keys:
                if key in doc.keys():
                    data[i][key] = str(doc[key])

            if payload['join']:
                data[i]['ReferenceZoneInfo']['AreaRefAddedOn'] = str(doc['ReferenceZoneInfo']['AreaRefAddedOn'])
                data[i]['ResolutionCodeInfo']['EntityCreatedAt'] = str(doc['ResolutionCodeInfo']['EntityCreatedAt'])
                data[i]['ResolutionCodeInfo']['EntityModifiedAt'] = str(doc['ResolutionCodeInfo']['EntityModifiedAt'])

        return {
            'times': times,
            'parameters': payload,
            'len_of_data': len(data),
            'data': data
        }

    if request.method == 'GET':

        # Get query parameters
        zone_code = request.args.get('zone_code', default=None, type=str)
        date_from = request.args.get('date_from', default='01-10-2020', type=str)
        duration = request.args.get('duration', default='10', type=str)

        if zone_code is None:
            return "Zone Code needed.", 400

        # Get data
        data = query_energy_data([int(zone_code)], date_from, int(duration), False, True)

        # Make them JSON serializable
        for i in range(len(data)):
            doc = data[i]

            # Refactor datetime from str to date-objects
            datetime_keys = ['EntityCreatedAt', 'EntityModifiedAt', 'DateTime', 'UpdateTime']
            for key in datetime_keys:
                if key in doc.keys():
                    data[i][key] = str(doc[key])

        return {
            'times': times,
            'parameters': {
                'zone_code': zone_code,
                'date_from': date_from,
                'duration': duration
            },
            'len_of_data': len(data),
            'data': data
        }

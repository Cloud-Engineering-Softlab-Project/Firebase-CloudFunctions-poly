import datetime
import time
from random import randrange
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
def query_ref_zones(time_added: str, country_fk: str, ref_zone_id: str) -> [dict]:

    # Refactor DateTimes from string to date object
    if time_added:
        time_added_obj = datetime.datetime.strptime(time_added, '%d-%m-%Y')

    country_fk = country_fk = int(country_fk) if country_fk else None

    # Get ref_zone with specific ID
    if ref_zone_id:
        doc_dict = db.collection(u'reference_zones').document(ref_zone_id).get().to_dict()
        return [doc_dict]

    # Query ref zones which they are added later than the  "time_added"
    elif time_added:
        data_ref = db.collection(u'reference_zones')
        query = data_ref \
            .where(u'Country_FK', u'==', country_fk) \
            .where(u'AreaRefAddedOn', u'>=', time_added_obj)

        results = query.stream()

    # Query ref zones with only Country_FK
    else:
        data_ref = db.collection(u'reference_zones')
        query = data_ref \
            .where(u'Country_FK', u'==', country_fk)

        results = query.stream()

    final = []
    for result in results:
        doc = result.to_dict()
        final.append(doc)

    return final

@measure_time
def ref_zones(request):
    
    if request.method == 'GET':

        # Get query parameters
        time_added = request.args.get('time_added', default=None, type=str)
        country_fk = request.args.get('country_fk', default=None, type=str)
        ref_zone_id = request.args.get('ref_zone_id', default=None, type=str)

        # Get data
        data = query_ref_zones(time_added, country_fk, ref_zone_id)

        # Make them JSON serializable
        for i in range(len(data)):
            doc = data[i]

            # Refactor datetime from str to date-objects
            datetime_keys = ['AreaRefAddedOn']
            for key in datetime_keys:
                if key in doc.keys():
                    data[i][key] = str(doc[key])

        return {
            'times': times,
            'len_of_data': len(data),
            'data': data
        }

    if request.method == 'POST':

        # Get query parameters
        ref_zone_id = request.args.get('ref_zone_id', default=None, type=str)

        # Generate ref_zone_id
        if ref_zone_id is None:
            ref_zone_id = str(randrange(410, 1000))

        # Check ID
        doc = db.collection('reference_zones').document(ref_zone_id).get()
        if doc.exists:
            return f"Reference Zone with ID {ref_zone_id} already exists.", 400

        # Write dummy document
        else:
            new_doc = {
                "AreaRefAbbrev": "GREEK TESTING",
                "Country_FK": randrange(50, 100),
                "Id": int(ref_zone_id),
                "eicFunctionName_FK": None,
                "AreaTypeCode_FK": randrange(0, 100),
                "AreaRefAddedOn": datetime.datetime.now(),
                "MapCode_FK": randrange(0, 100),
                "AreaRefName": "[NEW] /GREEK",
                "AreaCode_eic_FK": None
            }
            db.collection('reference_zones').document(ref_zone_id).set(new_doc)

            return {
                "times": times,
                "ref_zone_id": ref_zone_id
            }

    if request.method == 'DELETE':

        # Get query parameters
        ref_zone_id = request.args.get('ref_zone_id', default=None, type=str)

        # Generate ref_zone_id
        if ref_zone_id is None:
            ref_zone_id = str(randrange(100, 1000))

        # Check ID
        doc = db.collection('reference_zones').document(ref_zone_id).get()
        if not doc.exists:
            return f"Reference Zone with ID {ref_zone_id} does not exist.", 400
        else:
            if doc.to_dict()['AreaRefAbbrev'] != "GREEK TESTING":
                return f"Reference Zone with ID {ref_zone_id} cannot be deleted.", 400

        # Delete document
        db.collection('reference_zones').document(ref_zone_id).delete()

        return {
            "times": times,
            "ref_zone_id": ref_zone_id
        }

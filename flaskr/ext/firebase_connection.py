import re
import locale
from datetime import datetime, date, time
from firebase_admin import credentials, firestore, initialize_app
from babel.dates import format_date, parse_date
import json

class FireBase:
    def __init__(self, certificate_path:str=''):
        # Initialize Firebase
        self.cred = credentials.Certificate(certificate_path)
        initialize_app(self.cred)

        # Get a reference to the Firestore database
        self.db = firestore.client()
        return

    def convert_to_date(self, date_text):
        # Remove day name from date string
        date_text = re.sub(r'.*, ', '', date_text).strip()
        month_encode = {"Januari": "January", "Februari": "February", "Maret": "March", "April": "April", "Mei": "May", "Juni": "June", "Juli": "July", "Agustus": "August", "September": "September", "Oktober": "October", "November": "November", "Desember": "December"}
        date_arr = date_text.split(" ")
        date_arr[1] = month_encode[date_arr[1]]
        # Set locale to read Indonesion Month
        # locale.setlocale(category=locale.LC_ALL, locale="id_ID.UTF-8")
        date_obj = datetime.strptime(" ".join(date_arr), "%d %B %Y").date()

        return date_obj

    def get_data(self, user_id):
        data = {'user_id': user_id}
        
        # Data From Diary
        diary_ref = self.db.collection(user_id+'_diary')
        diary_data = None

        latest_date = datetime.strptime('1997-1-1', '%Y-%m-%d').date()

        for i, diary in enumerate(diary_ref.stream()):
            if(i == 0):
                diary_data = diary.to_dict()
                latest_date = self.convert_to_date(diary.to_dict()['diaryDate'])
            if(self.convert_to_date(diary.to_dict()['diaryDate']) <= latest_date):
                old_diary = diary.to_dict()
                for key in diary_data:
                    diary_data[key] = diary_data[key] if diary_data[key] != None else old_diary[key]
            else:
                new_diary = diary.to_dict()
                for key in diary_data:
                    diary_data[key] = new_diary[key] if new_diary[key] != None else diary_data[key]

                latest_date = self.convert_to_date(diary.to_dict()['diaryDate'])

        if (diary_data != None):
            data['latest_diary_date'] = latest_date.strftime('%Y-%m-%d')
            data['activities'] = diary_data.get('activities', None)
            data['body_metrics'] = diary_data.get('bodyMetrics', None)
            data['consumptions'] = diary_data.get('consumptions', None)
            data['symptoms'] = diary_data.get('symptoms', None)

        # Data From Profile
        user_data = self.db.collection('user').document(user_id).get()
        if user_data.exists:
            user_data = user_data.to_dict()
        else:
            user_data = {}

        data['birth_date'] = user_data.get('birth_date', None)
        data['have_smoked'] = user_data.get('haveSmoked', None)
        data['have_smoked_ecigarette'] = user_data.get('haveSmokedECigarette', None)
        data['sleep_time'] = user_data.get('sleepTime', None)
        data['wake_time'] = user_data.get('wakeTime', None)

        data_json = json.dumps(data)

        return data_json
    
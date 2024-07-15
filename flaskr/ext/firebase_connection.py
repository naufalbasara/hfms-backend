import re
import locale
from datetime import datetime, date, time, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from babel.dates import format_date, parse_date
import json

class FireBase:
    def __init__(self, certificate_path:str=''):
        # Initialize Firebase
        if not firebase_admin._apps:
            self.cred = credentials.Certificate(certificate_path) 
            initialize_app(self.cred)

        # Get a reference to the Firestore database
        self.db = firestore.client()
        return

    def convert_to_date(self, date_text):
        # Remove day name from date string
        date_text = re.sub(r'.*, ', '', date_text).strip()
        month_encode = {"Januari": "1", "Februari": "2", "Maret": "3", "April": "4", "Mei": "5", "Juni": "6", "Juli": "7", "Agustus": "8", "September": "9", "Oktober": "10", "November": "11", "Desember": "12"}
        date_arr = date_text.split(" ")
        date_arr[1] = month_encode[date_arr[1]]
        date_obj = datetime.strptime(" ".join(date_arr), "%d %m %Y").date()

        return date_obj

    def extract_diary(self, diary_ref):
        body_height_list = {}
        body_weight_list = {}
        bmi_list = {}
        symptoms_list = {}
        diastolic_list = {}
        systolic_list = {}
        activities_list = {}
        consumptions_list = {}

        for i, diary in enumerate(diary_ref.stream()):
            diary_data = diary.to_dict()
            date = self.convert_to_date(diary_data['diaryDate'])
            activities = diary_data.get('activities')
            body_metrics = diary_data.get('bodyMetrics', None)
            consumptions = diary_data.get('consumptions', None)
            symptoms = diary_data.get('symptoms', None)

            try:
                body_height = body_metrics.get('bodyHeight')
            except:
                body_height = None
            try:
                body_weight = body_metrics.get('bodyWeight')
            except:
                body_weight = None
            try:
                bmi = body_metrics.get('bmi')
            except:
                bmi = None
            try:
                diastolic = body_metrics.get('diastolicPressure')
            except:
                diastolic = None
            try:
                systolic = body_metrics.get('systolicPressure')
            except:
                systolic = None
            
            body_height_list[date] = body_height
            body_weight_list[date] = body_weight
            bmi_list[date] = bmi
            symptoms_list[date] = symptoms
            diastolic_list[date] = diastolic
            systolic_list[date] = systolic
            activities_list[date] = activities
            consumptions_list[date] = consumptions

        body_height_list = dict(sorted(body_height_list.items()))
        body_weight_list = dict(sorted(body_weight_list.items()))
        bmi_list = dict(sorted(bmi_list.items()))
        symptoms_list = dict(sorted(symptoms_list.items()))
        diastolic_list = dict(sorted(diastolic_list.items()))
        systolic_list = dict(sorted(systolic_list.items()))
        activities_list = dict(sorted(activities_list.items()))
        consumptions_list = dict(sorted(consumptions_list.items()))

        return {
            'body_height_list' : body_height_list,
            'body_weight_list' : body_weight_list,
            'bmi_list' : bmi_list,
            'symptoms_list' : symptoms_list,
            'diastolic_list' : diastolic_list,
            'systolic_list' : systolic_list,
            'activities_list' : activities_list,
            'consumptions_list' : consumptions_list
        }

    def get_data(self, user_id, data_window=60):
        data = {'user_id': user_id}
        
        # Data From Diary
        diary_ref = self.db.collection(user_id+'_diary')
        
        extracted_diary = self.extract_diary(diary_ref)
        
        body_height_list = extracted_diary.get('body_height_list')
        body_weight_list = extracted_diary.get('body_weight_list')
        bmi_list = extracted_diary.get('bmi_list')
        diastolic_list = extracted_diary.get('diastolic_list')
        systolic_list = extracted_diary.get('systolic_list')
        symptoms_list = extracted_diary.get('symptoms_list')
        activities_list = extracted_diary.get('activities_list')
        consumptions_list = extracted_diary.get('consumptions_list')

        # Get latest available data of weight, height, bmi, diastolic, and systolic pressure
        data['body_weight'] = None
        for val in body_weight_list.values():
            if(val != None):
                data['body_weight'] = val
        data['body_height'] = None
        for val in body_height_list.values():
            if(val != None):
                data['body_height'] = val
        data['bmi'] = None
        for val in bmi_list.values():
            if(val != None):
                data['bmi'] = val
        data['diastolic_pressure'] = None
        for val in diastolic_list.values():
            if(val != None):
                data['diastolic_pressure'] = val
        data['systolic_pressure'] = None
        for val in systolic_list.values():
            if(val != None):
                data['systolic_pressure'] = val
        
        today = date.today()
        start_date = date.today() - timedelta(days=data_window)
        end_date = date.today()

        data['symptoms'] = []
        data['activities'] = []
        data['consumptions'] = []
        while (start_date <= end_date):
            data['symptoms'].append(symptoms_list.get(start_date))
            data['activities'].append(activities_list.get(start_date))
            data['consumptions'].append(consumptions_list.get(start_date))
            start_date = start_date + timedelta(days=1)

        # Data From Profile
        user_data = self.db.collection('user').document(user_id).get()
        if user_data.exists:
            user_data = user_data.to_dict()
        else:
            user_data = {}

        data['birth_date'] = user_data.get('birthDate', None)
        data['have_smoked'] = user_data.get('haveSmoked', None)
        data['have_smoked_ecigarette'] = user_data.get('haveSmokedECigarette', None)
        data['sleep_time'] = user_data.get('sleepTime', None)
        data['wake_time'] = user_data.get('wakeTime', None)
        
        try:
            if(data['body_height'] == None):
                data['body_height'] = user_data.get('bodyHeight', None)
        except:
            pass

        return data
    
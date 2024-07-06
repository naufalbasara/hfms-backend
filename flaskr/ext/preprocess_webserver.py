from ext.food_data_central import FoodCentral

import json, re, random, math
from datetime import datetime, date
from googletrans import Translator

class PreProcess:
    def __init__(self, fdc_api='uHxCRFHwKEClBTQ06pMHGfks3I7wr0seMxCSO76Q'):
        self.translator = Translator()
        self.food_central = FoodCentral(api_key=fdc_api)

        random.seed(37)

        return

    def translate(self, name, src='id', dest='en'):
        try:
            translated = self.translator.translate(name, src=src, dest=dest)
            return translated.text
        except:
            return name

    def get_age(self, birth_date_str):
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%M-%d").date()
            today = date.today()

            age = today.year - birth_date.year
            # Adjust for the case where the birth date hasn't occurred yet this year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            return age
        except:
            return None

    def timestamp_to_int(self, time_string):
        try:
            time_obj = datetime.strptime(time_string, "%H:%M")
            return time_obj.hour * 60 + time_obj.minute
        except:
            return None

    def get_sleep_duration(self, sleep_time_string, wake_time_string):
        sleep_time = self.timestamp_to_int(sleep_time_string)
        wake_time = self.timestamp_to_int(wake_time_string)

        if(sleep_time > wake_time):
            wake_time += (24*60) # Add 24 hour to wake time to calculate sleep duraton
        
        return wake_time - sleep_time

    def get_portion(self, portion_string):
        portion = re.search(r'\b\d+\b', portion_string)
        if portion:
            return portion.group()
        else:
            return 0

    def get_nutrient_value(self, nutrients, nutrient_name, nutrient_name_simple):
        try:
            nutrient = nutrients[nutrient_name]

            # Standardize Metrics of Measurement for each nutrients
            if nutrient_name_simple in ['energy']:
                if(nutrient['unitName'] == "KCAL"):
                    multiplier = 1
                elif(nutrient['unitName'] == "kJ"):
                    multiplier = 0.239006
                else:
                    multiplier = 0
            if nutrient_name_simple in ['protein', 'carbohydrate', 'sugars', 'fiber', 'fat', 'saturated_fatty_acid', 'monounsaturated_fatty_acid', 'polyunsaturated_fatty_acid']:
                if(nutrient['unitName'] == "G"):
                    multiplier = 1
                elif(nutrient['unitName'] == "MG"):
                    multiplier = 1000
                elif(nutrient['unitName'] == "KG"):
                    multiplier = 0.001
                else:
                    multiplier = 0
            if nutrient_name_simple in ['cholesterol', 'calcium']:
                if(nutrient['unitName'] == "G"):
                    multiplier = 0.001
                elif(nutrient['unitName'] == "MG"):
                    multiplier = 1
                elif(nutrient['unitName'] == "KG"):
                    multiplier = 0.000001
                else:
                    multiplier = 0
            
            return nutrient['value'] * multiplier

        except:
            return 0

    def get_nutrient_summary(self, food_name, num_samples=30):
        # First Iteration: Check Food Name from Foundation type
        try:
            nutrients, num_hits = self.food_central.get_nutrients(food_name, data_type=['Foundation'])
            if(num_hits > 0):
                return nutrients[0]
        except:
            pass
        
        # Second Iteration: Check Food Name from Branded type, sample 30 hit
        try:
            nutrients, num_hits = self.food_central.get_nutrients(food_name, data_type=['Branded'])
            if(num_hits > 0):
                nutrient = nutrients[0]
                for i, val in enumerate(random.sample(nutrients, min(num_samples, num_hits))):
                    if(i == 0):
                        continue
                    
                    list_of_key = list(set(nutrient['foodNutrients'])+set(val['foodNutrients']))
                    for key in list_of_key:
                        nutrient['foodNutrients'][key] = nutrient['foodNutrients'].get(key, 0) + val['foodNutrients'].get(key, 0)
                    
                return nutrient
        except:
            pass

        # Second B Iteration: Check Food Name from Survey Food type, sample 30 hit
        try:
            nutrients, num_hits = self.food_central.get_nutrients(food_name, data_type=['Survey (FNDDS)'])
            if(num_hits > 0):
                nutrient = nutrients[0]
                for i, val in enumerate(random.sample(nutrients, min(num_samples, num_hits))):
                    if(i == 0):
                        continue
                    
                    list_of_key = list(set(nutrient['foodNutrients'])+set(val['foodNutrients']))
                    for key in list_of_key:
                        nutrient['foodNutrients'][key] = nutrient['foodNutrients'].get(key, 0) + val['foodNutrients'].get(key, 0)
                    
                return nutrient
        except:
            pass
        
        # Third Iteration: Check Food Name from Foundation type, by individual words (get the fewest non zero hit)
        try:
            fewest_hit = 1e8
            nutrients = None
            for i, word in enumerate(food_name.split(' ')):
                # Limit to the first 3 words to search individually
                if(i >= 3):
                    break
                nutrients_temp, num_hits = self.food_central.get_nutrients(word, data_type=['Foundation'])

                if (num_hits > 2e4):
                    break
                if(num_hits < fewest_hit and num_hits != 0):
                    nutrients = nutrients_temp
                    fewest_hit = num_hits
            
            if(nutrients != None):
                return nutrients[0]
        except:
            pass

        # Fourth Iteration: Check Food Name from Branded type, by individual words (get the fewest non zero hit)
        try:
            fewest_hit = 1e8
            nutrients = None
            for i, word in enumerate(food_name.split(' ')):
                # Limit to the first 3 words to search individually
                if(i >= 3):
                    break
                nutrients_temp, num_hits = self.food_central.get_nutrients(word, data_type=['Branded'])

                if (num_hits > 2e4):
                    break
                
                if(num_hits < fewest_hit and num_hits != 0):
                    nutrients = nutrients_temp
                    fewest_hit = num_hits

            if(nutrients != None):
                nutrient = nutrients[0]
                for i, val in enumerate(random.sample(nutrients, min(num_samples, num_hits))):
                    if(i == 0):
                        continue
                    
                    list_of_key = list(set(nutrient['foodNutrients'])+set(val['foodNutrients']))
                    for key in list_of_key:
                        nutrient['foodNutrients'][key] = nutrient['foodNutrients'].get(key, 0) + val['foodNutrients'].get(key, 0)
                    
                return nutrient
        except:
            pass
        
        return {'status': 400, 'totalHits': 0}

    def get_consumption_detail(self, consumptions, additional_mapping):
        
        if(len(consumptions) == 0):
            total_detail = {
                'energy': None,
                'protein': None,
                'carbohydrate': None,
                'sugars': None,
                'fiber': None,
                'fat': None,
                'saturated_fatty_acid': None,
                'monounsaturated_fatty_acid': None,
                'polyunsaturated_fatty_acid': None,
                'cholesterol': None,
                'calcium': None
            }
            return total_detail

        total_detail = {
            'energy': 0,
            'protein': 0,
            'carbohydrate': 0,
            'sugars': 0,
            'fiber': 0,
            'fat': 0,
            'saturated_fatty_acid': 0,
            'monounsaturated_fatty_acid': 0,
            'polyunsaturated_fatty_acid': 0,
            'cholesterol': 0,
            'calcium': 0
        }

        try:
            for consumption in consumptions:
                # Translate Food name from id to en
                food_name = self.translate(consumption['name'])

                # Hardcode to exclude water / mineral water
                if(food_name.lower() in ['water', 'mineral water']):
                    continue

                # Get Nutrient Detail From USDA Food Data Central
                nutrient = self.get_nutrient_summary(food_name)
                
                # Nutrient from FDA is for every 100 gr/ml food
                try:
                    portion_multiplier = 100/self.get_portion(consumption.get(additional_mapping['consumption_portion'], 100))
                except:
                    portion_multiplier = 1

                detail = {}
                if(nutrient['status'] == 200):
                    detail['energy'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Energy', 'energy') * portion_multiplier
                    detail['protein'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Protein', 'protein') * portion_multiplier
                    detail['carbohydrate'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Carbohydrate, by difference', 'carbohydrate') * portion_multiplier
                    detail['sugars'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Sugars, Total', 'sugars') * portion_multiplier
                    detail['fiber'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Fiber, total dietary', 'fiber') * portion_multiplier
                    detail['fat'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Total lipid (fat)', 'fat') * portion_multiplier
                    detail['saturated_fatty_acid'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Fatty acids, total saturated', 'saturated_fatty_acid') * portion_multiplier
                    detail['monounsaturated_fatty_acid'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Fatty acids, total monounsaturated', 'monounsaturated_fatty_acid') * portion_multiplier
                    detail['polyunsaturated_fatty_acid'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Fatty acids, total polyunsaturated', 'polyunsaturated_fatty_acid') * portion_multiplier
                    detail['cholesterol'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Cholesterol', 'cholesterol') * portion_multiplier
                    detail['calcium'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Calcium, Ca', 'calcium') * portion_multiplier

                    if detail['energy'] == 0:
                        energy_other = self.get_nutrient_value(nutrient['foodNutrients'], 'Energy (Atwater General Factors)', 'energy') * portion_multiplier
                        if(energy_other != 0):
                            detail['energy'] = energy_other

                # Update total nutrients
                print(consumption['name'], detail)
                for key in total_detail:
                    if key in detail:
                        total_detail[key] += detail[key]
        except Exception as e:
            print('error in cons detail', e)
            pass
        
        return total_detail

    def get_vigorous_activity_minute(self, activities, additional_mapping):
        
        total_minutes = None
        try:
            for i, activity in enumerate(activities):
                if(i == 0):
                    total_minutes = 0
                if(float(activity.get(additional_mapping['activities_heartRate'])) > 142):
                    total_minutes += float(activity.get(additional_mapping['activities_duration']))
        except Exception as er:
            pass
        
        return total_minutes
    
    def get_bmi(self, weight, height):
        if(weight == None or height == None):
            return None
        return float(weight)/((float(height)/100)**2)
    
    def is_having_pain(self, symptoms_list, additional_mapping):
        if(len(symptoms_list) == 0):
            return 9

        for symptoms in symptoms_list:
            try:
                if symptoms == additional_mapping['Pain in Chest Area']:
                        return 1
            except:
                pass
        
        return 0

    def preprocess(self, request_data):
        
        value_mapping = {
            # Desc --> 'Input name from form': 'variable used in this script'
            'Demog1_RIDAGEYR': 'birth_date',
            'Quest22_SMQ890': 'have_smoked',
            'Quest22_SMQ900': 'have_smoked_ecigarette',
            'Quest21_SLQ300': 'sleep_time',
            'Quest21_SLQ330': 'wake_time',
            'dailySymptoms': 'dailySymptoms',
            'dailyDiet': 'dailyDiet',
            'dailyActivities': 'dailyActivities',
            'Exami2_BMXWT': 'body_weight',
            'Exami2_BMXHT': 'body_height',
            'Exami1_SysPulse': 'systolic_pressure',
            'Exami1_DiaPulse': 'diastolic_pressure',
        }

        additional_mapping = {
            'consumptions_name': 'name', # form name for Food name, e.g. sop buntut
            'consumptions_portion': 'portion', # form name for Food portion (In grams), e.g. 120 
            'symptoms_name': 'name', # form name for symptoms name, e.g. Pain in Chest Area 
            'Pain in Chest Area': 'sakit dada', # Prefilled name for Pain in chest area in symptoms dropdown 
            'activities_heartRate': 'heartRate', # Form name for heart rate in activities
            'activities_duration': 'duration', # Form name for duration in activities 
        }

        # Cigarette question is binary question (yes/no), add True & False value that users input here, e.g. if users input Yes then it's True, etc.
        binary_question_mapping = {
            True: '1',
            False: '0'
        }

        data_raw = {value_mapping[key]: val for key, val in request_data.items() if key in value_mapping}
        print('data_raw', data_raw)

        age = {
            'Demog1_RIDAGEYR': self.get_age(data_raw['birth_date'])
        }
        print('age', age)

        
        smoking = {
            'Quest22_SMQ890': 1 if data_raw['have_smoked'] == binary_question_mapping[True] else 0,
            'Quest22_SMQ900': 1 if data_raw['have_smoked_ecigarette'] == binary_question_mapping[True] else 0
        }
        print('smoking', smoking)

        sleep = {
            'Quest21_SLQ3032': self.timestamp_to_int(data_raw['sleep_time']),
            # 'Quest21_SLQ330': self.timestamp_to_int(data_raw['wake_time']),
            'Quest21_SLD123': self.get_sleep_duration(data_raw['sleep_time'], data_raw['wake_time'])
        }
        print('sleep', sleep)

        symptoms = data_raw['dailySymptoms']
        symptoms = [col for col in symptoms.values()]
        if(symptoms == None):
            symptoms = []
        print(symptoms)
        pain = {
            'Quest3_CDQ008': self.is_having_pain(symptoms, additional_mapping)
        }
        print('pain', pain)

        consumption = data_raw['dailyDiet']
        consumption = [col for col in consumption.values()]
        if(consumption == None):
            consumption = []

        dietary_detail = self.get_consumption_detail(consumption, additional_mapping)
        dietary = {
            'Dieta1_DR1TKCAL': dietary_detail['energy'],
            'Dieta1_DR1TPROT': dietary_detail['protein'],
            'Dieta1_DR1TCARB': dietary_detail['carbohydrate'],
            'Dieta1_DR1TSUGR': dietary_detail['sugars'],
            'Dieta1_DR1TFIBE': dietary_detail['fiber'],
            'Dieta1_DR1TTFAT': dietary_detail['fat'],
            'Dieta1_DR1TSFAT': dietary_detail['saturated_fatty_acid'],
            'Dieta1_DR1TMFAT': dietary_detail['monounsaturated_fatty_acid'],
            'Dieta1_DR1TPFAT': dietary_detail['polyunsaturated_fatty_acid'],
            'Dieta1_DR1TCHOL': dietary_detail['cholesterol'],
            'Dieta1_DR1TCALC': dietary_detail['calcium'],
        }


        activities = data_raw['dailyActivities']
        activities = [col for col in activities.values()]
        if(activities == None):
            activities = []
        print('activities', activities)
        activity = {
            'Quest19_VigorousActivity': self.get_vigorous_activity_minute(activities, additional_mapping)
        }
        print('activity', activity)
        
        height_weight = {
            'Exami2_BMXWT': float(data_raw['body_weight']),
            'Exami2_BMXHT': float(data_raw['body_height']),
            'Exami2_BMXBMI': self.get_bmi(data_raw['body_weight'], data_raw['body_height'])
        }
        print('height weight', height_weight)

        pressure = {
            'Exami1_SysPulse': float(data_raw.get('systolic_pressure')),
            'Exami1_DiaPulse': float(data_raw.get('diastolic_pressure'))
        }
        print('pressure', pressure)

        # Rearrage Data for Model Consumption
        data = {}

        # Lifestyle
        data.update(smoking)
        data.update(sleep)
        data.update(dietary)
        data.update(activity)

        # Characteristics
        data.update(age)
        data.update(height_weight)
        data.update(pain)
        data.update(pressure)
        print(data)
        return data
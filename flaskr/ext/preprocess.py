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
        except Exception as e:
            print("googletrans error:", e)
            return name
    
    def convert_to_date(self, date_text):
        # Remove day name from date string
        date_text = re.sub(r'.*, ', '', date_text).strip()
        month_encode = {"Januari": "1", "Februari": "2", "Maret": "3", "April": "4", "Mei": "5", "Juni": "6", "Juli": "7", "Agustus": "8", "September": "9", "Oktober": "10", "November": "11", "Desember": "12",
                        "January": "1", "February": "2", "March": "3", "April": "4", "May": "5", "June": "6", "July": "7", "August": "8", "September": "9", "October": "10", "November": "11", "December": "12"}
        date_arr = date_text.split(" ")
        date_arr[1] = month_encode[date_arr[1]]
        date_obj = datetime.strptime(" ".join(date_arr), "%d %m %Y").date()

        return date_obj

    def get_age(self, birth_date_str):
        try:
            birth_date = self.convert_to_date(birth_date_str)
            today = date.today()

            age = today.year - birth_date.year
            # Adjust for the case where the birth date hasn't occurred yet this year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            return age
        except Exception as error:
            print(f'failed getting age due to: {error}')
            return None

    def timestamp_to_int(self, time_string):
        try:
            time_obj = datetime.strptime(time_string, "%I:%M %p")
            return time_obj.hour * 60 + time_obj.minute
        except:
            return None

    def get_sleep_duration(self, sleep_time_string, wake_time_string):
        sleep_time = self.timestamp_to_int(sleep_time_string)
        wake_time = self.timestamp_to_int(wake_time_string)

        if(sleep_time > wake_time):
            wake_time += (24*60) # Add 24 hour to wake time to calculate sleep duraton
        
        return (wake_time - sleep_time)/60

    def get_portion(self, portion_string):
        try:
            if(portion_string.lower() == "kecil"):
                return 50
            if(portion_string.lower() == "sedang"):
                return 100
            if(portion_string.lower() == "besar"):
                return 150
        except:
            pass

        try:
            portion = re.search(r'\b\d+\b', portion_string)
            if portion:
                return portion.group()
        except:
            pass

        return 0

    def get_nutrient_value(self, nutrients, nutrient_name, nutrient_name_simple, regex=False):
        try:
            if(regex==False):
                nutrient = nutrients[nutrient_name]
            else:
                for key in nutrients.keys():
                    if nutrient_name.lower() in key.lower():
                        nutrient = nutrients[key]
                        break

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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
            pass
        
        return {'status': 400, 'totalHits': 0}

    def get_consumption_detail(self, consumptions_list):
        
        if(len(consumptions_list) == 0):
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
        num_food = 0
        num_day = 0

        for consumptions in consumptions_list:
            if consumptions == None:
                continue
            try:
                for consumption in consumptions:
                    try:
                        with open('ext/precalculated_nutrient.json', 'r') as f:
                            precalc_nutrient = json.load(f)
                    except Exception as e:
                        print(f'=== error at precalc 1 {e} ===')
                        precalc_nutrient = {}

                    nutrient = None
                    for key, val in precalc_nutrient.items():
                        try:
                            if key.lower().strip() == consumption['name'].lower().strip():
                                nutrient = val
                        except Exception as e:
                            print(f'=== error at precalc 2 {e} ===')
                            pass

                    if(nutrient == None):
                        # Translate Food name from id to en
                        food_name = self.translate(consumption['name'])
                        food_name = re.sub(r'[,\.;&/\\]', ' ', food_name)

                        # Get Nutrient Detail From USDA Food Data Central
                        nutrient = self.get_nutrient_summary(food_name)

                    # Nutrient from FDA is for every 100 gr/ml food
                    try:
                        portion_multiplier = 100/self.get_portion(consumption['portion'])
                    except:
                        portion_multiplier = 1

                    detail = {}
                    if(nutrient['status'] == 200):
                        detail['energy'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Energy', 'energy') * portion_multiplier
                        detail['protein'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Protein', 'protein') * portion_multiplier
                        detail['carbohydrate'] = self.get_nutrient_value(nutrient['foodNutrients'], 'Carbohydrate, by difference', 'carbohydrate') * portion_multiplier
                        detail['sugars'] = self.get_nutrient_value(nutrient['foodNutrients'], 'sugars', 'sugars', regex=True) * portion_multiplier
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
                    for key in total_detail:
                        if key in detail:
                            total_detail[key] += detail[key]
                    
                    num_food += 1
                num_day += 1
            except Exception as error:
                print(f'getting nutrient details failed due to:\n\t{error}')
                pass
        
        if(num_food == 0):
            return {
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
        if(num_day != 0):
            for key in total_detail:
                total_detail[key] = total_detail[key]/num_day
        
        return total_detail

    def get_vigorous_activity_minute(self, activities_list, window_day=30):
        if(len(activities_list) < window_day):
            window_day = len(activities_list)

        total_minutes = 0
        i = 0
        try:
            for activities in activities_list[-window_day:]:
                if(activities == None):
                    continue

                # If activities is not null
                i += 1
                for activity in activities:
                    if(activity['heartRate'] > 142):
                        total_minutes += activity['duration']
        except:
            pass
        
        # to prevent division by 0
        if(i == 0):
            i = 1
        return total_minutes/i
    
    def get_bmi(self, weight, height):
        if(weight == None or height == None):
            return None
        return float(weight)/((float(height)/100)**2)
    
    def is_having_pain(self, symptoms_list, window_day=7):
        
        if(len(symptoms_list) < window_day):
            window_day = len(symptoms_list)
        
        for symptoms in symptoms_list[-window_day:]:
            try:
                for symptom in symptoms:
                    if 'Nyeri Dada' in symptom.get('symptoms'):
                        return 1
            except:
                pass
        
        return 0

    def preprocess(self, data_json):
        # Take data in json string then preprocess and output np array
        print(data_json)
        data_raw = {
            'birth_date': None, 'have_smoked': None, 'have_smoked_ecigarette': None,
            'sleep_time': None, 'wake_time': None, 'symptoms': None, 'consumptions': None,
            'activities': None, 'body_weight': None, 'body_height': None,
            'systolic_pressure': None,'diastolic_pressure': None
                    }

        for col in data_raw.keys():
            if col not in data_json:
                return None
            if data_json[col] == None:
                return None
            data_raw[col] = data_json.get(col)

        age = {
            'Demog1_RIDAGEYR': self.get_age(data_raw['birth_date'])
        }

        
        smoking = {
            'Quest22_SMQ890': 1 if data_raw['have_smoked'] else 0,
            'Quest22_SMQ900': 1 if data_raw['have_smoked_ecigarette'] else 0
        }

        sleep = {
            'Quest21_SLQ3032': self.timestamp_to_int(data_raw['sleep_time']),
            # 'Quest21_SLQ330': self.timestamp_to_int(data_raw['wake_time']),
            'Quest21_SLD123': self.get_sleep_duration(data_raw['sleep_time'], data_raw['wake_time'])
        }

        symptoms = data_raw['symptoms']
        if(symptoms == None):
            symptoms = []
        pain = {
            'Quest3_CDQ008': self.is_having_pain(symptoms)
        }

        consumption = data_raw['consumptions']
        if(consumption == None):
            consumption = []
        print('getting dietary details...')
        dietary_detail = self.get_consumption_detail(consumption)
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

        activities = data_raw['activities']
        if(activities == None):
            activities = []
        activity = {
            'Quest19_VigorousActivity': self.get_vigorous_activity_minute(activities)
        }
        
        height_weight = {
            'Exami2_BMXWT': float(data_raw['body_weight']),
            'Exami2_BMXHT': float(data_raw['body_height']),
            'Exami2_BMXBMI': self.get_bmi(data_raw['body_weight'], data_raw['body_height'])
        }

        pressure = {
            'Exami1_SysPulse': float(data_raw.get('systolic_pressure')),
            'Exami1_DiaPulse': float(data_raw.get('diastolic_pressure'))
        }

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

        return data

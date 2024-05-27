import requests

class FoodCentral:
    __base_endpoint = 'https://api.nal.usda.gov/fdc/v1/'
    __search_endpoint = __base_endpoint + 'foods/search'
    __list_endpoint = __base_endpoint + 'foods/list'

    def __init__(self, food_combination:list=[], api_key:str=''):
        self.__api_key = api_key
        self.__food_combination = food_combination
        return

    def deconstruct_food(self, food_combination):
        return

    def get_nutrients(self, keyword, data_type=['Foundation'], sort_by='publishedDate', sort_order='desc', require_all_words='true'):
        params = {
            'api_key': self.__api_key,
            'query': keyword,
            'dataType': data_type,
            'sortBy': sort_by,
            'sortOrder': sort_order,
            'requireAllWords': require_all_words
        }

        response = requests.get(self.__search_endpoint, params=params)
        
        obj_data_list = []

        for i, food in enumerate(response.json()['food']):
            num_hits = 0
            obj_data = {'rank': i}
            try:
                obj_data = {
                    'query': response.json()['foodSearchCriteria']['query'],
                    'description': food['description'],
                    'publishedDate': food['publishedDate'],
                    'foodNutrients': {},
                    'portion': {
                        'size': 100,
                        'unit': 'g'
                    },
                    'status': response.status_code
                }
                obj_data['foodNutrients'] = {}
                for nutrient in food['foodNutrients']:
                    obj_data['foodNutrients'][nutrient['nutrientName']] = {
                        'value': nutrient['value'],
                        'unitName': nutrient['unitName'],
                    }
                num_hits += 1
                obj_data_list.append(obj_data)
            except:
                pass

        return obj_data_list, num_hits
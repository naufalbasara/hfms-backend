import numpy as np, os, joblib, pandas as pd, random, sklearn, json, time
from datetime import date

class GA:
    """
    Class for genetic algorithm lifestyle recommendation, stored preprocessing pipeline and ML model to predict
    likeliness of someone having a heart failure.
    """
    def __init__(
            self,
            lifestyle_genes:dict,
            characteristic:np.ndarray,
            current_lifestyle:dict={},
            population_size:int=25,
            generations:int=30,
            mutation_probability:float=0.2,
            model_path:str='',
            scaler_path:str='',
            version:int=1,
            for_app=False
            ) -> None:
        self.__genes = lifestyle_genes
        self.__characteristic = characteristic
        self.__current_lifestyle = current_lifestyle
        self.__current_lifestyle_arr = self.__dict_to_arr(current_lifestyle)
        self.__population_size = population_size
        self.__generations = generations
        self.__mutation_probability = mutation_probability
        self.__model = joblib.load(model_path)
        self.__for_app = for_app

        # preprocess characteristic and lifestyle
        print('preprocessing')
        self.preprocess_pipeline(scaler_path)
        print('predicting')
        self.__current_risk = self.__predict(self.__current_lifestyle_arr)
        self.__best_result = self.__current_risk
        self.__version = version

    def __generate_individual(self):
        """
        Generating individual of lifestyle component in early iteration population
        """
        individual_lifestyle = {}
        individual_lifestyle_arr = []

        for current_ls in self.__current_lifestyle.keys():
            selected_value = random.choice([*self.__genes[current_ls].keys()])
            selected_value = float(selected_value) if str(selected_value) in self.__genes[current_ls] else int(selected_value)

            individual_lifestyle[current_ls] = selected_value
            individual_lifestyle_arr.append(selected_value)

        return individual_lifestyle, np.expand_dims(np.array(individual_lifestyle_arr).astype(float), axis=0)

    def __dict_to_arr(self, individual_dict:dict):
        individual_arr = []
        for ls_component, value in individual_dict.items():
            individual_arr.append(value)

        return np.expand_dims(np.array(individual_arr).astype(float), axis=0)

    def __to_interval(self, interval_str:str) -> pd.Interval:
        left_closed = interval_str.startswith('[')
        right_closed = interval_str.endswith(']')

        closed='neither'
        if left_closed:
            closed='left'
        elif right_closed:
            closed='right'
        closed = 'both' if left_closed and right_closed else closed

        try:
            left_value, right_value = [*map(float, interval_str[1:-1].split(', '))]
        except Exception as e:
            raise e

        return pd.Interval(left=left_value, right=right_value, closed=closed)

    def __discretize(self, value, column):
        for index, (encode, interval) in enumerate(sorted(self.__genes[column].items(), key=lambda x: x[0])):
            value_list = [*self.__genes[column].values()]

            try:
                interval_val = self.__to_interval(interval)
                if index == 0 and value <= interval_val.left:
                    return encode
                
                elif value in interval_val:
                    return encode
                
                elif index == len(value_list)-1:
                    return encode
                
            except:
                return value

    def __generate_populations(self) -> list:
        """
        Generating populations of lifestyle components
        Returned a list of generated individuals
        """
        populations = []
        populations.append(self.__current_lifestyle_arr)
        start = 0 if len(populations) == 0 else 1

        for _ in range(start, self.__population_size):
            _, generated_individual_arr = self.__generate_individual()
            populations.append(generated_individual_arr)

        return populations

    def preprocess_pipeline(self, scaler_file_path:str):
        ordered_lifestyle_col = [*self.__current_lifestyle.keys()]

        lifestyle=np.expand_dims(np.array([*self.__current_lifestyle.values()]), axis=0)
        characteristic = self.__characteristic

        # discretize raw value
        discreted_values = []
        for index, ls_value in enumerate(lifestyle[0]):
            try:
                discreted_value = self.__discretize(ls_value, ordered_lifestyle_col[index])
                discreted_values.append(discreted_value)
            except Exception as e:
                print(e)
                discreted_values.append(ls_value)

        lifestyle = np.expand_dims(np.array(discreted_values).astype(float), axis=0)
        for idx, col in enumerate(self.__current_lifestyle.keys()):
            self.__current_lifestyle[col] = discreted_values[idx]

        # feature scaling
        scaler = joblib.load(scaler_file_path)
        assert type(scaler) == sklearn.preprocessing.StandardScaler

        self.__characteristic = scaler.transform(characteristic)
        self.__current_lifestyle_arr = lifestyle

        for index, ls_component in enumerate(ordered_lifestyle_col):
            self.__current_lifestyle[ls_component] = self.__current_lifestyle_arr[0, index]

        return True

    def __get_whole_data(self, lifestyle:np.ndarray):
        whole_data = np.concatenate((lifestyle, self.__characteristic), axis=1).astype(float)
        # whole_data = whole_data.reshape(whole_data.shape[0], whole_data.shape[1], 1)

        return whole_data

    def get_best_lifestyle(self):
        return self.__translate_lifestyle(self.__best_lifestyle, self.__best_result), self.__best_result
    
    def __comparison(self, existing_ls:pd.Interval, recommendation_result:pd.Interval) -> str:
        if recommendation_result == existing_ls:
            return f'({recommendation_result.left}-{recommendation_result.right})'
        elif recommendation_result > existing_ls:
            return f'{">" if existing_ls.closed=="right" or existing_ls.closed=="both" else ">="} {existing_ls.right} ({recommendation_result.left}-{recommendation_result.right})'
            
        return f'{"<" if existing_ls.closed=="left" or existing_ls.closed=="both" else "<="} {existing_ls.left} ({recommendation_result.left}-{recommendation_result.right})'

    def __translate_lifestyle(self, lifestyle:np.ndarray, ls_risk:float):
        lifestyle_dict = {}
        lifestyle_dict['lifestyle'] = {}
        ls_description_path = f'optimization_model/metadata/{"app/" if self.__for_app else ""}v{self.__version}/v{self.__version}_lifestyle_description.json'
        with open(ls_description_path, 'r') as json_file:
            lifestyle_description = json.load(json_file)

        for index, ls_component in enumerate(self.__current_lifestyle.keys()):
            value = lifestyle[0][index]
            value = int(value) if str(int(value)) in self.__genes[ls_component] else float(value)
            current_ls_value = int(self.__current_lifestyle[ls_component]) if str(int(self.__current_lifestyle[ls_component])) in self.__genes[ls_component] else float(self.__current_lifestyle[ls_component])

            if type(self.__genes[ls_component][str(current_ls_value)]) == str:
                existing_ls = self.__to_interval(self.__genes[ls_component][str(current_ls_value)])
                recommendation_result = self.__to_interval(self.__genes[ls_component][str(value)])
                
                existingComparison = self.__comparison(existing_ls, recommendation_result)
            else:
                existingComparison = f'{current_ls_value} -> {value}'

            changed = self.__current_lifestyle_arr[0][index] != lifestyle[0, index]

            lifestyle_dict['lifestyle'][ls_component] = {
                'description': lifestyle_description[ls_component],
                'currentValue': self.__genes[ls_component][str(current_ls_value)],
                'recommendedValueInterval': self.__genes[ls_component][str(value)] if not (ls_component == "Quest22_SMQ890" or ls_component == "Quest22_SMQ890") else 0,
                'codeValue': str(value),
                'comparison': existingComparison,
                'changeStatus': f'{changed}'
                }
        lifestyle_dict['currentRisk'] = self.__current_risk
        lifestyle_dict['currentRiskThresh'] = round(min((self.__current_risk*0.5)/0.20375, 100), 5)
        lifestyle_dict['riskAfterRecommendation'] = ls_risk
        lifestyle_dict['riskAfterRecommendationThresh'] = round(min((ls_risk*0.5)/0.20375, 100), 5)
        lifestyle_dict['riskReduction'] = self.__current_risk - ls_risk
        lifestyle_dict['riskReductionThresh'] = lifestyle_dict['currentRiskThresh'] - lifestyle_dict['riskAfterRecommendationThresh']
        lifestyle_dict['timeGenerated'] = str(date.today())
        lifestyle_dict['timeTaken'] = f'{round(time.time() - self.__start_time, 3)}s'

        return lifestyle_dict

    def __predict(self, lifestyle:np.ndarray):
        data = self.__get_whole_data(lifestyle)
        result = round(self.__model.predict_proba(data)[0, 1]*100, 15)

        return result

    def __crossover(self, parent1:np.ndarray, parent2:np.ndarray):
        offspring = np.array([-1] * len(parent1[0]))
        random_index = random.randint(0, len(offspring)-1)
        probability = random.random()

        offspring[:random_index] = parent1[0][:random_index]
        offspring[random_index:] = parent2[0][random_index:]

        # mutation for diversity
        if probability <= self.__mutation_probability:
            point1 = random.randint(0, (len(offspring)-1)//2)
            point2 = random.randint((len(offspring)-1)//2 + 1, len(offspring)-1)

            column_ordered = [*self.__current_lifestyle.keys()]

            mutated_genes1 = float(random.choice([*self.__genes[column_ordered[point1]].keys()]))
            mutated_genes2 = float(random.choice([*self.__genes[column_ordered[point2]].keys()]))

            offspring[point1] = mutated_genes1
            offspring[point2] = mutated_genes2

        return np.expand_dims(offspring, axis=0)

    def get_recommendation(self, verbose=1):
        history = []
        self.__start_time = time.time()
        populations = self.__generate_populations()

        population_risk = [(indiv, self.__predict(indiv)) for indiv in populations]
        self.__best_lifestyle = self.__current_lifestyle_arr
        self.__best_result = self.__current_risk

        for generation in range(self.__generations):
            # 1. (Selection phase) Select parent from the population
            sorted_populations = sorted(population_risk, key=(lambda x: x[1]))

            if sorted_populations[0][1] < self.__best_result:
                self.__best_lifestyle, self.__best_result = sorted_populations[0]

            # 2. Crossover and generate new population (mutation)
            new_populations = sorted_populations[:int(float(len(populations)*0.1))]
            for _ in range(int(float(len(populations)*0.9))):
                parent1 = random.choice(sorted_populations[:int(float(len(populations)*0.5))])[0]
                parent2 = random.choice(sorted_populations[:int(float(len(populations)*0.5))])[0]
                offspring = self.__crossover(parent1, parent2)
                offspring_risk = self.__predict(offspring)

                new_populations.append((offspring, offspring_risk))
            population_risk = new_populations
            history.append(self.__best_result)

            if verbose == 1:
                print(f'Generation {generation+1} ==> \n\tRisk: {self.__best_result}\n\tLifestyle: {self.__best_lifestyle}\n')

        return self.__translate_lifestyle(self.__best_lifestyle, self.__best_result), history
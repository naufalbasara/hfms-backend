import joblib, os, tensorflow as tf, sklearn, numpy as np, pandas as pd, json, warnings, re, time
import optimization_model.genetic_algorithm as optimization

from pprint import pprint

from flask import Flask, url_for, request
from markupsafe import escape
from datetime import date

from tools.utils import get_rootdir, preprocess_pipeline, load_model

warnings.filterwarnings("ignore")

app = Flask(__name__)

root_dir = get_rootdir()
model_path = os.path.join(root_dir, 'flaskr/prediction_model/model_cnn_v2-3.h5')
scaler_path = os.path.join(root_dir, 'flaskr/scaler_model/standard_scaler.gz')
column_order_path = os.path.join(root_dir, 'flaskr/optimization_model/data/columns_order-v2.json')
genes_path = os.path.join(root_dir, 'flaskr/optimization_model/data/variable_discrete_value.json')
model = load_model(model_path)

@app.route('/predict/', methods=['GET', 'POST'])
def predict():
    result_json = {}
    time_start = time.time()
    with open(column_order_path, 'r') as json_file:
        json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
        lifestyle_col = json.loads(json_f)['lifestyle']
        characteristic_col = json.loads(json_f)['characteristic']
    
    if request.method == 'POST':
        # load data from form / http post request
        characteristic = {}
        lifestyle = {}
        request_data = request.get_json()
        try:

            for ls_col in lifestyle_col.keys():
                lifestyle[ls_col] = request_data[ls_col]

            for char_col in characteristic_col.keys():
                if char_col == 'Quest16_MCQ160B':
                    continue
                characteristic[char_col] = request_data[char_col]


            characteristic = np.expand_dims(np.array([*characteristic.values()]), axis=0)
            lifestyle = np.expand_dims(np.array([*lifestyle.values()]), axis=0)
        except Exception as e:
            result_json['result'] = 'The data is incomplete, please provide the full data instead.'
            result_json['errorDetails'] = f'{e}'
            result_json['status'] = 404
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 404

        # preprocess data through data pipeline
        try:
            whole_data = preprocess_pipeline(scaler_path, characteristic, lifestyle)
            result = model.predict(whole_data, verbose=0)
            result_json['result'] = {
                'label': f"{np.argmax(result)}",
                'text': f"{'Not having heart failure.' if np.argmax(result)== 0 else 'Likely to have heart failure.'}"
            }
            result_json['probability'] = f"{result[0, 1]}"
            result_json['status'] = 200
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 200
        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['error'] = f'{e}'
            result_json['status'] = 404
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 404

    
    if request.method == 'GET':
        result_json['characteristic'] = [*characteristic_col.values()]
        result_json['lifestyle'] = [*lifestyle_col.values()]
    
    return result_json


@app.route('/recommendation/', methods=['POST'])
def get_recommendation():
    global model_path
    result_json = {}
    time_start = time.time()

    with open(column_order_path, 'r') as json_file:
        json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
        lifestyle_col = json.loads(json_f)['lifestyle']
        characteristic_col = json.loads(json_f)['characteristic']

    if request.method == 'POST':
        # get all the data from form / http post request 
        characteristic = {}
        lifestyle = {}
        request_data = request.get_json()

        try:
            for ls_col in lifestyle_col.keys():
                lifestyle[ls_col] = float(request_data[ls_col])

            for char_col in characteristic_col.keys():
                if char_col == 'Quest16_MCQ160B': continue
                characteristic[char_col] = request_data[char_col]

            # get all the data to numpy
            characteristic = np.expand_dims(np.array([*characteristic.values()]), axis=0)
            current_lifestyle = lifestyle

        except:
            result_json['result'] = 'There is something wrong with the data'
            result_json['error'] = f'{e}'
            result_json['status'] = 404
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 404

        with open(genes_path, 'r') as json_file:
            lifestyle_genes = json.load(json_file)
        try:
            # initiate model object
            recommendation = optimization.GA(
                lifestyle_genes=lifestyle_genes,
                characteristic=characteristic,
                current_lifestyle=current_lifestyle,
                population_size=25,
                generations=30,
                mutation_probability=0.2,
                model_path=model_path
            )

            # run preprocessing pipeline
            recommendation.preprocess_pipeline(scaler_path)

            # get recommendation
            try:
                recommendation_result, history = recommendation.get_recommendation(verbose=0)
                result_json['recommendationResult'] = recommendation_result
                result_json['resultHistory'] = history

            except Exception as e:
                result_json['errorDetails'] = f'{e}'
                result_json['timeGenerated'] = str(date.today())
                result_json['timeTaken'] = f'{time.time() - time_start} s'

                return result_json, 404

            result_json['status'] = 200
            result_json['statusMessage'] = "Success retrieving recommendation data"
            
            return result_json, 200

        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['status'] = 404
            result_json['errorDetails'] = f'{e}'
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 404
    
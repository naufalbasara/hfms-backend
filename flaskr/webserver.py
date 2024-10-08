import numpy as np, json, warnings, time, os
import optimization_model.genetic_algorithm as optimization

from datetime import datetime
from flask import Flask, request
from flask_cors import CORS, cross_origin
from datetime import date
from tools.utils import preprocess_pipeline, load_model
from ext.firebase_connection import FireBase
from ext.preprocess_webserver import PreProcess
from ext.preprocess import PreProcess as AppPreprocess

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'application/json'
CORS(app,resources={r"*": {"origins": "*"}})

def get_metadata_version(version, call_type:str) -> dict:
    version_text = f'v{version}'
    
    configuration_mapping = {
        'fp': {
            'v1': {
                'description': 'For thesis final project purposes',
                'scaler_path': f'scaler_model/{version_text}_standard_scaler.gz',
                'columns_order_path': f'optimization_model/metadata/{version_text}/{version_text}_columns_order.json',
                'genes_path': f'optimization_model/metadata/{version_text}/{version_text}_variable_discrete_value.json',
                'model_path': 'prediction_model/model_cnn_v2-3.h5'
            },
            'v2': {
                'description': 'For thesis final project (app) testing purposes',
                'scaler_path': f'scaler_model/{version_text}_standard_scaler.gz',
                'columns_order_path': f'optimization_model/metadata/{version_text}/{version_text}_columns_order.json',
                'genes_path': f'optimization_model/metadata/{version_text}/{version_text}_variable_discrete_value.json',
                'model_path': 'prediction_model/model_cnn_app.h5'
            },
            'v3': {
                'description': 'For thesis final project purposes',
                'scaler_path': f'scaler_model/{version_text}_standard_scaler.gz',
                'columns_order_path': f'optimization_model/metadata/{version_text}/{version_text}_columns_order.json',
                'genes_path': f'optimization_model/metadata/{version_text}/{version_text}_variable_discrete_value.json',
                'model_path': 'prediction_model/model_lstm_v3.h5'
            }
        },
        'app': {
            'v1': {
                'description': 'For application purposes, only receive user_id in a JSON payload',
                'scaler_path': f'scaler_model/app/{version_text}_standard_scaler.gz',
                'columns_order_path': f'optimization_model/metadata/app/{version_text}/{version_text}_columns_order.json',
                'genes_path': f'optimization_model/metadata/app/{version_text}/{version_text}_variable_discrete_value.json',
                'model_path': 'prediction_model/model_cnn_proper_apps_v3.h5'
            }
        }
    }
    try:
        if call_type == 'index':
            return configuration_mapping
        
        configuration_mapping = configuration_mapping['app' if call_type == 'app' else 'fp']

        return configuration_mapping[f'v{version}']
    except:
        return None

@app.route('/', methods=['GET'])
@cross_origin(origins='*')
def index():
        return {
            "Description": "Heart Failure Prediction and Lifestyle Recommendation System"
        }, 200

# ===================== FP Endpoints =====================
@app.route('/v<int:version>/predictions/', methods=['GET', 'POST'])
@cross_origin(origins='*')
def predict(version):
    # load configuration for relevant version
    assert type(version) == int and get_metadata_version(version, call_type='fp') != None
    metadata = get_metadata_version(version, call_type='fp')
    result_json = {}
    time_start = time.time()
    
    try:
        with open(metadata['columns_order_path'], 'r') as json_file:
            json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
            lifestyle_col = json.loads(json_f)['lifestyle']
            characteristic_col = json.loads(json_f)['characteristic']
    except Exception as e:
        result_json['result'] = 'Metadata file not found.'
        result_json['errorDetails'] = f'{e}'
        result_json['status'] = 400
        result_json['timeGenerated'] = str(date.today())
        result_json['timeTaken'] = f'{time.time() - time_start} s'

        return result_json, 400
    
    if request.method == 'POST':
        model = load_model(metadata['model_path'])
        # load data from form / http post request
        characteristic = {}
        lifestyle = {}
        request_data = request.get_json()

        # map the data from POST request json data to relevant variables
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
            result_json['status'] = 400
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 400

        # preprocess data through data pipeline
        try:
            whole_data = preprocess_pipeline(metadata['scaler_path'], characteristic, lifestyle, version=version)
            result = model.predict(whole_data, verbose=0)
            result_json['result'] = {
                'label': f"{np.argmax(result)}",
                'text': f"{'Not having heart failure.' if np.argmax(result)== 0 else 'Likely to have heart failure.'}"
            }
            result_json['probability'] = f"{result[0,1]*100}"
            result_json['status'] = 200
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 200
        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['error'] = f'{e}'
            result_json['status'] = 400
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 400

    
    if request.method == 'GET':
        result_json['acceptedDataScheme'] = {'lifestyle': lifestyle_col,
                                             'characteristic': characteristic_col
                                             }
    
        return result_json, 200

@app.route('/v<int:version>/recommendations/', methods=['POST', 'GET'])
@cross_origin(origins='*')
def recommendation(version):
    # load configuration for relevant version
    assert type(version) == int and get_metadata_version(version, call_type='fp') != None
    metadata = get_metadata_version(version, call_type='fp')

    result_json = {}
    time_start = time.time()

    try:
        with open(metadata['columns_order_path'], 'r') as json_file:
            json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
            lifestyle_col = json.loads(json_f)['lifestyle']
            characteristic_col = json.loads(json_f)['characteristic']
    except Exception as e:
        result_json['result'] = 'Metadata file not found.'
        result_json['errorDetails'] = f'{e}'
        result_json['status'] = 400
        result_json['timeGenerated'] = str(date.today())
        result_json['timeTaken'] = f'{time.time() - time_start} s'

        return result_json, 400

    if request.method == 'POST':
        # get all the data from form / http post request 
        characteristic = {}
        lifestyle = {}
        request_data = request.get_json()
        request_headers = request.headers

        try:
            for ls_col in lifestyle_col.keys():
                lifestyle[ls_col] = float(request_data[ls_col])

            for char_col in characteristic_col.keys():
                if char_col == 'Quest16_MCQ160B': continue
                characteristic[char_col] = float(request_data[char_col])

            # get all the data to numpy
            characteristic = np.expand_dims(np.array([*characteristic.values()]), axis=0)
            current_lifestyle = lifestyle

        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['error'] = f'{e}'
            result_json['status'] = 400
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 400

        with open(metadata['genes_path'], 'r') as json_file:
            lifestyle_genes = json.load(json_file)
        try:
            # initiate model object
            recommendation = optimization.GA(
                lifestyle_genes=lifestyle_genes,
                characteristic=characteristic,
                current_lifestyle=current_lifestyle,
                population_size=30,
                generations=30,
                mutation_probability=0.2,
                model_path=metadata['model_path'],
                scaler_path=metadata['scaler_path'],
                for_app=False,
                version=version
            )

            # get recommendation
            try:
                print("recommending")
                recommendation_result, history = recommendation.get_recommendation(verbose=0)
                result_json['recommendationResult'] = recommendation_result
                result_json['resultHistory'] = history

            except Exception as e:
                result_json['errorDetails'] = f'Error while generating recommendation: {e}'
                result_json['timeGenerated'] = str(date.today())
                result_json['timeTaken'] = f'{time.time() - time_start} s'

                return result_json, 400

            result_json['status'] = 200
            result_json['statusMessage'] = "Success retrieving recommendation data"
            
            return result_json, 200

        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['status'] = 400
            result_json['errorDetails'] = f'{e}'
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 400
    
    if request.method == 'GET':
        result_json['acceptedDataScheme'] = {'lifestyle': lifestyle_col,
                                             'characteristic': characteristic_col
                                             }
        
        return result_json, 200
# ===================== End of FP Endpoints =====================


# ===================== Application Endpoints =====================
@app.route('/v<int:version>/app/recommendations/', methods=['POST'])
@cross_origin(origins='*')
def app_recommendation(version):
    # load configuration for relevant version
    assert type(version) == int and get_metadata_version(version, call_type='app') != None
    metadata = get_metadata_version(version, call_type='app')

    result_json = {}
    time_start = time.time()

    # try getting metadata for corresponding version
    try:
        with open(metadata['columns_order_path'], 'r') as json_file:
            json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
            lifestyle_col = json.loads(json_f)['lifestyle']
            characteristic_col = json.loads(json_f)['characteristic']
    except Exception as e:
        result_json['result'] = 'Metadata file not found.'
        result_json['errorDetails'] = f'{e}'
        result_json['status'] = 400
        result_json['timeGenerated'] = str(date.today())
        result_json['timeTaken'] = f'{time.time() - time_start} s'

        return result_json, 400

    if request.method == 'POST':
        # get all the data from form / http post request 
        characteristic = {}
        lifestyle = {}
        request_data = request.get_json()
        print(f' {datetime.now()} request_data ===> ', request_data)
        user_id = request_data.get('user_id', None)
        print(f'request from {user_id}')
        if (user_id == None) or (user_id == ''):
            print('preprocess with preprocess_webserver')
            pipeline = PreProcess()
            cleaned_data = pipeline.preprocess(request_data)
        else:
            print('preprocess with preprocess for app')
            firebase = FireBase('PulseWise_secret.json')
            preprocess = AppPreprocess()
            user_data = firebase.get_data(user_id)
            if (user_data.get('sleep_time', None) == '') or (user_data.get('sleep_time', None) == None) :
                return {
                    'result': f'No data input from user {user_id}',
                    'status': 400,
                    'timeGenerated': str(date.today()),
                    'timeTaken': f'{time.time() - time_start} s'
                }, 400
            cleaned_data = preprocess.preprocess(user_data)
            print('cleaned_data ===> ',cleaned_data)
            if cleaned_data == None or cleaned_data.get('Dieta1_DR1TKCAL', None) == None:
                return {
                    'result': 'Bad input, please complete your profile',
                    'status': 400,
                    'timeGenerated': str(date.today()),
                    'timeTaken': f'{time.time() - time_start} s'
                }, 400

        try:
            for ls_col in lifestyle_col.keys():
                lifestyle[ls_col] = float(cleaned_data[ls_col])

            for char_col in characteristic_col.keys():
                if char_col == 'Quest16_MCQ160B': continue
                characteristic[char_col] = float(cleaned_data[char_col])

            # get all the data to numpy
            characteristic = np.expand_dims(np.array([*characteristic.values()]), axis=0)
            current_lifestyle = lifestyle

        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['error'] = f'{e}'
            result_json['status'] = 400
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 400

        with open(metadata['genes_path'], 'r') as json_file:
            lifestyle_genes = json.load(json_file)
        try:
            # initiate model object
            recommendation = optimization.GA(
                lifestyle_genes=lifestyle_genes,
                characteristic=characteristic,
                current_lifestyle=current_lifestyle,
                population_size=30,
                generations=30,
                mutation_probability=0.1,
                model_path=metadata['model_path'],
                scaler_path=metadata['scaler_path'],
                for_app=True,
                version=version
            )

            # get recommendation
            try:
                print("recommending")
                recommendation_result, history = recommendation.get_recommendation(verbose=0)
                result_json['recommendationResult'] = recommendation_result
                result_json['resultHistory'] = history

            except Exception as e:
                result_json['errorDetails'] = f'Error while generating recommendation: {e}'
                result_json['timeGenerated'] = str(date.today())
                result_json['timeTaken'] = f'{time.time() - time_start} s'

                return result_json, 400

            result_json['status'] = 200
            result_json['statusMessage'] = "Success retrieving recommendation data"
            
            return result_json, 200

        except Exception as e:
            result_json['result'] = 'There is something wrong with the data'
            result_json['status'] = 400
            result_json['errorDetails'] = f'{e}'
            result_json['timeGenerated'] = str(date.today())
            result_json['timeTaken'] = f'{time.time() - time_start} s'

            return result_json, 400
    
    if request.method == 'GET':
        result_json['acceptedDataScheme'] = {'lifestyle': lifestyle_col,
                                             'characteristic': characteristic_col
                                             }
        
        return result_json, 200

@app.route('/v<int:version>/app/predictions/', methods=['POST'])
@cross_origin(origins='*')
def app_predict(version):
    metadata = get_metadata_version(version, call_type='app')
    response_json = {}
    time_start = time.time()

    if request.method == 'POST':
        model = load_model(metadata['model_path'])
        try:
            with open(metadata['columns_order_path'], 'r') as json_file:
                json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
                lifestyle_col = json.loads(json_f)['lifestyle']
                characteristic_col = json.loads(json_f)['characteristic']
        except Exception as e:
            response_json['result'] = 'Metadata file not found.'
            response_json['errorDetails'] = f'{e}'
            response_json['status'] = 400
            response_json['timeGenerated'] = str(date.today())
            response_json['timeTaken'] = f'{time.time() - time_start} s'

            return response_json, 400

        # load data from form / http post request
        characteristic = {}
        lifestyle = {}
        user_id = request.get_json()['user_id']

        # instantiate necessary object
        firebase = FireBase('PulseWise_secret.json')
        preprocess = AppPreprocess()
        cleaned_data = preprocess.preprocess(firebase.get_data(user_id))
    
        # map the data from POST request json data to relevant variables
        try:
            for ls_col in lifestyle_col.keys():
                if cleaned_data[ls_col] == None: cleaned_data[ls_col] = 0
                lifestyle[ls_col] = cleaned_data[ls_col]

            for char_col in characteristic_col.keys():
                if char_col == 'Quest16_MCQ160B':
                    continue
                if cleaned_data[char_col] == None: cleaned_data[char_col] = 0
                characteristic[char_col] = cleaned_data[char_col]

            characteristic = np.expand_dims(np.array([*characteristic.values()]), axis=0)
            lifestyle = np.expand_dims(np.array([*lifestyle.values()]), axis=0)

        except Exception as e:
            response_json['result'] = 'The data is incomplete, please provide the full data instead.'
            response_json['errorDetails'] = f'{e}'
            response_json['status'] = 400
            response_json['timeGenerated'] = str(date.today())
            response_json['timeTaken'] = f'{time.time() - time_start} s'

            return response_json, 400

        # preprocess data through data pipeline
        try:
            whole_data = preprocess_pipeline(metadata['scaler_path'], characteristic, lifestyle, version=version)
            result = model.predict(whole_data, verbose=0)

            response_json['result'] = {
                'label': f"{np.argmax(result)}",
                'text': f"{'Not having heart failure.' if np.argmax(result)== 0 else 'Likely to have heart failure.'}"
            }
            response_json['probability'] = f"{result[0, 1]}"
            response_json['status'] = 200
            response_json['timeGenerated'] = str(date.today())
            response_json['timeTaken'] = f'{time.time() - time_start} s'

            return response_json, 200
        except Exception as e:
            response_json['result'] = 'There is something wrong with the data'
            response_json['error'] = f'{e}'
            response_json['status'] = 400
            response_json['timeGenerated'] = str(date.today())
            response_json['timeTaken'] = f'{time.time() - time_start} s'

            return response_json, 400
    
    return response_json
# ===================== End of Application Endpoints =====================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
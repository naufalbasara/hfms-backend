import joblib, os, tensorflow as tf, sklearn, numpy as np, pandas as pd, json, warnings, re, time
import optimization_model.genetic_algorithm as optimization

from flask import Flask, request
from datetime import date
from tools.utils import get_rootdir, get_certificate, preprocess_pipeline, load_model
from ext.firebase_connection import FireBase
from ext.preprocess import PreProcess

warnings.filterwarnings("ignore")

app = Flask(__name__)

root_dir = get_rootdir()
firebase_dir = get_certificate()

def get_metadata_version(version:int, call_type:str) -> dict:
    global root_dir
    assert type(version) == int

    version_text = f'v{version}'
    
    configuration_mapping = {
        'fp': {
            'v1': {
                'description': 'For thesis final project purposes',
                'scaler_path': os.path.join(root_dir, f'flaskr/scaler_model/{version_text}_standard_scaler.gz'),
                'columns_order_path': os.path.join(root_dir, f'flaskr/optimization_model/metadata/{version_text}/{version_text}_columns_order.json'),
                'genes_path': os.path.join(root_dir, f'flaskr/optimization_model/metadata/{version_text}/{version_text}_variable_discrete_value.json'),
                'model_path': os.path.join(root_dir, 'flaskr/prediction_model/model_cnn_v2-3.h5')
            },
            'v2': {
                'description': 'For thesis final project (app) testing purposes',
                'scaler_path': os.path.join(root_dir, f'flaskr/scaler_model/{version_text}_standard_scaler.gz'),
                'columns_order_path': os.path.join(root_dir, f'flaskr/optimization_model/metadata/{version_text}/{version_text}_columns_order.json'),
                'genes_path': os.path.join(root_dir, f'flaskr/optimization_model/metadata/{version_text}/{version_text}_variable_discrete_value.json'),
                'model_path': os.path.join(root_dir, 'flaskr/prediction_model/model_cnn_app.h5')
            }
        },
        'app': {
            'v1': {
                'description': 'For application purposes, only receive user_id in a JSON payload',
                'scaler_path': os.path.join(root_dir, f'flaskr/scaler_model/app/{version_text}_standard_scaler.gz'),
                'columns_order_path': os.path.join(root_dir, f'flaskr/optimization_model/metadata/app/{version_text}/{version_text}_columns_order.json'),
                'genes_path': os.path.join(root_dir, f'flaskr/optimization_model/metadata/app/{version_text}/{version_text}_variable_discrete_value.json'),
                'model_path': os.path.join(root_dir, 'flaskr/prediction_model/model_cnn_app.h5')
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
def index():
    response_json = {}
    path_obj = get_metadata_version(0, 'index')
    for key in path_obj.keys(): 
        response_json[key] = {}
        for version in path_obj[key].keys():
            response_json[key][version] = {
                'description': getattr(path_obj[key][version], 'description', None),
                'predictions': f'/{version}/{"app/" if key=="app" else ""}predictions',
                'recommendations': f'/{version}/{"app/" if key=="app" else ""}recommendations',
            }
    
    return response_json

# ===================== FP Endpoints =====================
@app.route('/v<int:version>/predictions/', methods=['GET', 'POST'])
def predict(version):
    # load configuration for relevant version
    assert type(version) == int and get_metadata_version(version, call_type='fp') != None
    metadata = get_metadata_version(version, call_type='fp')
    result_json = {}
    time_start = time.time()
    model = load_model(metadata['model_path'])

    with open(metadata['columns_order_path'], 'r') as json_file:
        json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
        lifestyle_col = json.loads(json_f)['lifestyle']
        characteristic_col = json.loads(json_f)['characteristic']
    
    if request.method == 'POST':
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
            result_json['probability'] = f"{result[0, 1]}"
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
def recommendation(version):
    # load configuration for relevant version
    assert type(version) == int and get_metadata_version(version, call_type='fp') != None
    metadata = get_metadata_version(version, call_type='fp')

    result_json = {}
    time_start = time.time()

    with open(metadata['columns_order_path'], 'r') as json_file:
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
                population_size=25,
                generations=30,
                mutation_probability=0.2,
                model_path=metadata['model_path'],
                scaler_path=metadata['scaler_path'],
                version=version
            )

            # get recommendation
            try:
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
# @app.route('/v<int:version>/app/recommendations/', methods=['POST'])
# def app_recommendation(version):
#     return

@app.route('/v<int:version>/app/predictions/', methods=['POST'])
def app_predict(version):
    metadata = get_metadata_version(version, call_type='app')
    response_json = {}
    model = load_model(metadata['model_path'])
    time_start = time.time()

    if request.method == 'POST':
        with open(metadata['columns_order_path'], 'r') as json_file:
            json_f = str(json_file.read()).strip("'<>() ").replace('\'', '\"')
            lifestyle_col = json.loads(json_f)['lifestyle']
            characteristic_col = json.loads(json_f)['characteristic']

        # load data from form / http post request
        characteristic = {}
        lifestyle = {}
        user_id = request.get_json()['user_id']

        # instantiate necessary object
        firebase = FireBase(firebase_dir)
        preprocess = PreProcess()
        cleaned_data = preprocess.preprocess(firebase.get_data(user_id))
    
        # map the data from POST request json data to relevant variables
        try:
            for ls_col in lifestyle_col.keys():
                if cleaned_data[ls_col] == None: raise Exception(f'{ls_col} missing')
                lifestyle[ls_col] = cleaned_data[ls_col]

            for char_col in characteristic_col.keys():
                if cleaned_data[char_col] == None: raise Exception(f'{char_col} missing')
                if char_col == 'Quest16_MCQ160B':
                    continue
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
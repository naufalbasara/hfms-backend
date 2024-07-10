import joblib, sklearn, numpy as np, pandas as pd, json, os, re

def get_rootdir() -> str:
    cwd = os.path.abspath(os.getcwd())
    try:
        end = re.search(r'flaskr', cwd).start()
        rootdir = cwd[:end]
    except:
        end = re.search(r'hfms-backend', cwd).end()
        rootdir = cwd[:end]

    return rootdir

def get_certificate() -> str:
    root_dir = get_rootdir()
    cert_path = os.path.join(root_dir, 'client_secret/PulseWise_secret.json')

    return cert_path

def load_model(model_path:str):
    """path to saved model with h5 format"""
    model = joblib.load(model_path)
    # model = keras.models.load_model(model_path)

    return model

def to_interval(interval_str:str) -> pd.Interval:
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
        raise f'{type(e)}:{e}'

    return pd.Interval(left=left_value, right=right_value, closed=closed)

def discretize(value, column, version:int):
    var_path = os.path.join(get_rootdir(), f'flaskr/optimization_model/metadata/v{version}/v{version}_variable_discrete_value.json')
    with open(var_path, 'r') as json_file:
        variable_discrete_val = json.load(json_file)

    for index, (encode, interval) in enumerate(sorted(variable_discrete_val[column].items(), key=lambda x: x[0])):
        value_list = [*variable_discrete_val[column].values()]

        try:
            interval_val = to_interval(interval)
            if index == 0 and value <= interval_val.left:
                return encode
            
            elif value in interval_val:
                return encode
            
            elif index == len(value_list)-1:
                return encode
            
        except:
            return value
        

def preprocess_pipeline(scaler_file_path:str, characteristic:np.ndarray, lifestyle:np.ndarray, version:int):
    var_path = os.path.join(get_rootdir(), f'flaskr/optimization_model/metadata/v{version}/v{version}_columns_order.json')
    discreted_values = []
    with open(var_path, 'r') as json_file:
        column_order = json.load(json_file)
        lifestyle_order = column_order['lifestyle']

    scaler = joblib.load(scaler_file_path)
    assert type(scaler) == sklearn.preprocessing.StandardScaler

    # encode to discretize lifestyle value
    for index, ls_value in enumerate(lifestyle[0]):
        try:
            discreted_value = discretize(ls_value, [*lifestyle_order.keys()][index], version)
            discreted_values.append(discreted_value)
        except Exception as e:
            print(e)
            discreted_values.append(ls_value)

    lifestyle = np.expand_dims(np.array(discreted_values), axis=0)
    
    # do feature scaling
    characteristic = scaler.transform(characteristic)

    whole_data = np.concatenate([lifestyle, characteristic], axis=1).astype(float)
    whole_data = whole_data.reshape(whole_data.shape[0], whole_data.shape[1], 1)

    return whole_data
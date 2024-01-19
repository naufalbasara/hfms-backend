from tools.gsheet_conn import GSheet
from services.preprocess_data import Dataframe
import os, pandas as pd
from dotenv import load_dotenv

def variable_mapping(variable_file_sheet_key='1AZrKKjabT-tRUceCXFq8BA_aHQQTUNC0Mc5mKEo224I'):
    """To make a dictionary of variable name"""
    variable_to_description = {}
    sheet = GSheet(variable_file_sheet_key)
    variable = sheet.to_df(sheet.open_wks('Sheet1'))

    for row in variable.values:
        if row[4] not in variable_to_description:
            variable_to_description[row[4]] = row[5]

    return variable_to_description

def do_join():
    # get the environment variables
    drive_path = os.getenv('DRIVE_PATH')
    data = None

    # loop through folder of survey variable type (demographic, laboratory, questionnaire, etc.)
    for survey_type in os.listdir(os.path.join(drive_path, 'Dataset/Raw CSV')):
        print(f'Extracting data from folder {survey_type}...\n')
        type_path = os.path.join(drive_path, 'Dataset/Raw CSV', survey_type)

        # loop through files in current survey type
        for dataset in os.listdir(type_path):
            dataset_path = os.path.join(type_path, dataset)
            try:
                if type(data) == type(None):
                    print(f"Initializing dataset with {dataset}")
                    data = Dataframe(dataset_path, 'csv')
                    continue
                
                df = pd.read_csv(dataset_path)
                data.join(df, on='SEQN')
            except Exception as error:
                print(f"[ERROR]: on file {dataset}\n\tYIELD: {error}")
    
    print(data.null_summary())

    return

if __name__ == '__main__':
    load_dotenv()
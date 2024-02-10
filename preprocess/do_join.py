from tools.gsheet_conn import GSheet
from preprocess.preprocess_data import Dataframe
import os, pandas as pd
from dotenv import load_dotenv

load_dotenv()

def variable_mapping(variable_file_sheet_key='1AZrKKjabT-tRUceCXFq8BA_aHQQTUNC0Mc5mKEo224I'):
    """To make a dictionary of variable name"""
    variable_to_description = {}
    sheet = GSheet(variable_file_sheet_key)
    variable = sheet.to_df(sheet.open_wks('Sheet1'))

    for row in variable.values:
        if row[4] not in variable_to_description:
            variable_to_description[row[4]] = row[5]

    return variable_to_description

if __name__ == '__main__':
    drive_path = '/Users/naufalbasara/naufalrb19@gmail.com - Google Drive/My Drive/Kuliah/Tugas Akhir/Final Project Shared Folder'
    combined_sheet = GSheet('1U-M35MU4VLXQTtSWkM9xddJAAeh6Z7bjGZOwwPZGnS4')
    variable_list_sheet = GSheet('1AZrKKjabT-tRUceCXFq8BA_aHQQTUNC0Mc5mKEo224I')
    folder_path = os.path.join(drive_path, 'Dataset/Raw CSV/')

    file_used = {}

    # Get all the used variable files in a dictionary
    # do something here..
    variable_list = variable_list_sheet.to_df(variable_list_sheet.open_wks('Sheet1'))
    variable_list = variable_list[variable_list['is_used'] == 'TRUE']

    for _, row in variable_list.iterrows():
        if row['name'] not in file_used:
            print(f'Creating list of files for {row["name"]}')
            file_used[row['name']] = []
        
        if row['title'] not in file_used[row['name']]:
            file_used[row['name']].append(row['title'])

    print("Done creating list for used files.")
    
    # Combine all the files by type
    # e.g. Demographic -> Demographic_Combined
    # e.g. Dietary1, Dietary2 -> Dietary_Combined
    print()
    combined_all = None
    for name, files in file_used.items():
        combined = None
        combined_name = name
        print(f'Merging all files in {name}...')
        
        for count, file in enumerate(files):
            try:
                file_code = f'{name[:5]}{count+1}'
                file_path = os.path.join(folder_path, name, f'{file.strip()}.csv')
                df = pd.read_csv(file_path)

                used_variables = variable_list[(variable_list['name'] == name) & (variable_list['title'] == file)]['variable'].tolist()
                df = df.loc[:, used_variables]

                old_ = df.columns
                new_ = [*df.columns]
                new_.remove('SEQN')
                new_ = [*map(lambda x: f'{file_code}_{x}', new_)]
                new_.insert(0, 'SEQN')

                column_mapping = dict(map(lambda x,y: (x,y), old_, new_))
                
                # rename all columns according to the survey type
                df.rename(columns=column_mapping, inplace=True)

                if type(combined) == type(None):
                    combined = df
                    continue

                combined = pd.merge(combined, df, how='outer', on='SEQN')
            except Exception as e:
                print(f"[FAILED]: Error in file {file}, {e}")
        
        if type(combined_all) == type(None):
            combined_all = combined
            continue
        
        combined_all = pd.merge(combined_all, combined, how='outer', on='SEQN')

        print(f'Merging files in {name} completed.')
        print()

        try:
            combined_sheet.trunc_ins(name, combined)
            print("Successfully updated to sheets \"Review Combined\"")
        except:
            print("[FAILED]: Unable to store in sheet..")
            print("Proceed to store in drive under the folder Dataset/Merged_Backup...")
            combined.to_csv(os.path.join(drive_path, 'Dataset/Merged_Backup', f'Combined_{name}.csv'))
            print("File stored.")
        
        print(f'---\t\t{name} COMPLETED\t\t---')
    
    try:
        combined_sheet.trunc_ins('ALL', combined_all)
        print("Successfully updated to sheets \"ALL\"")
    except:
        print("[FAILED]: Unable to store Combined_All in sheet..")
        print("Proceed to store in drive under the folder Dataset/Merged_Backup...")
        combined_all.to_csv(os.path.join(drive_path, 'Dataset/Merged_Backup', f'Combined_All.csv'))
        print("All combination file stored.")
    

    print(f'---\t\tALL COMPLETED\t\t---')
    print('\n\n')
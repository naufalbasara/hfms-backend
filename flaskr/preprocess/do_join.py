from tools.gsheet_conn import GSheet
import os, pandas as pd, json
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

def join(how, drive_path, data_folder_path, version):
    variable_list_sheet = GSheet('1AZrKKjabT-tRUceCXFq8BA_aHQQTUNC0Mc5mKEo224I')
    result_combined_sheet = GSheet('1U-M35MU4VLXQTtSWkM9xddJAAeh6Z7bjGZOwwPZGnS4')
    # log_sheet = GSheet('1rY5qjPzRNPcjzojSGvCyY-Gzj4-KD3oPAuVHviiVW2A')
    all_columns = {}
    try:
        print(f'-----\t\tPROCESS STARTED\t\t-----')
        file_used = {}

        # Get all the used variable files in a dictionary
        variable_list = variable_list_sheet.to_df(variable_list_sheet.open_wks('Sheet1'))
        variable_list = variable_list[variable_list['is_used'] == 'TRUE']

        for _, row in variable_list.iterrows():
            if row['name'] not in file_used:
                print(f'Creating list of files for {row["name"]}')
                file_used[row['name']] = []
                
            if row['title'] not in file_used[row['name']]:
                if row['title'] in ['Dietary Interview - Individual Foods, First Day', 'Dietary Interview - Individual Foods, Second Day'] and how == 'diet_ignored':
                    # skipped the data for respondent daily food consumption and only take the daily nutrition
                    continue
                else:
                    # do normal join
                    file_used[row['name']].append(row['title'])

        print("Done creating list for used files.\n")
            
        # Combine all the files by type
        # e.g. Demographic -> Demographic_Combined
        # e.g. Dietary1, Dietary2 -> Dietary_Combined
        combined_all = None
        for name, files in file_used.items():
            print(f'---\t\t{name} STARTED\t\t---')
            combined = None
            print(f'Merging all files in {name}...')
                
            for count, file in enumerate(files):
                try:
                    file_code = f'{name[:5]}{count+1}'
                    file_path = os.path.join(data_folder_path, name, f'{file.strip()}.csv')
                    df = pd.read_csv(file_path)

                    used_variables = [*map(lambda x: x.upper(), variable_list[(variable_list['name'] == name) & (variable_list['title'] == file)]['variable'].tolist())]
                    df = df.loc[:, used_variables]

                    # join on the user's input
                    if file.strip() in ['Dietary Interview - Individual Foods, First Day', 'Dietary Interview - Individual Foods, Second Day']:
                        if how=='diet_aggregated':
                            # do join by aggregating all the user's record on one day food consumption
                            df = df.groupby(['SEQN', 'DRDINT'], dropna=False, as_index=False).mean()
                            
                        elif how=='diet_separated':
                            # do join by separating all the user's record on one day food consumption and eating occasion
                            pass
                    
                    # change the columns to respective name
                    old_ = df.columns
                    new_ = [*df.columns]
                    new_.remove('SEQN')
                    new_ = [*map(lambda x: f'{file_code}_{x}', new_)]
                    new_.insert(0, 'SEQN')

                    column_mapping = dict(map(lambda x,y: (x,y), old_, new_))
                    all_columns[file_code] = column_mapping
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
            else:
                combined_all = pd.merge(combined_all, combined, how='outer', on='SEQN')

            print(f'Merging files in {name} completed.')
            print()

            try:
                result_combined_sheet.trunc_ins(name, combined)
                print("Successfully updated to sheets \"Review Combined\"")
                print(f"Storing Combined_{name}...")
                combined.to_csv(os.path.join(drive_path, 'Dataset/Data Versioning/Data', f'Combined_{name}.csv'))
                print("File stored in drive under the folder Dataset/Data Versioning.")
            except:
                print(f"[FAILED]: Unable to store Combined_{name}.csv in sheet..")
            finally:
                print(f'---\t\t{name} COMPLETED\t\t---')
            
        try:
            result_combined_sheet.trunc_ins('ALL', combined_all)
            print("Successfully updated to sheets \"ALL\"")
            print("Storing all combined file in drive...")
            combined_all.to_csv(os.path.join(drive_path, 'Dataset/Data Versioning', f'Combined_All_V{version}.csv'))
            print("All combination file stored in drive under the folder Dataset/Data Versioning.")
        except Exception:
            raise Exception

        print("\nStored column mapping to json.\n")
        with open('column_mapping_ignored_diet.json', 'a') as json_file:
            json.dump(all_columns, json_file)
        print("Column mapping stored to json.\n")

        print(f'-----\t\t$PROCESS COMPLETED$\t\t-----')
        print('\n\n')
    except Exception as e:
        print(e)
        return False
    finally:
        return True
import os, pandas as pd

from tools.gsheet_conn import GSheet
from preprocess.do_join import join
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    drive_path = '/Users/naufalbasara/naufalrb19@gmail.com - Google Drive/My Drive/Kuliah/Tugas Akhir/Final Project Shared Folder'
    combined_sheet = GSheet('1U-M35MU4VLXQTtSWkM9xddJAAeh6Z7bjGZOwwPZGnS4')
    variable_list_sheet = GSheet('1AZrKKjabT-tRUceCXFq8BA_aHQQTUNC0Mc5mKEo224I')
    folder_path = os.path.join(drive_path, 'Dataset/Raw CSV/')

    # df=pd.read_csv(os.path.join(drive_path, 'Dataset/Raw CSV/Dietary/Dietary Interview - Individual Foods, First Day.csv'))
    # print(df.info())
    # print("Columns: ")
    # for i in range(len(df.columns)):
    #     print(df.columns[i])
    # print("Number of Cols: ", len(df.columns))
    # print("DF Shape: ", df.shape)

    # print()
    # print()

    # print(df[['SEQN', 'DR1ILINE']])
    # print("SEQN Unique value counts: ", df['SEQN'].value_counts())
    # print("DR1ILINE Unique value counts: ", df['DR1ILINE'].value_counts())


    # Join all the data from NHANES
    join(how='diet_ignored', drive_path=drive_path, data_folder_path=folder_path, version=5)
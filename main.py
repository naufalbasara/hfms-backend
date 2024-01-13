from services.gsheet_conn import GSheet
from services.preprocess_data import Dataframe
import os

# Testing read csv data file
df = Dataframe('1000_merchants.csv', 'csv')
df = df.to_df()
df = df.rename(columns={
    'Unnamed: 0': '',
    '0': 'merchant_id',
    '1': 'merchant_name',
    '2': 'phone_number',
    '3': 'latitude',
    '4': 'longitude',
    '5': 'cohort',
    '6': 'kecamatan',
})

df = Dataframe(df)
df.normalize_data('standardization')

print(df.null_summary())
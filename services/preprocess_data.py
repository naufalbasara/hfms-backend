import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import (StandardScaler, MinMaxScaler, MaxAbsScaler, RobustScaler)

class Dataframe:
    def __init__(self, dfOrPath, fileType=None):
        """
        dfOrPath: pass df or path of file to read, e.g. data.csv/data.xlsx
        fileType: type of file to read, e.g. csv, excel
        """
        try:
            if type(dfOrPath) == str and fileType != None:
                if fileType == 'csv':
                    self.df = pd.read_csv(dfOrPath)
                else:
                    self.df = pd.read_excel(dfOrPath)

            if type(dfOrPath) == pd.core.frame.DataFrame:
                self.df = dfOrPath

        except:
            raise Exception('Not the valid argument to initialize object')
        finally:
            return self.df.info()

    def null_summary(self, columns=None):
        """print summary of nulls in the dataframe or certain columns in the dataframe"""
        if columns != None:
            print(self.df[columns].isnull().sum())
        
        return self.df.isnull().sum()
    
    def to_df(self):
        """returning dataframe object"""
        return self.df

    def normalize_data(self, type, columns=None):
        """do feature scaling in a dataframe, provided two types of feature scaling: standardization or normalization\n
        standardization : (x - mean) / sd\n
        normalization:\n
        a. min max scaling (min-max)\n
        b. mean normalization\n
        c. max absolute scaling (max-absolute)\n
        d. robust scaling (robust)
        """
        type_mapping = {
            'standardization': StandardScaler(),
            'min-max': MinMaxScaler(),
            'max-absolute': MaxAbsScaler(),
            'robust': RobustScaler()
        }
        try:
            scalingFunction = type_mapping[type]
            if columns != None:
                self.df
                self.df[columns] = scalingFunction.fit_transform(self.df[columns])
            
            self.df = scalingFunction.fit_transform(self.df)

        except:
            raise Exception()

        return

    def append(self, another_df):
        to_append = [self.df, another_df]
        self.df = pd.concat(to_append)
        return
    
    def join(self, another_df, on):
        self.df = pd.merge(self.df, another_df, how='outer', on=on)
        return
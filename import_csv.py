# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 17:01:26 2020

@author: David
"""
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import glob
import datetime
import os

default_path = r'D:\DataDay' # use your path


def get_all_data(path = default_path, start_year = 2014, end_year = 2020) :
    """get_all_data returns all data from given path following the TB output format,
    it also returns a list of contract names and a list of indecies.

    Parameters
    ----------
    start_year : int
        
    end_year : int
        
    path : str, optional
        file path, by default default_path

    Returns
    -------
    A tuple of data, names, and index
    """
    all_data = {}
    all_files = glob.glob(path + "/*.csv")
    contract_names = []
    longest_index = []
    for filename in all_files:
        contract_name = os.path.basename(filename).split(".")[0]
        
        df = pd.read_csv(filename, index_col=None, header=-1,)
        df.columns = ["Date","Hour","Open", "High", "Low", "Close", "Volume", "Open Interest"]
        df['Date']= df['Date'].apply(lambda x: pd.to_datetime(str(x), format='%Y%m%d'))
        df['Hour'] = df['Hour'].apply(lambda x: datetime.timedelta(hours = x/100))
        df['Time'] = df['Date'] + df['Hour']
        df.drop('Hour', axis=1, inplace=True)
        df.drop('Date', axis=1, inplace=True)
        df = df[df['Time'] >= datetime.date(start_year,1,1)]
        df =  df[df['Time'] <= datetime.date(end_year,12,31)]
        df = df.iloc[10:]
        df['Time'] = df['Time'].dt.strftime('%Y-%m-%d-%H')
        df.set_index("Time", inplace = True)
        
        if (len(df.index) >= len(longest_index)):
            longest_index = df.index
            
        contract_name = ''.join([i for i in contract_name if not i.isdigit()])
        all_data[contract_name] = df.to_dict('index')
        contract_names.append(contract_name)
        # print (df)
    return all_data, contract_names, longest_index

def get_specific_data(contract_name, path = default_path, start_year = 2017, end_year = 2020):
    """get_specific_data returns data for a signle contract from given path following the TB output format,
    it also returns a list of contract names and a list of indecies.

    Parameters
    ----------
    contract_name : str
        name of the contract

    start_year : int
        
    end_year : int
        
    path : str, optional
        file path, by default default_path

    Returns
    -------
    A tuple of data, names, and index
    """
    all_data = {}
    all_files = glob.glob(path + "/" + contract_name + ".csv")
    contract_names = []
    for filename in all_files:
        contract_name = os.path.basename(filename).split(".")[0]
        contract_names.append(contract_name)
        df = pd.read_csv(filename, index_col=None, header=-1,)
        df.columns = ["Date","Hour","Open", "High", "Low", "Close", "Volume", "Open Interest"]
        df['Date']= df['Date'].apply(lambda x: pd.to_datetime(str(x), format='%Y%m%d'))
        df['Hour'] = df['Hour'].apply(lambda x: datetime.timedelta(hours = x/100))
        df['Time'] = df['Date'] + df['Hour']
        df.drop('Hour', axis=1, inplace=True)
        df.drop('Date', axis=1, inplace=True)
        df = df[df['Time'] >= datetime.date(start_year,1,1)]
        df =  df[df['Time'] <= datetime.date(end_year,1,1)]
        df = df.iloc[10:]
        df['Time'] = df['Time'].dt.strftime('%Y-%m-%d-%H')
        df.set_index("Time", inplace = True)
        all_data[contract_name] = df.to_dict('index')
        # print (df)
    return all_data, contract_names, df.index


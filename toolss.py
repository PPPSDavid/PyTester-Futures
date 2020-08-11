import mysql.connector as db
import json
import os
import os.path
import pandas as pd
import pwds

MySQL_HOST = pwds.MySQL_HOST
MySQL_USER = pwds.MySQL_USER
MySQL_PASSWORD = pwds.MySQL_PASSWORD
MySQL_DBNAME = pwds.MySQL_DBNAME
MySQL_PORT = pwds.MySQL_PORT

mydb = db.connect(
    host=MySQL_HOST,
    user=MySQL_USER,
    password=MySQL_PASSWORD,
    db=MySQL_DBNAME,
    port=MySQL_PORT,
    auth_plugin='mysql_native_password'
)
mycursor = mydb.cursor()

def download_size_information():
    """
    download_size_information downloads the price tick and volume multiple from server if not downloaded before

    Returns
    -------
    A tuple of dictionaries
        first being dictionary of vol multiple, second is dict of tick size
    """
    if not os.path.isfile('./tick_multiplier.json'):
        vol = {}
        tick = {}
        sql = 'SELECT name, price_tick, volume_multiple from future_data.future_info'
        mycursor.execute(sql)
        data = mycursor.fetchall()
        for element in data:
            contract = element[0]
            price_tick = element[1]
            volume = element[2]
            vol[contract] = volume
            tick[contract] = price_tick
        with open('volume.json', 'w+') as fp:
            json.dump(vol,fp)
        with open('tick.json', 'w+') as fp:
            json.dump(tick,fp)
        return vol, tick
    else:
        return load_size_information()

def load_size_information():
    """load_size_information load volume and tick data from local file

    Returns
    -------
    A tuple of dictionaries
        first being dictionary of vol multiple, second is dict of tick size
    """
    vol = {}
    tick = {}
    with open('volume.json', 'r') as fp:
        vol = json.load(fp)
    with open('tick.json',  'r') as fp:
        tick = json.load(fp)
    return vol, tick


def data_export_csv(data: dict):
    """data_export_csv export a dict-like dataframe to csv in the same folder

    Parameters
    ----------
    data : dict

    Returns
    -------
    A dataframe that has been written to csv
    """
    result = pd.DataFrame.from_dict(data, orient = 'index')
    result.index = pd.to_datetime(result.index, format = '%Y-%m-%d-%H', errors='ignore')
    result.to_csv('export.csv')
    return result


if __name__ == "__main__":
    a = download_size_information()
    b = download_size_information()

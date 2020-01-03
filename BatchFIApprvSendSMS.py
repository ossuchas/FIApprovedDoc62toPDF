import requests
import json
import logging
import urllib
import pyodbc

import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

import time

# for Logging
import socket

from config import APP_NAME, SMS_APIURL, SMS_MSG

# APP_NAME = "FIAPPROVED"
# SMS_APIURL = 'http://192.168.0.40/smsapi/api/SMS/SendSMS'


class ConnectDB:
    def __init__(self):
        """ Constructor for this class. """
        self._connection = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=192.168.2.58;Database=db_iconcrm_fusion;uid=iconuser;pwd=P@ssw0rd;')
        self._cursor = self._connection.cursor()

    def query(self, query):
        try:
            result = self._cursor.execute(query)
        except Exception as e:
            logging.error('error execting query "{}", error: {}'.format(query, e))
            return None
        finally:
            return result

    def update(self, sqlStatement):
        try:
            self._cursor.execute(sqlStatement)
        except Exception as e:
            logging.error('error execting Statement "{}", error: {}'.format(sqlStatement, e))
            return None
        finally:
            self._cursor.commit()

    def exec_sp(self, sqlStatement, params):
        try:
            self._cursor.execute(sqlStatement, params)
        except Exception as e:
            logging.error('error execting Statement "{}", error: {}'.format(sqlStatement, e))
            return None
        finally:
            self._cursor.commit()

    def exec_spRet(self, sqlStatement, params):
        try:
            result = self._cursor.execute(sqlStatement, params)
        except Exception as e:
            print('error execting Statement "{}", error: {}'.format(sqlStatement, e))
            return None
        finally:
            return result

    def __del__(self):
        self._cursor.close()


def getListData():

    strSQL = """
    SELECT TOP 1 fidoc_id
    FROM dbo.crm_log_fiapproveddoc WITH(NOLOCK)
    WHERE 1=1
	AND sms_flag = 'Y'
	AND ISNULL(sms_sent_stts,'N') NOT IN ('Y','E')
	ORDER BY createdate
    """

    myConnDB = ConnectDB()
    result_set = myConnDB.query(strSQL)
    returnVal = []

    for row in result_set:
        returnVal.append(row.fidoc_id)

    return returnVal


def updateFIApprovedLog(id, send_status):
    myConnDB = ConnectDB()

    params = (send_status, id)

    sqlStmt = """
    UPDATE dbo.crm_log_fiapproveddoc
    SET sms_sent_stts = ?,
        sms_send_date = GETDATE(),
        modifyby = 'batchsms',
        modifydate = GETDATE()
    WHERE fidoc_id = ?
    """
    myConnDB.exec_sp(sqlStmt, params)


def send_sms(dataobj):
    headers = {'Content-type': 'application/json'}
    session = requests.Session()
    return session.post(SMS_APIURL, data=json.dumps(dataobj), headers=headers)


def main():
    # Get Data List
    fidocs = getListData()

    params = "Driver={ODBC Driver 17 for SQL Server};Server=192.168.2.58;\
               Database=db_iconcrm_fusion;uid=iconuser;pwd=P@ssw0rd;"

    params = urllib.parse.quote_plus(params)

    db = create_engine('mssql+pyodbc:///?odbc_connect=%s' % params, fast_executemany=True)

    for id in fidocs:

        str_sql = """
        SELECT a.mobileno, a.transfernumber, a.short_url
        FROM dbo.crm_log_fiapproveddoc a WITH(NOLOCK)
        WHERE a.fidoc_id = {}
        """.format(id)

        df = pd.read_sql(sql=str_sql, con=db)

        # assign variable
        mobile = df.iat[0, 0]
        ref1 = df.iat[0, 1]
        url = df.iat[0, 2]
        # print(mobile)
        # print(ref1)
        # print(url)

        # Kai Fix Mobile No.
        mobile = '0830824173'  # Kai
        # mobile = '0929246354'  # Tai
        # mobile = '0819857023'  # P'Kik
        # mobile = '0814584803'  # Nam

        sms_msg = f"{SMS_MSG}{url}"
        # print("SMS Message = {}".format(sms_msg))
        print("SMS Message = {}".format(sms_msg))

        # Update Status Send Mail Success
        updateFIApprovedLog(id=id, send_status='Y')
        logging.info("Successfully sent sms")

        dataobj = sms_json_model(mobile, sms_msg, ref1)
        print(dataobj)

        response = send_sms(dataobj)
        data = response.json()
        print(data)
        time.sleep(2)


def sms_json_model(mobile: str, sms_msg: str, ref1: str):
    dataobj = [{
        "smsid": 0,
        "sendByApp": APP_NAME,
        "sendDate": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "mobileNumber": mobile,
        "sender": "APRefund",
        "ref1": ref1,
        "ref2": "-",
        "ref3": "-",
        "messageFrom": "APRefund",
        "title": "-",
        "message": sms_msg,
        "sendStatus": "",
        "result": "",
        "fileName": "",
        "fullPath": ""
    }]
    return dataobj


if __name__ == '__main__':
    main()

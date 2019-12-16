import logging
from pathlib import Path
import requests
import os.path
import re
import smtplib
import urllib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from sqlalchemy import create_engine

import pyodbc

REPORT_NAME = "RP_FI_020_62"
REPORT_URL = "http://192.168.0.97/CRMReportWeb/Forms/WF_ReportViewer.aspx?"


class ConnectDB:
    def __init__(self):
        ''' Constructor for this class. '''
        self._connection = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=192.168.0.75;Database=db_iconcrm_fusion;uid=iconuser;pwd=P@ssw0rd;')
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


def send_email(subject, message, from_email, to_email=None, attachment=None):
    """
    :param subject: email subject
    :param message: Body content of the email (string), can be HTML/CSS or plain text
    :param from_email: Email address from where the email is sent
    :param to_email: List of email recipients, example: ["a@a.com", "b@b.com"]
    :param attachment: List of attachments, exmaple: ["file1.txt", "file2.txt"]
    """
    if attachment is None:
        attachment = []
    if to_email is None:
        to_email = []
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ", ".join(to_email)
    msg.attach(MIMEText(message, 'html'))

    for f in attachment:
        with open(f, 'rb') as a_file:
            basename = os.path.basename(f)
            part = MIMEApplication(a_file.read(), Name=basename)

        part['Content-Disposition'] = 'attachment; filename="%s"' % basename
        msg.attach(part)

    email = smtplib.SMTP('apmail.apthai.com', 25)
    email.sendmail(from_email, to_email, msg.as_string())
    email.quit()
    return


def getTransferNumber():
    strSQL = """
    SELECT  DISTINCT TOP 5 TF.TransferNumber
    FROM  [ICON_EntForms_Transfer] TF WITH (NOLOCK)  
    LEFT OUTER JOIN [ICON_EntForms_Agreement] A WITH (NOLOCK)  ON A.ContractNumber = TF.ContractNumber 
    WHERE 1=1 
	AND (TF.NetSalePrice <= 5000000) 
	AND (dbo.fn_ClearTime(TF.TransferDateApprove) BETWEEN '2019-04-30' AND '2019-12-31') 
	ORDER BY TF.TransferNumber
    """

    myConnDB = ConnectDB()
    result_set = myConnDB.query(strSQL)
    returnVal = []

    for row in result_set:
        returnVal.append(row.TransferNumber)

    return returnVal


def rpt2pdf(projectid: str = None, unit_no: str = None):

    file_name = 'pdf/{}_{}.pdf'.format(projectid, unit_no)
    print("##### Generate file {}_{}.pdf #####".format(projectid, unit_no))
    file_full_path = Path(file_name)
    report_url = REPORT_URL
    report_name = 'Report_Name={}'.format(REPORT_NAME)
    userloginid = '&userloginid=2570'
    projectid = '&ProductID={}'.format(projectid)
    comid = '&CompanyID=A'
    unitid = '&UnitID={}'.format(unit_no)
    start_date = '&StartDate=null'
    end_date = '&EndDate=null'
    print_mode = '&PrintMode='
    session = '&SessionID=56a8844b-2e12-4cf0-bfe1-466a90a9ecfa'
    export = '&IsExport=1'

    # concat string
    url = "{}{}{}{}{}{}{}{}{}{}{}".format(report_url, report_name, userloginid,
                                          projectid, comid, unitid, start_date,
                                          end_date, print_mode, session, export)

    session = requests.Session()
    response = session.get(url, stream=True)
    file_full_path.write_bytes(response.content)


def main():
    transfers = getTransferNumber()

    params = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.0.75;Database=db_iconcrm_fusion;uid=iconuser;pwd=P@ssw0rd;'
    params = urllib.parse.quote_plus(params)

    db = create_engine('mssql+pyodbc:///?odbc_connect=%s' % params, fast_executemany=True)

    for transfer in transfers:
        str_sql = """
        SELECT  A.ProductId, A.UnitNumber, FORMAT(TF.TransferDateApprove,'yyyyMMdd') AS TransferDateApprove
        FROM  [ICON_EntForms_Transfer] TF WITH (NOLOCK)  
      LEFT OUTER JOIN [ICON_EntForms_Agreement] A WITH (NOLOCK)  ON A.ContractNumber = TF.ContractNumber 
      WHERE 1=1 
      AND TF.TransferNumber = '{}'
        """.format(transfer)

        df = pd.read_sql(sql=str_sql, con=db)
        product_id =df.iat[0, 0]
        unit_no = df.iat[0, 1]
        transfer_date = df.iat[0, 2]

        # print(product_id, unit_no, transfer_date)
        rpt2pdf(product_id, unit_no)

        receivers = ['suchat_s@apthai.com']
        subject = "test"
        bodyMsg = "test"
        sender = 'noreply@apthai.com'

        attachedFile = ["pdf/{}_{}.pdf".format(product_id, unit_no)]

        # Send Email to Customer
        print("##### Send Mail File {}_{}.pdf #####".format(product_id, unit_no))
        send_email(subject, bodyMsg, sender, receivers, attachedFile)


if __name__ == '__main__':
    main()



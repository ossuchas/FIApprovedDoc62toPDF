import logging
from pathlib import Path
import requests
# import os.path
from os import path, environ, remove
import re
import smtplib
import urllib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from sqlalchemy import create_engine
from config import REPORT_URL, REPORT_NAME, \
    MINIO_ACCESS_KEY, MINIO_BUCKET_NAME, MINIO_ENDPOINT, MINIO_SECRET_KEY, \
    MAIL_SENDER, MAIL_SUBJECT, MAIL_BODY, EMAIL_FORMAT, BITLY_ACCESS_TOKEN

import pyodbc
import bitly_api

from minio import Minio
from minio.error import ResponseError

regex = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"


class ConnectDB:
    def __init__(self):
        ''' Constructor for this class. '''
        self._connection = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};Server=192.168.2.58;Database=db_iconcrm_fusion;uid=iconuser;pwd=P@ssw0rd;')
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
            basename = path.basename(f)
            part = MIMEApplication(a_file.read(), Name=basename)

        part['Content-Disposition'] = 'attachment; filename="%s"' % basename
        msg.attach(part)

    email = smtplib.SMTP('apmail.apthai.com', 25)
    email.sendmail(from_email, to_email, msg.as_string())
    email.quit()
    return


def getTransferNumber():
    # strSQL = """
    # SELECT  DISTINCT TOP 1 TF.TransferNumber
    # FROM  [ICON_EntForms_Transfer] TF WITH (NOLOCK)
    # LEFT OUTER JOIN [ICON_EntForms_Agreement] A WITH (NOLOCK)  ON A.ContractNumber = TF.ContractNumber
    # LEFT OUTER JOIN [ICON_EntForms_AgreementOwner] AO WITH (NOLOCK)  ON AO.ContractNumber = A.ContractNumber AND AO.Header = 1
    # WHERE 1=1
	# AND (TF.NetSalePrice <= 5000000)
	# AND (dbo.fn_ClearTime(TF.TransferDateApprove) BETWEEN '2019-04-30' AND '2019-12-31')
	# AND TF.TransferNumber NOT IN (SELECT FI.transfernumber FROM dbo.crm_log_fiapproveddoc FI (NOLOCK))
	# AND dbo.fn_ChckNationalityTHFE( AO.ContactID) = 'T'
	# --AND a.ProductID = '10096'
	# ORDER BY TF.TransferNumber
    # """
    strSQL = """
    SELECT  DISTINCT TOP 5 TF.TransferNumber + '-' + TN.ContactID AS TransferNumber
    FROM  [ICON_EntForms_Transfer] TF WITH (NOLOCK)
    LEFT OUTER JOIN [ICON_EntForms_Agreement] A WITH (NOLOCK)  ON A.ContractNumber = TF.ContractNumber
    LEFT OUTER JOIN [ICON_EntForms_AgreementOwner] AO WITH (NOLOCK)  ON AO.ContractNumber = A.ContractNumber AND AO.Header = 1
	LEFT OUTER JOIN [ICON_EntForms_TransferOwner] TN WITH (NOLOCK)  ON TN.TransferNumber = TF.TransferNumber AND TN.IsDelete = 0
    WHERE 1=1
	AND (TF.NetSalePrice <= 5000000)
	AND (dbo.fn_ClearTime(TF.TransferDateApprove) BETWEEN '2019-04-30' AND '2019-12-31')
	AND TF.TransferNumber NOT IN (SELECT FI.transfernumber FROM dbo.crm_log_fiapproveddoc FI (NOLOCK))
	AND dbo.fn_ChckNationalityTHFE( AO.ContactID) = 'T'
	ORDER BY TF.TransferNumber + '-' + TN.ContactID
        """

    myConnDB = ConnectDB()
    result_set = myConnDB.query(strSQL)
    returnVal = []

    for row in result_set:
        returnVal.append(row.TransferNumber)

    return returnVal


def getListEmailbyTransferNo(transfernumb: str = None):

    strSQL = """
    SELECT ISNULL(b.EMail, '-') as Email
    FROM dbo.ICON_EntForms_TransferOwner a WITH(NOLOCK),
    dbo.ICON_EntForms_Contacts b WITH(NOLOCK)
    WHERE a.TransferNumber = '{}' 
    AND a.IsDelete = 0
    AND a.ContactID = b.ContactID
        """.format(transfernumb)

    myConnDB = ConnectDB()
    result_set = myConnDB.query(strSQL)
    returnVal = []

    for row in result_set:
        if validateEmail(row.Email):
            returnVal.append(row.Email)

    return returnVal


def rpt2pdf(projectid: str = None, unit_no: str = None, file_full_path: str = None):
    # file_name = 'pdf/{}_{}.pdf'.format(projectid, unit_no)
    print("##### Generate file {}_{}.pdf #####".format(projectid, unit_no))
    file_full_path = Path(file_full_path)
    report_url = REPORT_URL
    report_name = 'Report_Name={}'.format(REPORT_NAME)
    userloginid = '&userloginid=2607'
    projectid = '&ProductID={}'.format(projectid)
    comid = '&CompanyID=A'
    unitid = '&UnitID={}'.format(unit_no)
    start_date = '&StartDate=null'
    end_date = '&EndDate=null'
    print_mode = '&PrintMode='
    session = '&SessionID=198b9ce1-b364-4a6c-9d4f-06d3e9502ada'
    export = '&IsExport=1'

    # concat string
    url = "{}{}{}{}{}{}{}{}{}{}{}".format(report_url, report_name, userloginid,
                                          projectid, comid, unitid, start_date,
                                          end_date, print_mode, session, export)
    # print(url)
    session = requests.Session()
    response = session.get(url, stream=True)
    file_full_path.write_bytes(response.content)


def validateEmail(email):
    if re.search(regex, email):
        return True
    else:
        return False


def push2minio(filename: str = None, file_full_path: str = None):
    minioClient = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=None)
    # Put file to minIO
    try:
        minioClient.fput_object(MINIO_BUCKET_NAME, filename, file_full_path, content_type='application/pdf')
    except ResponseError as err:
        return "Error {}".format(err)


def insertlog(productid: str = None, unitnumber: str = None, transfernumber: str = None, url_file: str = None,
              send_mail_stts: str = None, sms_flag: str = None, short_url: str = None,
              contactid: str = None, mobileno: str = None):
    strSQL = """
    INSERT INTO dbo.crm_log_fiapproveddoc
    ( productid, unitnumber, transfernumber, url_file, short_url, send_mail_stts,  sms_flag,
    createby, createdate, modifyby, modifydate, contactid, mobileno)
    VALUES(?, ?, ?, ?, ?, ?, ?, 'batchfi', GETDATE(), 'batchfi', GETDATE(), ?, ?)
        """
    param = (productid, unitnumber, transfernumber, url_file, short_url, send_mail_stts, sms_flag, contactid, mobileno)
    myConnDB = ConnectDB()
    myConnDB.exec_sp(strSQL, params=param)


def delpdffile(file_full_path: str = None):
    remove(file_full_path)


def generate_shorturl(long_url: str = None, ACCESS_TOKEN: str = None) -> str:
    b = bitly_api.Connection(access_token=ACCESS_TOKEN)
    response = b.shorten(long_url)
    return response['url']


def main():
    # GET transfer number list
    transfers = getTransferNumber()

    params = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.2.58;Database=db_iconcrm_fusion;uid=iconuser;pwd' \
             '=P@ssw0rd; '
    params = urllib.parse.quote_plus(params)
    db = create_engine('mssql+pyodbc:///?odbc_connect=%s' % params, fast_executemany=True)

    for transfer in transfers:
        tf_val = transfer.split('-')[0]
        contactid_val = transfer.split('-')[1]
        # print(tf_val)
        # print(contactid_val)

        # str_sql = """
        # SELECT  A.ProductId, A.UnitNumber, FORMAT(TF.TransferDateApprove,'yyyyMMdd') AS TransferDateApprove
        # FROM  [ICON_EntForms_Transfer] TF WITH (NOLOCK)
        # LEFT OUTER JOIN [ICON_EntForms_Agreement] A WITH (NOLOCK)  ON A.ContractNumber = TF.ContractNumber
        # WHERE 1=1
        # AND TF.TransferNumber = '{}'
        # """.format(transfer)

        str_sql = """
        SELECT  A.ProductId, A.UnitNumber, FORMAT(TF.TransferDateApprove,'yyyyMMdd') AS TransferDateApprove, TN.Mobile
        FROM  [ICON_EntForms_Transfer] TF WITH (NOLOCK)
        LEFT OUTER JOIN [ICON_EntForms_Agreement] A WITH (NOLOCK)  ON A.ContractNumber = TF.ContractNumber
		LEFT OUTER JOIN [ICON_EntForms_TransferOwner] TN WITH (NOLOCK)  ON TN.TransferNumber = TF.TransferNumber 
        WHERE 1=1
        AND TF.TransferNumber = '{}'
		AND TN.ContactID = '{}'
        """.format(tf_val, contactid_val)

        df = pd.read_sql(sql=str_sql, con=db)
        product_id = df.iat[0, 0]
        unit_no = df.iat[0, 1]
        transfer_date = df.iat[0, 2]
        mobile_no = df.iat[0, 3]
        send_mail_stts = 'F'
        sms_flag = 'N'

        # print(mobile_no)

        # print(product_id, unit_no, transfer_date)
        file_name = "{}_{}.pdf".format(product_id, unit_no)
        file_full_path = "pdf/{}".format(file_name)
        rpt2pdf(product_id, unit_no, file_full_path)

        # receivers = ['suchat_s@apthai.com', 'jintana_i@apthai.com', 'wallapa@apthai.com']
        emaillist = getListEmailbyTransferNo(transfer)
        # emaillist = getListEmailbyTransferNo('30002CT9173347')

        # Check Email valid and sending
        if emaillist:
            print(emaillist)
            send_mail_stts = 'S'
            receivers = ['suchat_s@apthai.com']
            subject = "{} ({}:{})".format(MAIL_SUBJECT, product_id, unit_no)
            bodyMsg = MAIL_BODY
            sender = MAIL_SENDER

            attachedFile = [file_full_path]

            # Send Email to Customer
            print("##### Send Mail File {}_{}.pdf #####".format(product_id, unit_no))
            send_email(subject, bodyMsg, sender, receivers, attachedFile)

        print("##### Push to MinIO {} #####".format(file_name))
        push2minio(file_name, file_full_path)

        print("##### Delete file {} #####".format(file_name))
        delpdffile(file_full_path)

        url_file = "https://happyrefund.apthai.com/datashare/crmfiapproveddoc/{}".format(file_name)

        print("##### Generate Shorten URL {} #####".format(file_name))
        short_url = generate_shorturl(long_url=url_file, ACCESS_TOKEN=BITLY_ACCESS_TOKEN)
        print(short_url)

        print("##### Insert Log FI {} {} #####".format(product_id, unit_no))
        if send_mail_stts == 'F':
            sms_flag = 'Y'
        insertlog(product_id, unit_no, tf_val, url_file, send_mail_stts, sms_flag, short_url,
                  contactid_val, mobile_no)


if __name__ == '__main__':
    main()

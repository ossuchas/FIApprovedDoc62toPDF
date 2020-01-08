import os
import urllib

DEBUG = True
REPORT_NAME = "RP_FI_020_62"
# URL Test
# REPORT_URL = "http://192.168.0.97/CRMReportWeb/Forms/WF_ReportViewer.aspx?"

# URL Prod
REPORT_URL = "http://ap-ir.com/CRMReportWeb/Forms/WF_ReportViewer.aspx?"

EMAIL_FORMAT = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"

# MINIO Dev Env
# MINIO_ENDPOINT = "192.168.2.29:9400"
# MINIO_ACCESS_KEY = "MD6RUWLB2UL23HWWIQ95"
# MINIO_SECRET_KEY = "z+vz7XsjRsjxAqbH3ntzLNp9gf9GqgwKpnzzWeQf"
# MINIO_BUCKET_NAME = "crmfiapproveddoc"

# MINIO Prod Env
MINIO_ENDPOINT = "192.168.3.11:9400"
MINIO_ACCESS_KEY = "RG7LY045BY4EW2Z9O1Z0"
MINIO_SECRET_KEY = "ZXnvVWe9LcsticSFxJVJzy2imOIWU+oT7TZpIPVA"
MINIO_BUCKET_NAME = "crmfiapproveddoc"

# Mail Setting
MAIL_SENDER = "noreply@apthai.com"
MAIL_SUBJECT = "หนังสือประกอบการยื่นยกเว้นภาษี กรณีบ้านหลังแรก"
MAIL_BODY = """<p style="font-family:AP;">เรียนลูกค้า<br>&nbsp;&nbsp;&nbsp;&nbsp;\
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;กลุ่มบริษัทเอพี ขอจัดส่งหนังสือรับรองจำนวนเงินที่ชำระค่าซื้ออสังหาริมทรัพย์ \
    เพื่อใช้ประกอบการยื่นยกเว้นภาษี กรณีบ้านหลังแรก \
    <br />ลูกค้าสามารถดาวน์โหลดแบบฟอร์มได้ตามไฟส์แนบ \
    <br /><p style="font-family:AP;"><a href="http://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg353.pdf">\
    ประกาศจากกรมสรรพากร</a></p><br /><br  /> \
    ขอแสดงความนับถือ<br /><img src="http://www.apintranet.com/static/media/logo.d9fe4116.png"\
    alt="ap" width="5%" ><br />บมจ.เอพี (ไทยแลนด์) และบริษัทในเครือ<br /></p>"""

# Bitly shorten url
# BITLY_ACCESS_TOKEN = "43280e02fc4a96a4eafa456cc054b49895db00f3"  # Gmail suchat.s14102526@gmail.com
BITLY_ACCESS_TOKEN = "82a0df35c581df9c1732293afb1b1dab91797945"  # Gmail ap2020fi01@gmail.com


# SEND SMS
APP_NAME = "FIAPPROVED"
SMS_APIURL = "http://192.168.0.40/smsapi/api/SMS/SendSMS"
SMS_MSG = "กลุ่ม บ.เอพี ขอจัดส่งหนังสือประกอบการยื่นยกเว้นภาษี กรณีบ้านหลังแรก ดาวน์โหลดเอกสารได้ที่ "

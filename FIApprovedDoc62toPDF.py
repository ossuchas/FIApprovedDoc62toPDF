from pathlib import Path
import requests


def rpt2pdf():
    file_name = 'FI_90307543_60018CT9200274.pdf'
    file_full_path = Path(file_name)
    # report_url = 'http://ap-ir.com/CRMReportWeb/Forms/WF_ReportViewer.aspx?'
    report_url = 'http://192.168.0.97/CRMReportWeb/Forms/WF_ReportViewer.aspx?'
    report_name = 'Report_Name=RP_FI_020_62'
    userloginid = '&userloginid=2570'
    projectid = '&ProductID=40017'
    comid = '&CompanyID=A'
    unitid = '&UnitID=N06B11'
    start_date = '&StartDate=null'
    end_date = '&EndDate=null'
    print_mode = '&PrintMode='
    session = '&SessionID=56a8844b-2e12-4cf0-bfe1-466a90a9ecfa'
    export = '&IsExport=1'

    # concat string
    url = "{}{}{}{}{}{}{}{}{}{}{}".format(report_url, report_name, userloginid,
                                          projectid, comid, unitid, start_date,
                                          end_date, print_mode, session, export)

    response = requests.get(url, stream=True)
    file_full_path.write_bytes(response.content)


def main():
    rpt2pdf()


if __name__ == '__main__':
    main()



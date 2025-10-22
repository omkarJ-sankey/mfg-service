"""payments helper functions"""
#  File details-
#   Author      - Manish Pawar
#   Description - Payments helper function.
#   Name        - payments helper function
#   Modified by - Manish Pawar

# These are all the imports that we are exporting from
# different module's from project or library.
import json
from decouple import config
import traceback

import io

from datetime import datetime, timedelta
from io import StringIO
import xlsxwriter
# pylint:disable=import-error
from .sentry_tracers import traced_request
from .constants import SQUARE_BASE_URL, REQUEST_API_TIMEOUT
from .model_files.station_models import ServiceConfiguration
from django.http import HttpResponse
from cryptography.fernet import Fernet

from .common import string_to_array_converter

def make_request(method, sub_url, user_id="Anonymous", data="", module=""):
    """this function is used to call APIs"""
    square_headers = {
        "Square-Version": "2023-03-15",
        "Authorization": f"Bearer {config('DJANGO_PAYMENT_ACCESS_TOKEN')}",
        "Content-Type": "application/json",
    }
    response = traced_request(
        method.upper(),
        f"{SQUARE_BASE_URL}{sub_url}",
        data=json.dumps(data) if data else data,
        headers=square_headers,
        timeout=REQUEST_API_TIMEOUT
    )
    if response.status_code != 200:
        print(
            f"Response error data for '{module}' for user -> {user_id} is ==>"
        )
        print(response.content)
    return response

def export_payments_data_function(
    table, columns_for_sheet, rows_for_sheet, filenames
):
    """common function to export data in sheet"""
    try:
        output = io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        bold = workbook.add_format({"bold": True})
        for file_index, filename in enumerate(filenames):
            worksheet = workbook.add_worksheet(filename)
            row_num = 0
            # Insertinh header row of sheet
            columns = columns_for_sheet[file_index]
            for count, column_item in enumerate(columns):
                worksheet.write(row_num, count, column_item, bold)

            # Inserting other rows in sheet
            for data in table:
                
                row_num += 1
                col_num = 0

                for row in rows_for_sheet[file_index]:
                    if row == "emp_session_id":
                        if data["is_ocpi"] == True:
                            if data["session_id"] is None or data["session_id"] == "nan":
                                worksheet.write(row_num, col_num, str(""))
                                col_num += 1
                                continue
                            worksheet.write(row_num, col_num, str(data["session_id"]))
                            col_num += 1
                            continue
                        worksheet.write(row_num, col_num, str(data[row]))
                        col_num += 1
                        continue
                    if row == "user_id__username":
                        if data["key"] is None:
                            worksheet.write(row_num, col_num, "Not Available")
                            col_num += 1
                            continue
                        decrypter = Fernet(data["key"])
                        decrypted_email = decrypter.decrypt(
                            data["email"]
                        ).decode()
                        worksheet.write(row_num, col_num, str(decrypted_email))
                        col_num += 1
                        continue
                    if row == "key" or row == 'email':
                        continue
                    if row == "total_cost":
                        if data["is_ocpi"] == True:
                            if data["total_cost_incl"] is None or data["total_cost_incl"] == "nan":
                                worksheet.write(row_num, col_num, str(""))
                                col_num += 1
                                continue
                            worksheet.write(row_num, col_num, str(int(float(data["total_cost_incl"])*100)))
                            col_num += 1
                            continue
                        worksheet.write(row_num, col_num, str(data[row]))
                        col_num += 1
                        continue
                    if row == "end_time":
                        if data["is_ocpi"] == True:
                            if data["end_datetime"] is None or data["end_datetime"] == "nan":
                                worksheet.write(row_num, col_num, str(""))
                                col_num += 1
                                continue
                            worksheet.write(row_num, col_num, str(data["end_datetime"]))
                            col_num += 1
                            continue
                        worksheet.write(row_num, col_num, str(data[row]))
                        col_num += 1
                        continue
                    if data[row] is None or data[row] == "nan":
                        worksheet.write(row_num, col_num, str(""))
                        col_num += 1
                        continue
                    if row == "payment_terminal":
                        worksheet.write(
                            row_num,
                            col_num,
                            str(
                                "|".join(
                                    string_to_array_converter(
                                        data[row]
                                    )
                                )
                            ).replace("Worldline", "Receipt Hero"),
                        )
                        col_num += 1
                        continue
                    if row == "amenities" and filename == "Valeting Terminals":
                        worksheet.write(
                            row_num,
                            col_num,
                            str(
                                "|".join(
                                    list(
                                        ServiceConfiguration.objects.filter(
                                            id__in=string_to_array_converter(
                                                data[row]
                                            )
                                        ).values_list("service_name", flat=True)
                                    )
                                )
                            ),
                        )
                    else:
                        worksheet.write(row_num, col_num, str(data[row]))
                    col_num += 1

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)
        # Set up the Http response.
        filename = f"{filenames[0] + str(datetime.now().date())}.xlsx"
        response = HttpResponse(
            output,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except Exception as e:
        traceback.print_exc()
        return None

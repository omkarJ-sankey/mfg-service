"""bulk upload functions"""
# Date - 23/11/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on bulk upload of promotions.
#   Name            - Promotions Bulk upload functions
#   Modified by     - Manish Pawar
#   Modified date   - 23/11/2021

# imports required to create views
import threading
from datetime import datetime
import concurrent.futures
import pytz
import pandas as pd
from django.utils import timezone

# pylint:disable=import-error
from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.model_files.promotions_models import Promotions
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.common import (
    array_to_string_converter,
    field_checker_func,
    field_tracking_func,
    remove_whitespace,
    error_messages_object_formatter,
    upload_progress_database,
    upload_progress_errors_database,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.constants import (
    UNQUIE_BAR_CODE,
    UNQUIE_RETAILBAR_CODE,
    YES,
    NO,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    PROMOTIONS_CONST,
)
from adminServices.admin_app_level_constants import UPLOAD_RESPONSE
from .db_operators import (
    create_promotion_func,
    update_promotion_func,
    handle_promotion_assignment,
)
from .views import remove_promotions_cached_data
from .app_level_constants import (
    LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS,
    LIST_OF_FILDS_FOR_PROMOTIONS,
    LIST_OF_FILDS_FOR_PROMOTIONS_ASSIGN,
    LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN,
)
from .bulk_upload_helper_functions import promotion_assign_bulk_upload


def add_audit_data_for_promotions(promotion_ids, user):
    """this function adds audit data for bulk uploaded functions"""

    def add_promotion_audit_data(promotion_id):
        """this function adds promotion audit data in background"""
        promotion = Promotions.objects.filter(
            unique_code=promotion_id
        ).first()

        if promotion is None:
            return None
        audit_entry = AuditTrail.objects.filter(
            data_db_id=f"{PROMOTIONS_CONST}-{promotion.id}"
        ).last()
        new_data = audit_data_formatter(PROMOTIONS_CONST, promotion.id)
        old_data = audit_entry.new_data
        if old_data == new_data:
            return None
        if audit_entry:
            add_audit_data(
                user,
                (promotion.unique_code + ", " + promotion.promotion_title),
                f"{PROMOTIONS_CONST}-{promotion.id}",
                AUDIT_UPDATE_CONSTANT,
                PROMOTIONS_CONST,
                new_data,
                old_data,
            )
        else:
            add_audit_data(
                user,
                (promotion.unique_code + ", " + promotion.promotion_title),
                f"{PROMOTIONS_CONST}-{promotion.id}",
                AUDIT_ADD_CONSTANT,
                PROMOTIONS_CONST,
                new_data,
                None,
            )
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        executor.map(
            add_promotion_audit_data,
            list(promotion_ids),
        )


def background_functions_of_bulk_upload(*arg):
    """this functions runs all functions of Bulk upload in the background"""
    list_of_arg = list(arg)
    total_data_lenght = (
        len(list_of_arg[0]) + len(list_of_arg[1]) + len(list_of_arg[2])
    )
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions", uploading_status="uploading"
    )
    if promotion_bulk_upload_progress.first():
        total_count = (
            int(promotion_bulk_upload_progress.first().total_rows_count)
            + total_data_lenght
        )
        promotion_bulk_upload_progress.update(
            total_rows_count=total_count, uploading_status="uploading"
        )
    try:
        create_promotion_func(list_of_arg[0])
        update_promotion_func(list_of_arg[1])
        handle_promotion_assignment(list_of_arg[2])

        add_audit_data_for_promotions(
            [
                added_promotions.unique_code
                for added_promotions in list_of_arg[0]
            ]
            + [
                updated_promotions["unique_code"]
                for updated_promotions in list_of_arg[1]
            ],
            list_of_arg[3],
        )
    except TimeoutError:
        promotion_bulk_upload_progress.update(
            total_rows_count=0,
            uploaded_rows_count=0,
            uploading_status="completed",
        )
    after_promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions", uploading_status="uploading"
    )
    after_promotion_bulk_upload_progress.update(
        total_rows_count=0, uploaded_rows_count=0, uploading_status="completed"
    )
    remove_promotions_cached_data()


def promotions_bulk_date_formatter(date, is_start):
    """this is date formaater to format string date to datetime"""
    try:
        str_date = str(date.date()).split("-")
    except AttributeError:
        str_date = str(date).split("-")
    date_in_format = f"{str_date[1]}/{str_date[2]}/{str_date[0]}"
    date_one = datetime.strptime(date_in_format, "%m/%d/%Y")
    if is_start:
        newdatetime = date_one.replace(hour=0, minute=0, tzinfo=pytz.UTC)
    else:
        newdatetime = date_one.replace(hour=23, minute=59, tzinfo=pytz.UTC)
    newdatetime = timezone.localtime(newdatetime)
    return newdatetime


def add_update_promotions_bulk_upload(*args):
    """promotion bulk upload function"""
    (
        data_frame,
        list_of_fields,
        promotion_assign_set,
        promotions_assign_data_frame,
        user,
        list_of_fields_for_iteration,
        promotions_from_sheet,
    ) = args
    promotions_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
    )
    promotions_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="promotions"
    )
    upload_progress_errors_database("promotions", promotions_error_records)
    promotions_queryset = Promotions.objects.filter()

    # arrays to make db operations
    promotion_data_for_create = []
    promotion_data_for_update = []

    promotions_error_tracker = []

    def upload_promotion_data(i):
        error_tracker_promotions = []
        if (
            remove_whitespace(
                str(promotions_assign_data_frame[UNQUIE_BAR_CODE][i])
            )
            not in promotion_assign_set
        ):
            error_tracker_promotions.append(
                error_messages_object_formatter(
                    [UNQUIE_RETAILBAR_CODE, "Error"],
                    [
                        f"{data_frame['Unique/Barcode'][i]} \
                        (Promotions Tab)",
                        'Please provide promotion assignment data in \
                                "Promotion assign tab"',
                    ],
                )
            )
            return error_tracker_promotions

        validator = field_checker_func(list_of_fields, data_frame, i)
        if validator[0]:
            validator_one_promotions = field_checker_func(
                list_of_fields_for_iteration, data_frame, i
            )
            if len(list_of_fields_for_iteration) != len(
                validator_one_promotions[1]
            ):
                error_message_text_promotions = ""
                for f_error in validator[1]:
                    if len(error_message_text_promotions) > 0:
                        error_message_text_promotions += f", {f_error}"
                    else:
                        error_message_text_promotions = f_error
                error_tracker_promotions.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{data_frame['Unique/Barcode'][i]} \
                                (Promotions Tab)",
                            f'Please provide these required fields \
                                -> "{error_message_text_promotions}"',
                        ],
                    )
                )
            return error_tracker_promotions
        start_time = None
        end_time = None
        try:
            start_time = promotions_bulk_date_formatter(
                data_frame["Start date"][i], True
            )
            end_time = promotions_bulk_date_formatter(
                data_frame["End date"][i], False
            )
        except AttributeError:
            error_tracker_promotions.append(
                error_messages_object_formatter(
                    [UNQUIE_RETAILBAR_CODE, "Error"],
                    [
                        f"{data_frame['Unique/Barcode'][i]}\
                            (Promotions Tab)",
                        "Start and/or End date format is not as \
                            per the valid rule.",
                    ],
                )
            )
        promotion_exists = promotions_queryset.filter(
            unique_code=remove_whitespace(str(data_frame[UNQUIE_BAR_CODE][i]))
        )
        promotion_status = "Active"
        if not pd.isna(data_frame["Status(Active/Inactive)"][i]):
            promotion_status = data_frame["Status(Active/Inactive)"][i]
        if promotion_exists.first():
            promotion_data_for_update.append(
                {
                    "unique_code": remove_whitespace(
                        str(data_frame[UNQUIE_BAR_CODE][i])
                    ),
                    "product": data_frame["Product"][i],
                    "retail_barcode": data_frame["Retail code"][i],
                    "promotion_title": data_frame["Promotion title"][i],
                    "m_code": remove_whitespace(str(data_frame["M Code"][i])),
                    "status": promotion_status,
                    "start_date": start_time,
                    "end_date": end_time,
                    "available_for": data_frame["Available for"][i],
                    "offer_type": data_frame["Offer type"][i],
                    "londis_code": data_frame["Londis code"][i],
                    "budgen_code": data_frame["Budgens code"][i],
                    "price": float(data_frame["Product price"][i]),
                    "quantity": float(data_frame["Quantity"][i]),
                    "offer_details": data_frame["Offer details"][i],
                    "deleted": NO,
                    "terms_and_conditions": data_frame["Terms and condition"][
                        i
                    ],
                    "updated_date": timezone.localtime(timezone.now()),
                    "updated_by": user.full_name,
                }
            )
        else:
            promotion_data_for_create.append(
                Promotions(
                    unique_code=remove_whitespace(
                        str(data_frame[UNQUIE_BAR_CODE][i])
                    ),
                    retail_barcode=data_frame["Retail code"][i],
                    product=data_frame["Product"][i],
                    promotion_title=data_frame["Promotion title"][i],
                    m_code=remove_whitespace(str(data_frame["M Code"][i])),
                    status=promotion_status,
                    start_date=start_time,
                    end_date=end_time,
                    available_for=data_frame["Available for"][i],
                    offer_type=data_frame["Offer type"][i],
                    londis_code=data_frame["Londis code"][i],
                    budgen_code=data_frame["Budgens code"][i],
                    price=float(data_frame["Product price"][i]),
                    quantity=float(data_frame["Quantity"][i]),
                    offer_details=data_frame["Offer details"][i],
                    terms_and_conditions=data_frame["Terms and condition"][i],
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )
            )
        return error_tracker_promotions

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(
            upload_promotion_data,
            list(range(0, len(data_frame[UNQUIE_BAR_CODE]))),
        )
        for result in results:
            if len(result) > 0:
                promotions_error_tracker += result

    current_count = int(
        promotions_bulk_upload_progress.first().uploaded_rows_count
    ) + len(promotions_from_sheet)
    promotions_bulk_upload_progress.update(uploaded_rows_count=current_count)
    return [
        promotion_data_for_create,
        promotion_data_for_update,
        promotions_error_tracker,
    ]


def promotions_assign_add_update_bulk_upload(*args):
    """promotion bulk upload function"""
    (
        promotion_assign_set,
        promotions_assign_data_frame,
        user,
        promotions_assign_list_of_fields,
        promotions_assign_list_of_fields_for_iteration,
    ) = args
    promotions_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
    )
    promotions_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="promotions"
    )
    upload_progress_errors_database("promotions", promotions_error_records)

    # arrays to make db operations
    promotions_assignment_data = []
    promotions_assign_error_tracker = []

    for promotion_assignment_number in list(
        range(0, len(promotions_assign_data_frame[UNQUIE_BAR_CODE]))
    ):
        results, promotion_assignment = promotion_assign_bulk_upload(
            promotion_assignment_number,
            promotions_assign_list_of_fields,
            promotions_assign_data_frame,
            promotion_assign_set,
            promotions_assignment_data,
            user,
            promotions_assign_list_of_fields_for_iteration,
        )
        if len(results) > 0:
            promotions_assign_error_tracker += results
        if promotion_assignment:
            promotions_assignment_data += promotion_assignment
    current_count = int(
        promotions_bulk_upload_progress.first().uploaded_rows_count
    ) + len(promotion_assign_set)
    promotions_bulk_upload_progress.update(uploaded_rows_count=current_count)

    return [promotions_assignment_data, promotions_assign_error_tracker]


def promotions_bulk_upload(*args):
    """promotion bulk upload function"""
    (
        data_frame,
        list_of_fields,
        promotion_assign_set,
        promotions_assign_data_frame,
        user,
        list_of_fields_for_iteration,
        promotions_from_sheet,
        promotions_assign_list_of_fields,
        promotions_assign_list_of_fields_for_iteration,
    ) = args
    promotions_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="promotions"
    )
    upload_progress_errors_database("promotions", promotions_error_records)
    promotions_errors = []
    (
        promotion_data_for_create,
        promotion_data_for_update,
        promotions_error_tracker,
    ) = add_update_promotions_bulk_upload(
        data_frame,
        list_of_fields,
        promotion_assign_set,
        promotions_assign_data_frame,
        user,
        list_of_fields_for_iteration,
        promotions_from_sheet,
    )

    (
        promotions_assignment_data,
        promotions_assign_error_tracker,
    ) = promotions_assign_add_update_bulk_upload(
        promotion_assign_set,
        promotions_assign_data_frame,
        user,
        promotions_assign_list_of_fields,
        promotions_assign_list_of_fields_for_iteration,
    )

    promotions_errors.append(
        {"tab": "Promotions Tab", "errors": promotions_error_tracker}
    )
    promotions_errors.append(
        {
            "tab": "Promotion Assign Tab",
            "errors": promotions_assign_error_tracker,
        }
    )
    promotions_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="promotions"
    )
    if promotions_error_records.first():
        promotions_error_records.update(
            errors=array_to_string_converter(promotions_errors),
            ready_to_export=YES,
        )
    start_time = threading.Thread(
        target=background_functions_of_bulk_upload,
        args=[
            promotion_data_for_create,
            promotion_data_for_update,
            promotions_assignment_data,
            user
        ],
        daemon=True
    )
    start_time.start()


def promotions_bulk_upload_function(sheet, user, promotion_assign_sheet):
    """promotions bulk upload function"""
    data_frame = sheet
    field_tracker_promotions = []
    sheet_have_field_errors = False
    sheet_field_errors_response = {
        "status": True,
        "data": {"fields": False, "data": []},
        "c_data": {"fields": False, "data": field_tracker_promotions},
    }

    if UNQUIE_BAR_CODE in promotion_assign_sheet:
        promotion_assign_set = list(promotion_assign_sheet[UNQUIE_BAR_CODE])
        promotion_assign_set = [
            remove_whitespace(str(pr)) for pr in promotion_assign_set
        ]
    if UNQUIE_BAR_CODE in sheet:
        promotions_from_sheet = list(sheet[UNQUIE_BAR_CODE])

    list_of_fields_promotions = LIST_OF_FILDS_FOR_PROMOTIONS
    list_of_fields_for_iteration_promotions = (
        LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS
    )
    field_tracker_promotions = field_tracking_func(
        list_of_fields_for_iteration_promotions, data_frame
    )
    if len(field_tracker_promotions) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["data"] = {
            "fields": True,
            "data": field_tracker_promotions,
        }

    promotions_assign_data_frame = promotion_assign_sheet
    field_tracker_promotions = []
    promotions_assign_list_of_fields = LIST_OF_FILDS_FOR_PROMOTIONS_ASSIGN
    promotions_assign_list_of_fields_for_iteration = (
        LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN
    )
    field_tracker_promotions = field_tracking_func(
        promotions_assign_list_of_fields_for_iteration,
        promotions_assign_data_frame,
    )
    if len(field_tracker_promotions) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["c_data"] = {
            "fields": True,
            "data": field_tracker_promotions,
        }
    if sheet_have_field_errors is True:
        return sheet_field_errors_response

    total_data_count = len(promotion_assign_set) + len(promotions_from_sheet)
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
    )
    upload_progress_database(
        "promotions", promotion_bulk_upload_progress, total_data_count
    )

    start_time = threading.Thread(
        target=promotions_bulk_upload,
        args=[
            data_frame,
            list_of_fields_promotions,
            promotion_assign_set,
            promotions_assign_data_frame,
            user,
            list_of_fields_for_iteration_promotions,
            promotions_from_sheet,
            promotions_assign_list_of_fields,
            promotions_assign_list_of_fields_for_iteration,
        ],
        daemon=True
    )
    start_time.start()

    return UPLOAD_RESPONSE

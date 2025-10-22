"""email and sms common functions"""

import json
import secrets
import base64
import os
from datetime import datetime
import pytz
from decouple import config
from django.utils import timezone

from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)

from .model_files.config_models import (
    BaseConfigurations,
)
from .payments_helper_function import make_request
from .constants import (
    ADMIN_OTP,
    DELETE_ACCOUNT,
    FORGET_PASS_CONST,
    NEW_LOGGED_IN_USER,
    OTP_NUMBER_END_POINT,
    OTP_NUMBER_START_POINT,
    OTP_NUMBER_START_POINT_FOR_SMS,
    OTP_NUMBER_END_POINT_FOR_SMS,
    REGISTER,
    SEND_EMAIL_VALUE,
    SEND_EMAIL_NAME_VALUE,
    ROOT_URL,
    DELETED_ACCOUNT,
    SMS_FROM_STRING,
    DEFAULT_OTP_MESSAGE,
    DEFAULT_FROM_SMS,
    SWARCO,
    DRIIVZ,
    DRIIVZ_START_ON,
    DRIIVZ_STOP_ON,
    KWH,
    SWARCO_END_TIME,
    SWARCO_START_TIME,
    TOTAL_ENERGY,
    DATE_TIME_FORMAT,
    GET_REQUEST,
    NOT_AVAILABLE,
    EMAIL_ID_FOR_ERROR_EMAIL_ALERT,
    DEFAULT_EMAIL_ID_FOR_ERROR_EMAIL_ALERT,
    MFG_ADMIN,
    BLOCKED_USERS_PHONE_LIST,
    BLOCKED_USERS_EMAILS_LIST
)
from .common import (
    redis_connection,
    time_formatter_for_hours,
    filter_function_for_base_configuration
)

twilio_client = Client(
    config("DJANGO_TWILIO_ACCOUNT_SID"), config("DJANGO_TWILIO_AUTH_TOKEN")
)


def generate_otp(send_sms_otp_for_v3):
    """genarate OTP function"""
    secure_otp_generator = secrets.SystemRandom()
    if send_sms_otp_for_v3:
        return secure_otp_generator.randrange(
            OTP_NUMBER_START_POINT_FOR_SMS, OTP_NUMBER_END_POINT_FOR_SMS
        )
    return secure_otp_generator.randrange(
        OTP_NUMBER_START_POINT, OTP_NUMBER_END_POINT
    )


def email_attachment_function(
    attachment_data, file_name_and_extension, file_type=None
):
    """email attachment common function"""
    encoded = base64.b64encode(attachment_data).decode()
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    if file_type:
        attachment.file_type = FileType(file_type)
    attachment.file_name = FileName(file_name_and_extension)
    attachment.disposition = Disposition("attachment")
    return attachment


def email_sender(
    template_id,
    to_emails,
    dynamic_data,
    attachment_data=None,
    attachment_name="",
):
    """send email function"""
    if template_id:
        from_email = BaseConfigurations.objects.get(
            base_configuration_key=SEND_EMAIL_VALUE
        ).base_configuration_value
        from_name = BaseConfigurations.objects.get(
            base_configuration_key=SEND_EMAIL_NAME_VALUE
        ).base_configuration_value
        # list of emails and preheader names, update with yours
        print("Sending email to : ",len(to_emails)," users")
        for i in range(0, len(to_emails), 500):
            batch_to_emails = to_emails[i:i + 500]
            
            message = Mail(from_email=(from_email, from_name), to_emails=batch_to_emails)
            # pass custom values for our HTML placeholders
            message.dynamic_template_data = dynamic_data
            message.template_id = template_id
            if attachment_data:
                if isinstance(attachment_data, dict):
                    lst_attachments = []
                    for key, val in attachment_data.items():
                        name_extension_separator = os.path.splitext(key)
                        lst_attachments.append(
                            email_attachment_function(
                                val,
                                f"{name_extension_separator[0]}.{name_extension_separator[1]}",
                            )
                        )
                    message.attachment = list(lst_attachments)
                else:
                    message.attachment = email_attachment_function(
                        attachment_data,
                        f"{attachment_name}.pdf",
                        "application/pdf",
                    )
            # create our sendgrid client object, pass it our key,
            #        then send and return our response objects
            try:
                send_grid_call = SendGridAPIClient(config("DJANGO_APP_EMAIL_KEY"))
                response = send_grid_call.send(message)
                _, _, _ = (
                    response.status_code,
                    response.body,
                    response.headers,
                )
                users_count = i+500
                print("Mail sent to ", users_count," users")
            except (NotImplementedError, ValueError, AttributeError) as error:
                print(f"Error: {error}", "Error email")
        return True
    return False


def send_email_function(email, email_type, user_first_name, key_or_password):
    """preparing dynamic data to send email function"""
    user_first_name = user_first_name.split(" ")[0]
    template_id = None
    dynamic_data = {}
    if email_type == FORGET_PASS_CONST:
        template_id = config("DJANGO_APP_FORGET_PASSWORD_TEMPLATE_ID")
        dynamic_data = {
            "user_name": user_first_name,
            "verification_code": key_or_password,
        }
    elif email_type == REGISTER:
        template_id = config("DJANGO_APP_REGISTER_TEMPLATE_ID")
        dynamic_data = {
            "user_name": user_first_name,
            "verification_code": key_or_password,
        }
    elif email_type == DELETE_ACCOUNT:
        template_id = config("DJANGO_APP_DELETE_ACCOUNT_TEMPLATE_ID")
        dynamic_data = {
            "user_name": user_first_name,
            "verification_code": key_or_password,
        }
    elif email_type == NEW_LOGGED_IN_USER:
        template_id = config("DJANGO_APP_NEW_LOGGED_IN_USER_TEMPLATE_ID")
        dynamic_data = {
            "user_name": user_first_name,
            "user_password": key_or_password,
            "user_email": email,
            "mfg_root_link": BaseConfigurations.objects.get(
                base_configuration_key=ROOT_URL
            ).base_configuration_value,
        }
    elif email_type == ADMIN_OTP:
        template_id = config("DJANGO_APP_ADMIN_OTP_TEMPLATE_ID")
        dynamic_data = {
            "user_name": user_first_name,
            "verification_code": key_or_password,
        }
    elif email_type == DELETED_ACCOUNT:
        template_id = config("DJANGO_APP_DELETED_ACCOUNT_TEMPLATE_ID")
        dynamic_data = {
            "user_name": user_first_name,
        }
    return email_sender(template_id, [(email, user_first_name)], dynamic_data)


def get_base_configuration_values_for_sms():
    """this function returns base configuration values for OTP sms"""
    from_number = redis_connection.get(SMS_FROM_STRING)
    if from_number:
        from_number = from_number.decode("utf-8")
    else:
        from_number = BaseConfigurations.objects.filter(
            base_configuration_key=SMS_FROM_STRING
        ).first()
        if from_number:
            from_number = from_number.base_configuration_value
        else:
            from_number = DEFAULT_FROM_SMS
        redis_connection.set(SMS_FROM_STRING, from_number)
    return (DEFAULT_OTP_MESSAGE, from_number)


def send_sms(phone, otp):
    """this function sends sms"""
    try:
        (otp_message, from_number) = get_base_configuration_values_for_sms()
        message = twilio_client.messages.create(
            body=otp_message.replace("{{otp}}", str(otp)),
            from_=from_number,
            to=phone,
        )
        return bool(message.sid)
    except TwilioException:
        return False


# Function to send OTP
def send_otp(email_or_phone, user_name, otp_type, send_email=True, send_sms_otp_for_v3=False):
    """
    This is an helper function to send otp to session stored phones or
    passed phone number as argument.
    """
    if not user_name:
        user_name = ""
    if email_or_phone:
        key = generate_otp(send_sms_otp_for_v3)
        if send_email:
            blocked_email_list = filter_function_for_base_configuration(
                BLOCKED_USERS_EMAILS_LIST, json.dumps([])
            )
            if (
                blocked_email_list and
                email_or_phone in list(json.loads(blocked_email_list))
            ):
                return False
            send_status = send_email_function(
                email_or_phone, otp_type, user_name, key
            )
        else:
            blocked_phone_list = filter_function_for_base_configuration(
                BLOCKED_USERS_PHONE_LIST, json.dumps([])
            )
            if (
                blocked_phone_list and
                email_or_phone in list(json.loads(blocked_phone_list))
            ):
                return False
            # logic to send mobile message
            send_status = send_sms(email_or_phone, key)
        if send_status:
            otp_key = str(key)
            return otp_key
    return False


def get_formated_driivz_start_and_stop_date(date, provide_local_time_dates=False,ocpi_format = False):
    """this function is created to format driivz dates from epoch to required date format"""
    if ocpi_format:
        updated_date = (
        datetime.strftime(date,DATE_TIME_FORMAT)
        )
        if provide_local_time_dates is False:
            return updated_date
    else:
        if isinstance(date, (int, float)):
            updated_date = datetime.fromtimestamp(date)
        else:
            updated_date = (
                datetime.strptime(date.split(".")[0],DATE_TIME_FORMAT)
                if isinstance(date, str) and not isinstance(date, datetime) else
                datetime.fromtimestamp(date)
            )
    if provide_local_time_dates is False:
        return updated_date
    if isinstance(updated_date,str):
        return timezone.localtime(datetime.strptime(updated_date,DATE_TIME_FORMAT).replace(tzinfo=pytz.UTC))
    return timezone.localtime(updated_date.replace(tzinfo=pytz.UTC))


def session_details(session):
    """this function will prepare session details to send mails"""
    charging_session_consumption = session.kwh
    charging_session_end_time_history = get_formated_driivz_start_and_stop_date(
        session.end_datetime,
        provide_local_time_dates=True,
        ocpi_format=True
    )
    charging_session_start_time_history = get_formated_driivz_start_and_stop_date(
        session.start_datetime,
        provide_local_time_dates=True,
        ocpi_format=True
    )
    return [
        charging_session_consumption,
        charging_session_end_time_history,
        charging_session_start_time_history,
    ]


def send_hold_session_email(
    charging_session, session_data_from_driivz, email_id, username
):
    """this function sends hold payment email"""
    if charging_session and session_data_from_driivz and email_id != "":
        (
            energy_supplied,
            end_date_time,
            start_date_time,
        ) = session_details(
            charging_session
        )
        charging_duration = time_formatter_for_hours(
            int((end_date_time - start_date_time).total_seconds())
        )
        payment_response = make_request(
            GET_REQUEST,
            f"/payments/{charging_session.payment_id}",
            charging_session.user_id.id,
            module="Send Hold Payment Email",
        )
        payment_data = json.loads(payment_response.content)
        pre_auth_expire = NOT_AVAILABLE
        if (
            payment_response.status_code == 200
            and "payment" in payment_data
            and "created_at" in payment_data["payment"]
        ):
            pre_auth_expire = timezone.localtime(
                datetime.strptime(
                    payment_data["payment"]["delayed_until"],
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                ).replace(tzinfo=pytz.UTC)
            )
        email_sender(
            config("DJANGO_APP_HOLD_PAYMENT_EMAIL_TEMPLATE_ID"),
            str(email_id).strip(),
            {
                "session_id": charging_session.emp_session_id,
                "user_name": username,
                "charger_name": f"{charging_session.station_id.site_title.strip()}, "
                + f"{charging_session.station_id.station_name.strip()}",
                "charger_point_name": charging_session.chargepoint_id.charger_point_name,
                "network": f"MFG {charging_session.back_office}",
                "start_date_time": start_date_time.strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
                "end_date_time": end_date_time.strftime("%d/%m/%Y %H:%M:%S"),
                "duration": charging_duration,
                "energy_supplied": f"{energy_supplied} kWh",
                "total_cost_with_tax": f"{format(float(charging_session.total_cost_incl),'.2f')}",
                "pre_auth_expire": pre_auth_expire.strftime("%d/%m/%Y %H:%M:%S"),
            },
        ) 


def send_exception_email_function(failed_api_url, error_message):
    """this function send the exception error email"""
    email_id_for_error_email = filter_function_for_base_configuration(
        EMAIL_ID_FOR_ERROR_EMAIL_ALERT, DEFAULT_EMAIL_ID_FOR_ERROR_EMAIL_ALERT
    )
    to_email = [(email_id_for_error_email, MFG_ADMIN)]
    email_sender(
        config("DJANGO_APP_EXCEPTION_EMAIL_ALERT_TEMPLATE_ID"),
        to_email,
        {
            "user_name": MFG_ADMIN,
            "failed_api_url": failed_api_url,
            "error_message": error_message,
        },
    )

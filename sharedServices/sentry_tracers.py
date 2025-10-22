"""common function for API calls"""
import json as JSON
import inspect
import requests
from sentry_sdk import configure_scope, capture_message
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from requests.exceptions import RequestException
from .constants import REQUEST_API_TIMEOUT

@shared_task(bind=True, max_retries=3, default_retry_delay=2)
def traced_request_with_retries(
    self,
    method,
    url,
    data=None,
    headers=None,
    timeout=REQUEST_API_TIMEOUT,
    json=None,
    auth=None
):
    """override request to log the sentry traces"""
    frame = inspect.currentframe()
    try:
        response = requests.request(
            method,
            url,
            data=data,
            headers=headers,
            timeout=timeout,
            json=json,
            auth=auth
        )
        line_number = frame.f_lineno
        file_name = frame.f_code.co_filename
        
        if  500 <= response.status_code < 599:
            raise self.retry(exc=Exception(f"Server error {response.status_code}"), countdown=2)
        
        if 400<= response.status_code < 499:
            with configure_scope() as scope:
                scope.set_extra("api_method", method)
                scope.set_extra("api_url", url)
                scope.set_extra("status_code", response.status_code)
                
                scope.set_extra("file_name", file_name)
                scope.set_extra("line_number", line_number)
                capture_message(
                    f"[Third party API call failed] URL - {url}, Status Code - {response.status_code}",
                    level="error"
                )

        return response
    except RequestException as exc:
        # Retry on request exceptions (network, timeout, etc.)
        with configure_scope() as scope:
            scope.set_extra("api_method", method)
            scope.set_extra("api_url", url)
            scope.set_extra("exception", str(exc))
            scope.set_extra("file_name", frame.f_code.co_filename)
            scope.set_extra("line_number", frame.f_lineno)
            capture_message(f"[API exception] {method} {url} - {exc}", level="error")
            try:
                raise self.retry(exc=exc, countdown=2)
            except MaxRetriesExceededError:
                return {
                    "success": False,
                    "error": str(exc),
                    "message": "Max retries exceeded",
                    "method": method,
                    "url": url,
                }
        # raise self.retry(exc=exc, countdown=2)
    except Exception as exc:
        # Retry for general exceptions (e.g., 5xx error)
        try:
            raise self.retry(exc=exc, countdown=2)
        except MaxRetriesExceededError:
            return {
                "success": False,
                "error": str(exc),
                "message": "Max retries exceeded",
                "method": method,
                "url": url,
            }   

def traced_request(
    method,
    url,
    data=None,
    headers=None,
    timeout=REQUEST_API_TIMEOUT,
    json=None,
    auth=None
):
    """override request to log the sentry traces"""
    frame = inspect.currentframe()
    response = requests.request(
        method,
        url,
        data=data,
        headers=headers,
        timeout=timeout,
        json=json,
        auth=auth
    )
    line_number = frame.f_lineno
    file_name = frame.f_code.co_filename
    if 400 <= response.status_code < 600:
        with configure_scope() as scope:
            scope.set_extra("api_method", method)
            scope.set_extra("api_url", url)
            scope.set_extra("status_code", response.status_code)
            try:
                scope.set_extra("response", JSON.dumps(
                JSON.loads(response.content)
                if isinstance(response.content, (str, bytes, bytearray)) else
                response.content
                ))
            except (JSON.JSONDecodeError, UnicodeDecodeError) as e:
                print("error convert")
                scope.set_extra("response", response.content if response.content else "Empty or invalid response")
            scope.set_extra("file_name", file_name)
            scope.set_extra("line_number", line_number)
            capture_message(
                f"[Third party API call failed] URL - {url}, Status Code - {response.status_code}",
                level="error"
            )
    return response

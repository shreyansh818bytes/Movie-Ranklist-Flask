from typing import Callable

import requests


def handle_api_exception(api_connection_func: Callable):
    def wrapper(*args, **kwargs):
        try:
            return api_connection_func(*args, **kwargs)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
            requests.exceptions.JSONDecodeError,
            requests.exceptions.TooManyRedirects,
        ):
            return None
        except requests.exceptions.RequestException as exception:
            raise exception

    return wrapper

import json

from flask import Response as FlaskResponse


class Response(FlaskResponse):
    def __init__(self, response, status=200, mimetype="application/json", **kwargs):
        response = json.dumps(response)
        return super().__init__(response, status=status, mimetype=mimetype, **kwargs)

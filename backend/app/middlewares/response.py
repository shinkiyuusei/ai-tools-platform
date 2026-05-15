def register_response_hooks(app):
    @app.after_request
    def append_json_charset(response):
        if response.content_type and "application/json" in response.content_type:
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

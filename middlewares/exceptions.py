class BadRequestError(Exception):
    def __init__(self, message="Really a bad Request"):
        self.message = message
        self.status_code = 400
        super().__init__(self.message)


class NotFoundError(Exception):
    def __init__(self, message="Ahh, Didn't Found Your Request"):
        self.message = message
        self.status_code = 404
        super().__init__(self.message)


class InternalServerError(Exception):
    def __init__(self, message="Internal Server Error"):
        self.message = message
        self.status_code = 500
        super().__init__(self.message)

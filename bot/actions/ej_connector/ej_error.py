class EJError(Exception):
    """Raised when a request from EJ doesn't supply the expected response"""

    ERROR_CODES = {
        400: (1001, "Bad Request: The server could not understand the request."),
        401: (1002, "Unauthorized: Access is denied due to invalid credentials."),
        403: (
            1003,
            "Forbidden: The server understood the request, but refuses to authorize it.",
        ),
        404: (1004, "Not Found: The requested resource could not be found."),
        500: (1005, "Internal Server Error: The server encountered an internal error."),
        502: (
            1006,
            "Bad Gateway: The server received an invalid response from the upstream server.",
        ),
        503: (
            1007,
            "Service Unavailable: The server is currently unable to handle the request.",
        ),
        504: (
            1008,
            "Gateway Timeout: The server did not receive a timely response from the upstream server.",
        ),
    }

    def __init__(self, code):
        """
        Initialize the exception with a specific error code.

        Args:
            code (int): The HTTP response code that triggered the exception.
        """
        self.code, self.message = self.ERROR_CODES.get(code, (9999, "Unknown Error"))
        super().__init__(self.message)

    def __str__(self):
        """
        Return a string representation of the error including the code and message.

        Returns:
            str: A string describing the error code and message.
        """
        return f"[Error {self.code}]: {self.message}"

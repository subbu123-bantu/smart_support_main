class EmailSendError(Exception):
    def __init__(self, status_code=None, message="Email sending failed"):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")
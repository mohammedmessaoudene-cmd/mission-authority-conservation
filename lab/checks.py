"""Research checks that remain active under Python optimization."""
class CheckFailed(RuntimeError):
    def __init__(self, message, result):
        self.result = result
        super().__init__(message)


def checked(condition, message, result):
    if not condition:
        raise CheckFailed(message, result)
    return result

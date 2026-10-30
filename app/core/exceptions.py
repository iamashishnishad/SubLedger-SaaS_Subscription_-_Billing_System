class DomainError(Exception):
    """Base class for errors raised by the service layer.

    Each subclass carries the HTTP status and a stable machine-readable code,
    so routes never have to translate errors themselves.
    """

    status_code = 400
    code = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class BusinessRuleError(DomainError):
    status_code = 400
    code = "business_rule_violation"


class LedgerImmutableError(RuntimeError):
    """Raised when code tries to update or delete a ledger entry."""

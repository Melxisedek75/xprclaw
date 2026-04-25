"""Custom exceptions for MiroFish adapter."""


class XPRClawMiroFishError(Exception):
    """Base exception for all adapter errors."""

    pass


class MiroFishConfigError(XPRClawMiroFishError):
    """Configuration error (missing env var, invalid value, etc)."""

    pass


class MiroFishAPIError(XPRClawMiroFishError):
    """API call failed (4xx, 5xx, or network error after retries)."""

    def __init__(self, message: str, status_code: int | None = None, retry_count: int = 0):
        super().__init__(message)
        self.status_code = status_code
        self.retry_count = retry_count


class MiroFishTimeoutError(XPRClawMiroFishError):
    """Operation exceeded timeout deadline."""

    pass


class SimulationFailedError(XPRClawMiroFishError):
    """Simulation execution failed (poll returned failed status)."""

    pass

class KPMApiError(Exception):
    """Base class of all KPM api exceptions"""


class KpmMissingConnectionError(KPMApiError):
    """Raised if a request is performed with an unconnected client"""


class KpmConnectError(KPMApiError):
    """Raised if no connection can be created."""


class KpmRequestError(KPMApiError):
    """Raised if a request did not succeed."""


class KpmResponseError(KPMApiError):
    """Raised if a response can not be read."""

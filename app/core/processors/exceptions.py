class ProcessorError(Exception):
    """Base class of all Processor Errors"""


class IssueClosedError(ProcessorError):
    """Raised if an issue is already closed or rejected"""


class APIServerConnectionError(ProcessorError):
    """Raised if an API Server connection fails"""


class SyncConditionNotMet(Exception):
    """Raised if a sync condition is not met"""

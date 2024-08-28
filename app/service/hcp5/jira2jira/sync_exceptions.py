class Hcp5JiraToJiraSyncException(Exception):
    """Base class of all HCP5 Jira-to-Jira Sync Exceptions"""


class JiraIssueTypeNotAcceptedForSync(Hcp5JiraToJiraSyncException):
    """Raised if a Jira Issue Type is not accepted to be Synced"""


class JiraCommentConversionError(Hcp5JiraToJiraSyncException):
    """Raised when the conversion of a Jira Comment failed."""

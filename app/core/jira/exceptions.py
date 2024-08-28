class JiraApiError(Exception):
    """Base class of all Jira api exceptions"""

    def format(self):
        return __name__, self.args


class JiraMissingConnectionError(JiraApiError):
    """Raised if a request is performed with an unconnected client"""


class JiraConnectError(JiraApiError):
    """Raised if no connection can be created."""


class JiraRequestError(JiraApiError):
    """Raised if a request did not succeed."""


class JiraIssueNotFound(JiraApiError):
    """Raised if a Jira query returned no issues."""


class MultipleJiraIssuesFound(JiraApiError):
    """Raised if a Jira query based on expected unique value
    returned multiple issues."""


class JQLorAppConfigQueryError(JiraApiError):
    """Raised if a Jira query based on expected unique value
    returned issue(s) but not with main JQL query."""

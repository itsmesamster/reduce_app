# standard
from dataclasses import dataclass, asdict

# 3rd party

# project
from app.core.jira.jira_map import JiraFieldsMapCore, ExtraFieldsMapCore


@dataclass(frozen=True)
class VwAudiHcp5JiraFieldMap(JiraFieldsMapCore):
    """Jira fields mapping from UI representation to Jira internal representation."""

    @dataclass(frozen=True)
    class VwAudiJiraExtraFieldsMap(ExtraFieldsMapCore):
        """Jira custom fields mapping from UI representation
        to Jira internal representation."""

        pass

    @property
    def extras(self) -> VwAudiJiraExtraFieldsMap:
        return self.VwAudiJiraExtraFieldsMap()

    def __repr__(self) -> str:
        dc = asdict(self)
        dc["extras"] = asdict(self.extras)
        return str(dc)

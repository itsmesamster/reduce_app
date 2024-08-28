from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ExtraFieldsMapCore:
    """Jira extra custom fields mapping from UI representation
    to Jira internal representation."""

    pass


@dataclass(frozen=True)
class JiraFieldsMapCore:
    """Jira fields mapping from UI representation to Jira internal representation."""

    ticket_id: str = "key"
    url: str = "self"

    project: str = "project"
    assignee: str = "assignee"
    labels: str = "labels"
    status: str = "status"
    components: str = "components"

    @property
    def extras(self) -> ExtraFieldsMapCore:
        pass

    def __repr__(self) -> str:
        dc = asdict(self)
        dc["extras"] = asdict(self.extras)
        return str(dc)

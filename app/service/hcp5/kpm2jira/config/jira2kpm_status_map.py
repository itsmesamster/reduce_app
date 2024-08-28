# standard
from dataclasses import dataclass

# 3rd party


# Fetching all AHCP5 tickets which are not closed, are customer issues,
# have the origin KPM and an external reference set


@dataclass(frozen=True)
class KpmStatus:
    comment: str
    status: int = ""
    supplier_response: str = ""

    def __repr__(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if v:
                d[k] = v
        return str(d)

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(frozen=True)
class JiraToKpmStatuses:
    # JIRA status -> KPM status
    # JIRA status -> [Date] =KPM status number + KPM comment
    OPEN: KpmStatus = KpmStatus("Ins System Übernommen", 0)  # no status change needed
    INFO_MISSING: KpmStatus = KpmStatus(
        "Rückfrage gestellt"
    )  # no status change needed + comment to KPM
    REOPENED: KpmStatus = KpmStatus(
        "Ticket wiedereröffnet", 0
    )  # KPM Status Übernommen (0)
    IN_ANALYSIS: KpmStatus = KpmStatus(
        "Mit der Analyse begonnen", 1
    )  # KPM status In Bearbeitung (1)
    IN_REVIEW: KpmStatus = KpmStatus(
        "Fix in Review", 1
    )  # KPM status In Bearbeitung (1)
    IN_PROGRESS: KpmStatus = KpmStatus(
        "Fix in Umsetzung", 1
    )  # KPM status In Bearbeitung (1)
    REJECTED: KpmStatus = KpmStatus(
        "Reject", 4
    )  # KPM status Verification (4) + comment to KPM (4+R)

    def get_status(self, jira_status: str) -> KpmStatus:
        jira_status = jira_status.upper().replace(" ", "_")
        if jira_status in self.__dict__:
            return getattr(self, jira_status)

    def get_status_comment(self, jira_status: str) -> str:
        status: KpmStatus = self.get_status(jira_status)
        if status:
            return status.comment
        return ""

    def get_status_number(self, jira_status: str) -> str:
        status: KpmStatus = self.get_status(jira_status)
        if status:
            return status.status
        return ""

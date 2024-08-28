# project core
from app.core.scheduler import scheduler

# project service
from app.service.hcp5.kpm2jira.sync import KPMJiraMainSync


# the service should be run from outside of the app dir:
# python -m app.service.hcp5.kpm2jira
# or
# python app/service/hcp5/kpm2jira


if __name__ == "__main__":
    scheduler(KPMJiraMainSync().sync)

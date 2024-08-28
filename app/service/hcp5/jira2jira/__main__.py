# project core
from app.core.scheduler import scheduler


# project service
from app.service.hcp5.jira2jira.sync import HCP5JiraJiraMainSync


# the service should be run from outside of the app dir:
# python -m app.service.hcp5.jira2jira
# or
# python app/service/hcp5/jira2jira


if __name__ == "__main__":
    scheduler(HCP5JiraJiraMainSync().sync)

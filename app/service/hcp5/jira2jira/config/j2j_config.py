""" config constants for AHCP5 JIRA to JIRA sync extension """

# standard
from dataclasses import dataclass
from os import getenv as env
from pathlib import Path

# project core
from app.core.utils import set_vault_secrets

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.config.j2j_config_dev_prod import (
    J2J_ESR_USE_JIRA_SERVER,
    J2J_VW_USE_JIRA_SERVER,
    ENV,
)


# print service name art
with open(f"{Path(__file__).parent}/service_name_art", "r") as f:
    print(f.read())


SERVICE_NAME = "ISSUE_SYNC_AHCP5_J2J"

VW_ESR_USER_EXT = ["(extern: esr labs)", "(extern: accenture)"]  # use ignore case


assignee_jql = "AND assignee = currentUser()"

logger.warning(f"USING VW/AUDI/CARIAD SERVER {J2J_VW_USE_JIRA_SERVER}")
logger.warning(f"USING ESR LABS SERVER {J2J_ESR_USE_JIRA_SERVER}")

POST_BACK_TO_VW_JIRA = True

if J2J_ESR_USE_JIRA_SERVER == ENV.DEV and J2J_VW_USE_JIRA_SERVER == ENV.PROD:
    POST_BACK_TO_VW_JIRA = False
    logger.warning(
        f"ESR JIRA ({J2J_ESR_USE_JIRA_SERVER}) and "
        f"VW JIRA ({J2J_VW_USE_JIRA_SERVER}) servers are different."
    )

logger.info(
    f"POST BACK TO VW JIRA is set to {POST_BACK_TO_VW_JIRA} "
    f"for {J2J_VW_USE_JIRA_SERVER} server."
)

# VAULT SECRETS
secrets_keys = []

if J2J_ESR_USE_JIRA_SERVER == ENV.PROD:
    secrets_keys.extend(
        [
            "J2J_ESR_PROD_JIRA_EMAIL",
            "J2J_ESR_PROD_JIRA_TOKEN",
            "J2J_ESR_PROD_JIRA_USER_ID",
        ]
    )

if J2J_ESR_USE_JIRA_SERVER == ENV.DEV:
    secrets_keys.extend(
        [
            "J2J_ESR_DEV_JIRA_EMAIL",
            "J2J_ESR_DEV_JIRA_TOKEN",
            "J2J_ESR_DEV_JIRA_USER_ID",
        ]
    )

if J2J_VW_USE_JIRA_SERVER == ENV.PROD:
    secrets_keys.extend(
        [
            "J2J_VW_PROD_JIRA_USER",
            "J2J_VW_PROD_JIRA_TOKEN",
        ]
    )

if J2J_VW_USE_JIRA_SERVER == ENV.DEV:
    secrets_keys.extend(
        [
            "J2J_VW_DEV_JIRA_USER",
            "J2J_VW_DEV_JIRA_TOKEN",
        ]
    )

VAULT_SECRETS_TO_SET = secrets_keys


VAULT_URL = env("VAULT_URL")
if not VAULT_URL:
    VAULT_URL = "https://vault.int.esrlabs.com"
    logger.error(f"Could not find VAULT_URL env var. Using default URL: {VAULT_URL}")

# set VAULT_TOKEN in your dev env
# or add it to the Docker container @ docker run
VAULT_TOKEN = env("VAULT_TOKEN")
if not VAULT_TOKEN:
    logger.error("Could not find VAULT_TOKEN env var.")

SECRETS_URL = f"{VAULT_URL}/v1/tooling-team/data/issue-sync-hcp5-vwjira-to-esrjira"

if not all([env(secret) for secret in VAULT_SECRETS_TO_SET]):
    logger.debug(
        "Missing secrets: "
        f"{[secret for secret in VAULT_SECRETS_TO_SET if not env(secret)]}"
    )
    set_vault_secrets(SECRETS_URL, VAULT_TOKEN, VAULT_SECRETS_TO_SET)

for secret in VAULT_SECRETS_TO_SET:
    if not env(secret):
        logger.error(f"Missing {secret} environment variable.")

if not all([env(secret) for secret in VAULT_SECRETS_TO_SET]):
    logger.error("Service cannot run with missing secrets. Exiting ...")
    exit()


@dataclass
class J2jAhcp5EsrJira:
    """Jira config for >>Jira-to-Jira<< AHCP5 ESR LABS JIRA server."""

    use_jira_server: ENV = J2J_ESR_USE_JIRA_SERVER

    ISSUE_PREFIX = "AHCP5"
    PROJECT_KEY = "AHCP5"
    PROJECT_NAME = "Audi HCP5"
    ORIGIN = "Audi Jira"
    LABELS = "Technical_Clearing"
    RESOLUTION = "Unresolved"
    REPORTERS = ""
    ISSUE_TYPE = ""
    PARENT_EPIC = "AHCP5-2651"  # default Parent Epic for Jira "Task"
    VERONIKA_ID = "557058:da3e424e-aa5c-4e3f-be06-55150e8d66a4"  # Veronika Kleine
    DEFAULT_COMPONENT = "Unknown"

    __ESR_JIRA_PROD_SERVER = "https://esrlabs.atlassian.net/"
    __ESR_JIRA_PROD_EMAIL = env("J2J_ESR_PROD_JIRA_EMAIL")
    __ESR_JIRA_PROD_TOKEN = env("J2J_ESR_PROD_JIRA_TOKEN")
    __ESR_JIRA_PROD_USER_ID = env("J2J_ESR_PROD_JIRA_USER_ID")
    __ESR_JIRA_PROD_SYNC_REPORTS_ID = "AHCP5-36586"
    __ESR_JIRA_PROD_ASSIGNEE = VERONIKA_ID

    __ESR_JIRA_DEV_SERVER = "https://esrlabs-sandbox-800.atlassian.net/"
    __ESR_JIRA_DEV_EMAIL = env("J2J_ESR_DEV_JIRA_EMAIL")
    __ESR_JIRA_DEV_TOKEN = env("J2J_ESR_DEV_JIRA_TOKEN")
    __ESR_JIRA_DEV_USER_ID = env("J2J_ESR_DEV_JIRA_USER_ID")
    __ESR_JIRA_DEV_SYNC_REPORTS_ID = "AHCP5-36302"

    def __post_init__(self):
        logger.warning(f"USING ESR LABS SERVER {self.use_jira_server.value}")
        if self.use_jira_server == ENV.PROD:
            self.server = self.__ESR_JIRA_PROD_SERVER
            self.email = self.__ESR_JIRA_PROD_EMAIL
            self.token = self.__ESR_JIRA_PROD_TOKEN
            self.user_id = self.__ESR_JIRA_PROD_USER_ID
            self.sync_reports_jira_id = self.__ESR_JIRA_PROD_SYNC_REPORTS_ID
            self.assignee = self.__ESR_JIRA_PROD_ASSIGNEE

            self.default_audi_cluster = "-"

        elif self.use_jira_server == ENV.DEV:
            self.server = self.__ESR_JIRA_DEV_SERVER
            self.email = self.__ESR_JIRA_DEV_EMAIL
            self.token = self.__ESR_JIRA_DEV_TOKEN
            self.user_id = self.__ESR_JIRA_DEV_USER_ID
            self.sync_reports_jira_id = self.__ESR_JIRA_DEV_SYNC_REPORTS_ID
            self.assignee = self.user_id

            self.default_audi_cluster = "Cluster 4.3"

        self.base_jql_esr = (
            f"PROJECT = {self.PROJECT_KEY} "
            f"AND RESOLUTION = {self.RESOLUTION} "
            f"AND LABELS = {self.LABELS}"
        )


J2J_ESR_JIRA = J2jAhcp5EsrJira()


@dataclass
class J2jVwAhcp5CariadJira:
    """Jira config for >>Jira-to-Jira<< AHCP5 VW/Audi Cariad JIRA server."""

    use_jira_server = J2J_VW_USE_JIRA_SERVER

    ISSUE_PREFIX = "HCP5"
    PROJECT_KEY = "HCP5"
    PROJECT_NAME = "Audi HCP5"
    STATUS_CATEGORY = '("To Do", "In Progress")'
    LABELS = ["Technical_Clearing", "ESR"]
    REPORTERS = ""
    ESR_ASSIGNEES = "(ufs1vcn, wvk8ck1)"  # Veronika and Sabina
    COMMENTS_SYNC_IGNORED_USERS = ["ufs1vcn", "wvk8ck1"]

    __VW_JIRA_PROD_SERVER = "https://devstack.vwgroup.com/jira/"
    __VW_JIRA_PROD_USER = env("J2J_VW_PROD_JIRA_USER")
    __VW_JIRA_PROD_TOKEN = env("J2J_VW_PROD_JIRA_TOKEN")

    # !!!! TODO: FIXME: add dev server !!!!
    __VW_JIRA_DEV_SERVER = ""  # no VW Jira DEV server yet
    __VW_JIRA_DEV_USER = env("J2J_VW_DEV_JIRA_USER")
    __VW_JIRA_DEV_TOKEN = env("J2J_VW_DEV_JIRA_TOKEN")

    def __post_init__(self):
        logger.warning(f"USING VW/AUDI/CARIAD SERVER {self.use_jira_server.value}")
        if self.use_jira_server == ENV.PROD:
            self.server = self.__VW_JIRA_PROD_SERVER
            self.user = self.__VW_JIRA_PROD_USER
            self.token = self.__VW_JIRA_PROD_TOKEN

        elif self.use_jira_server == ENV.DEV:
            self.server = self.__VW_JIRA_DEV_SERVER
            self.user = self.__VW_JIRA_DEV_USER
            self.token = self.__VW_JIRA_DEV_TOKEN

        # !!! TODO: FIXME: remove prod/dev hack after getting VW PROD TOKEN !!!!
        # !!! HACK: using dev user + token for prod server !!!
        if self.use_jira_server == ENV.PROD and not self.token:
            self.user = self.__VW_JIRA_DEV_USER
            self.token = self.__VW_JIRA_DEV_TOKEN

        self.base_jql_vwaudi = (
            f"PROJECT = {self.PROJECT_KEY} "
            f"AND LABELS = {self.LABELS[0]} "
            f"AND LABELS = {self.LABELS[1]} "
            f"AND statusCategory in {self.STATUS_CATEGORY}"
        )


J2J_VWAUDI_JIRA = J2jVwAhcp5CariadJira()


INTEGRATION_LABELS = [
    "AR_Integration",
    "SSW_Integration",
    "Iot_Integration",
    "E3_Integration",
    "MOD_Integration",
]


#### VW JQL used for sync ---> ####

VW_JQL = {}

VW_JQL["TASK"] = (
    "project = HCP5 "
    "AND labels = Technical_Clearing "
    "AND statusCategory not in (Done) "
    f"AND assignee in {J2J_VWAUDI_JIRA.ESR_ASSIGNEES} "
)
VW_JQL["INTEGRATION"] = (
    "project = HCP5 "
    "AND issuetype = Integration "
    "AND labels in "
    "(AR_Integration, SSW_Integration, Iot_Integration, "
    "E3_Integration, MOD_Integration) "
    'AND status = "Umsetzung angefragt" '
    f"AND assignee in {J2J_VWAUDI_JIRA.ESR_ASSIGNEES} "
    'AND status changed to ("Umsetzung angefragt") after startOfYear()'
)

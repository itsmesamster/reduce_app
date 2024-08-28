""" config constants for AHCP5 KPM to JIRA sync extension """

# KPM test inbox ticket: 9906671 (created on Apr 11th 2024)

# standard
from os import getenv as env
from enum import Enum
from pathlib import Path

# project core
from app.core.custom_logger import logger
from app.core.utils import save_vault_secret_as_file, check_get_set_secrets


# print service name art
with open(f"{Path(__file__).parent}/service_name_art", "r") as f:
    print(f.read())


class ENV(Enum):
    DEV = "development"
    PROD = "production"


SERVICE_NAME = "ISSUE_SYNC_HCP5_KPM2JIRA"
SERVICE_PATH = "app/service/hcp5/kpm2jira"

## !!!! ATTENTION !!!! - THE KPM DEV ENV IS NOT ISOLATED FROM PROD !!!!
#############################################################
### !!!! ATTENTION !!!! - these are the main ENV VARS   #####
###          for selecting the KPM and JIRA servers     #####
USE_KPM_SERVER = ENV.PROD
USE_JIRA_SERVER = ENV.DEV
###                                                     #####
#############################################################

logger.warning(f"KPM SERVER:  \t\t {USE_KPM_SERVER.value}")
logger.warning(f"JIRA SERVER: \t\t {USE_JIRA_SERVER.value}")

CLUSTER_MAP = f"{SERVICE_PATH}/config/jira_cluster_map.yaml"

POST_BACK_TO_KPM = True
if USE_KPM_SERVER != USE_JIRA_SERVER:
    logger.warning(
        f"KPM ({USE_KPM_SERVER}) and JIRA ({USE_JIRA_SERVER}) servers are different. "
        "POST BACK TO KPM will be set to False."
    )
    POST_BACK_TO_KPM = False
else:
    logger.info(f"POST BACK TO KPM is set to TRUE for {USE_KPM_SERVER} server.")

# VAULT SECRETS
SECRETS_TO_SET = [
    "KPM_USER_ID",
    "JIRA_EMAIL",
    "JIRA_TOKEN",
    "JIRA_ACCOUNT_ID",
]

if not env("KPM_CERT_FILE_PATH"):
    SECRETS_TO_SET.append("KPM_CERT")

VAULT_URL = env("VAULT_URL")
if not VAULT_URL:
    VAULT_URL = "https://vault.int.esrlabs.com"
    logger.error(f"Could not find VAULT_URL env var. Using default URL: {VAULT_URL}")

SECRETS_URL = f"{VAULT_URL}/v1/tooling-team/data/issue-sync-hcp5-vwkpm-to-esrjira"

# set VAULT_TOKEN in your dev env
# or add it to the Docker container @ docker run
VAULT_TOKEN = env("VAULT_TOKEN")
if not VAULT_TOKEN:
    logger.error("Could not find VAULT_TOKEN env var.")

check_get_set_secrets(
    vault_secrets_url=SECRETS_URL,
    vault_token=VAULT_TOKEN,
    secrets_to_set=SECRETS_TO_SET,
)

if env("KPM_CERT") and not env("KPM_CERT_FILE_PATH"):
    logger.info("Saving KPM cert as file ...")
    save_vault_secret_as_file("KPM_CERT", env("KPM_CERT"))
    KPM_CERT_FILE_PATH = env("KPM_CERT_FILE_PATH")


# KPM   @ CARIAD Audi / VW Group
KPM_SERVER = "https://ws-gateway-cert.volkswagenag.com/services"
KPM_USER_ID = env("KPM_USER_ID")
KPM_CERT_FILE_PATH = env("KPM_CERT_FILE_PATH")
KPM_CERT = env("KPM_CERT")  # not to be used directly
__KPM_PROD_INBOX = "FF/HCP5BS-ESR/"
__KPM_DEV_INBOX = "Z$/KPMEE-02/"

KPM_INBOX = __KPM_DEV_INBOX

if USE_KPM_SERVER == ENV.PROD:
    KPM_INBOX = __KPM_PROD_INBOX
elif USE_KPM_SERVER == ENV.DEV:
    KPM_INBOX = __KPM_DEV_INBOX

PLANT_VAL, ORG_UNIT_VAL = KPM_INBOX.rstrip("/").split("/")


# JIRA  @ ESR Labs      (Audi HCP5)

__JIRA_PROD_SERVER = "https://esrlabs.atlassian.net/"
__JIRA_DEV_SERVER = "https://esrlabs-sandbox-800.atlassian.net/"

JIRA_EMAIL = env("JIRA_EMAIL")  # Jira Ticket Reporter (Problem Resolution Mananger)
JIRA_TOKEN = env("JIRA_TOKEN")
VAULT_JIRA_ACCOUNT_ID = env("JIRA_ACCOUNT_ID")

# https://esrlabs.atlassian.net/jira/people/<JIRA_ACCOUNT_ID> -> find the jira accountid
ADRIAN_JIRA_ID = "63f87279c1f7acaf636ce8a9"  # DEV
GUIDO_JIRA_ID = "620b84191d088700694dada7"  # PROD
VERONIKA_JIRA_ID = "557058:da3e424e-aa5c-4e3f-be06-55150e8d66a4"  # PROD

PROD_USERS = ["guido.reinders", "veronika.kleine"]

JIRA_SERVER_URL = __JIRA_DEV_SERVER

if USE_JIRA_SERVER == ENV.PROD:
    JIRA_SERVER_URL = __JIRA_PROD_SERVER
    JIRA_ACCOUNT_ID = GUIDO_JIRA_ID  # Default Jira Ticket Assignee
    JIRA_ID_FOR_SYNC_REPORTS = "AHCP5-36311"
    if not any(prod_user in JIRA_EMAIL for prod_user in PROD_USERS + ["mocked_"]):
        logger.error(
            f"Don't use a DEV email address login [{JIRA_EMAIL}] for PROD JIRA. "
            "You will appear as a reporter when creating Jira tickets."
        )
        exit()
elif USE_JIRA_SERVER == ENV.DEV:
    JIRA_SERVER_URL = __JIRA_DEV_SERVER
    JIRA_ACCOUNT_ID = ADRIAN_JIRA_ID
    JIRA_ID_FOR_SYNC_REPORTS = "AHCP5-36301"

if JIRA_ACCOUNT_ID != VAULT_JIRA_ACCOUNT_ID:
    logger.warning(
        f"JIRA_ACCOUNT_ID from Vault [{VAULT_JIRA_ACCOUNT_ID}] "
        f"is different from the one in config [{JIRA_ACCOUNT_ID}]. "
        "Please check."
    )

JIRA_PROJECT = "Audi HCP5"
JIRA_ISSUE_PREFIX = "AHCP5"
JIRA_PROJECT_KEY = JIRA_ISSUE_PREFIX
JIRA_ISSUE_TYPE = '(Bug, "Customer Issue")'

JIRA_REPORTERS = (
    '("Guido Reinders", "Fabienne Anderwald", "Veronika Kleine", '
    '"Ibrahim Mohamed Elsayed Ezzat", "Carlos A. Delgado", "Adrian Boca")'
)
JIRA_ASSIGNEES = JIRA_REPORTERS

# "Adrian Boca" shouldn't be reporter or assignee for PROD ESR Labs JIRA,
# and should be removed from the JQL queries in the future (summer 2024)
# but for now there are 23 tickets where he is the reporter. Check with:
"""
PROJECT = "Audi HCP5" AND issuetype in (Bug, "Customer Issue") AND 
reporter in ("Adrian Boca") AND "Origin" in ("Audi KPM", "ESR Jira")
"""

JIRA_ORIGIN = 'Audi KPM", "ESR Jira'

# KPM -> JIRA conditions to pass for being sync
DP = "DevelopmentProblem"

# 1. not KPM["Supplier"]["Contractor"]["PersonalContractor"]["UserId"]
#                       in "D962178", "D16902F" -> Ignore, not assigned to ESR
K2J_KPM_SUPPLIER_CONTRACTOR_PATH = f"{DP}/Supplier/Contractor/PersonalContractor/UserId"
GUIDO = "D16902F"
FABIENNE = "D962178"
VERONIKA = "D688873"
K2J_KPM_SUPPLIER_CONTRACTOR_IDS = [GUIDO, FABIENNE, VERONIKA]

# 2. if KPM["ProblemStatus"] in ("5", "6") -> Ignore, ticket already closed
K2J_KPM_STATUS_PATH = f"{DP}/ProblemStatus"
K2J_KPM_CLOSED_STATUS_IDS = ("5", "6")

# 3. Check if "[Function / Component]" KPM["ShortText"] in ("5", "6")
#           -> Ignore, test ticket.
K2J_KPM_SHORT_TEXT_PATH = f"{DP}/ShortText"
K2J_KPM_SHORT_TEXT_VAL = ("5", "6")

# 3. Check unless KPM["SupplierStatus"] exists -> Ignore, must be set (Log error)
K2J_KPM_SUPPLIER_STATUS_PATH = f"{DP}/SupplierStatus"

INBOX_CHECKS = [
    f"{DP}/Supplier/Contractor/Address",
    # f'{DP}/Creator/Address',
    # f'{DP}/Coordinator/Contractor/Address',
    # f'{DP}/ProblemSolver/Contractor/Address',
    # f'{DP}/SpecialistCoordinator/Contractor/Address',
]

ORG_UNIT_KEY = "OrganisationalUnit"
PLANT_KEY = "Plant"

STATUSES_THAT_NEED_QUESTION_TO_OEM = ("Rejected", "Info Missing")

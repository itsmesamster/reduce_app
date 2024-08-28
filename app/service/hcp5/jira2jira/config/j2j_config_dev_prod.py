from enum import Enum


class ENV(Enum):
    DEV = "development"
    PROD = "production"


#############################################################
### !!!! ATTENTION !!!! - these are the main ENV VARS   #####
###          for selecting the VW and ESR JIRA servers  #####
J2J_VW_USE_JIRA_SERVER = ENV.PROD
J2J_ESR_USE_JIRA_SERVER = ENV.DEV
###                                                     #####
#############################################################

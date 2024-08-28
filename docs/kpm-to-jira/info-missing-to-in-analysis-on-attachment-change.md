# Transition Jira ticket status from Info Missing to In Analysis

## Overview
```plantuml
@startuml
actor User
collections KPM
control "KPM Sync" as App
collections Jira
User -> KPM: Add new attachment
App -> App: Detect Updated attachment
App -> Jira: Sync attachment
App -> App: Check ticket status
alt Ticket status is INFO MISSING
    App -> Jira: Transition status from INFO MISSING to IN ANALYSIS
end
@enduml
```

## Description
If a new attachment is added to the KPM system, this ticket shall be synced to the Jira system. In addition to that the status of the Jira ticket shall be updated in case the status was on INFO MISSING.

## Questions

* What should happen if the ticket is in any other state?


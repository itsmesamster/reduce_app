# Transition Jira ticket status from rejected to closed
## Overview
```plantuml
@startuml
actor User
collections Jira
control "KPM Sync" as App
collections KPM
User -> Jira: Transition status from "REJECTED" to "CLOSED"
Jira -> Jira: Set status "CLOSED"
App -> App: Detect Updated Status
alt KPM ticket accessible
    App -> App: Was not described?
else KPM ticket not accessible
    App -> Jira: Add comment "No access in KPM -> closed"
end
@enduml
```

## Description
If an previously rejected ticket is closed on the Jira system, a comment on the Jira ticket should be added in case there is no access to the corresponding KPM ticket.

## Questions

* What should happen if there is access?
* If the state should be updated to KPM, to which value?
* Is there any case possible where a Jira ticket exists without KPM ticket (Since they are synced)?



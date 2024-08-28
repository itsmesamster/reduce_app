# Create new Jira ticket from new KPM ticket

## Overview

```plantuml
@startuml
actor User
collections KPM
control "KPM Sync" as App
collections Jira
User -> KPM: Create new ticket in KPM
App -> KPM: Poll State (KPM ID)
App-> Jira: Poll State (External Reference ID)
App -> App: Detect missing Jira tickets by KPM ID
App -> Jira: Create new Jira ticket
App-> Jira: Copy Fields
Jira -> App: Return Jira ticket ID
App -> KPM: Update KPM field "FEHLERNUMMER" with new Jira ticket ID
App -> KPM: Update KPM field "STATUS" to "uebernommen"
App -> KPM: Update KPM field "KOMMENTAR" with "$date - Ticket wurde in ESR Jira System uebernommen"
@enduml
```

## Description
If a new ticket is created inside the KPM system, this ticket shall be created on the Jira system as well.
The below [specified](###fields-to-sync-from-kpm-to-jira) fields have to be synced as well. After a successful synchronization of the KPM
ticket into the Jira Ticket the KPM ticket shall be updated to indicated a successful transfer.

## Technical Details

### Fields to sync from kpm to jira
* Feedback from OEM

### Fields to update on KPM
* "FEHLERNUMMER" -> Jira ID of previously created ticket
* "STATUS" -> "uebernommen" (Is this the correct field in KPM?)
* "KOMMENTAR" -> "$date - Ticket wurde in ESR Jira System uebernommen" (Is this the correct field in KPM? - comment or "Feedback to OEM"/)

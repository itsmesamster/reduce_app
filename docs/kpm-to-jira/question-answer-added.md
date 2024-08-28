# Synchronize Supplier Response field

```plantuml
@startuml
actor User
collections KPM
control "KPM Sync" as App
collections Jira
User -> KPM: Add answer to question in the "Rueckfrage" process
App -> App: Detect new answer to question
note left
How can this be identified?
end note
App -> Jira: Add the answer to field "Answer from OEM"
alt Status is INFO MISSING
App -> Jira: Transition the status from INFO MISSING to IN ANALYSIS
else Status is not INFO MISSING
App -> App: Not defined
end case
@enduml
```

## Description
If a new answer is entered on the KPM system to an existing "Rueckfrage" process, this answer shall be added to the Jira ticket. Additionally the status of the Jira ticket should automatically be changed from INFO MISSING to IN ANALYSIS.

## Questions

* How should the field names in Jira be exactly name? (Does not matter for the app, but for completeness and to avoid further confusion)
* How does the "Rueckfrage" process look like on KPM. How are the fields named, what exactly has to be done in which order. Please provide a manual demonstration.
* How to handle additional questions.

## Additional TODO

* Once the field name is clarified, this field needs to be added to Jira. (Can not be done by tooling team)
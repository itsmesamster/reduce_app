# Synchronize Supplier Response field

```plantuml
@startuml
actor User
collections Jira
control "KPM Sync" as App
collections KPM
User -> Jira: Add question to field "Question to OEM"
note left
Is there a way to detect a new question?
Both ends are only pull based.
How do we identify if a question
was modified or if a new one was added?
end note
User -> Jira: Transition status to INFO MISSING
App -> App: Detect new question
App -> KPM: Create a new "Rueckfrage" (special feature or same as "Feedback from/to OEM?)
App -> KPM: Add the question to the "Rueckfrage" (Details required)
App -> KPM: Update KPM field "supplierresponse" with "DD.MM.YYYY: Rückfrage gestellt"
@enduml
```

## Description
If a new question to the OEM is entered in the Jira ticket, the process of a "Rueckfrage" shall be opened on the KPM side. The "Rueckfrage" shall contain the body of the "Question to OEM" field.

## Questions

* How should the field names in Jira be exactly named? (Does not matter for the app, but for completeness and to avoid further confusion)
* How does the "Rueckfrage" process look like on KPM. How are the fields named, what exactly has to be done in which order. Please provide a manual demonstration.
* How to handle additional questions.

## Additional TODO

* Once the field name is clarified, this field needs to be added to Jira. (Can not be done by tooling team)
### Creation of a ticket in Jira

> Fields with **?** are currently TBD

Customer Issue:

| Jira UI field                                 | Jira API field name | Type      | KPM UI field                | KPM API field name                                                        | Required by Jira | Jira default input if KPM field not abialable in Jira | Note                                                 |
| --------------------------------------------- | ------------------- | --------- | --------------------------- | ------------------------------------------------------------------------- | ---------------- | ----------------------------------------------------- | ---------------------------------------------------- |
| Project                                       | project             | project   | -                           | -                                                                         | yes              | Audi HCP5 (AHCP5)                                     | -                                                    |
| Issue Type                                    | issuetype           | issuetype | -                           | -                                                                         | yes              | Customer Issue                                        | -                                                    |
| Summary                                       | summary             | string    | KurzText                    | ShortText                                                                 | yes              | -                                                     | -                                                    |
| Description                                   | description         | string    | Beanstandung                | Description                                                               | yes              | -                                                     | Beanstandung + Analyse field (Analyse not yet found) |
| Priority                                      | priority            | priority  | Bewertung                   | Rating                                                                    | yes              | -                                                     | See below: KPM Rating                                |
| Specification                                 | customfield_12732   | string    | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Testcase ID                                   | customfield_12693   | string    | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Labels                                        | labels              | array     | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Assignee                                      | assignee            | user      | -                           | -                                                                         | yes              | Automatic                                             | -                                                    |
| External Reference                            | customfield_10503   | string    | Problemdaten                | ProblemNumber                                                             | yes              | -                                                     | -                                                    |
| Components                                    | components          | array     | Funktion                    | Function                                                                  | yes              | Unknown                                               | -                                                    |
| Audi Domain                                   | customfield_12613   | array     | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Audi Cluster                                  | customfield_12600   | array     | -                           | -                                                                         | yes              | Cluster 4.1                                           | -                                                    |
| Affects versions                              | versions            | array     | SW                          | Software                                                                  | yes              | 000                                                   | -                                                    |
| Due date                                      | duedate             | date      | -                           | -                                                                         | no               | -                                                     | Automatic from Jira (Script from HCP5)               |
| Hardware                                      | customfield_10500   | string    | HW                          | Hardware                                                                  | yes              | -                                                     | -                                                    |
| Reproducibility                               | customfield_10501   | option    | Reproduzierbar / Häufigkeit | -                                                                         | yes              | -                                                     | See below: Reproducibility                           |
| Problem Finder                                | customfield_10900   | string    | Beanstander                 | Exclaimer                                                                 | yes              | -                                                     | -                                                    |
| Origin                                        | customfield_12640   | option    | -                           | -                                                                         | yes              | AudiKPM                                               | -                                                    |
| Affected workproducts                         | customfield_12708   | array     | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Cause of bug                                  | customfield_10901   | option    | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Cause of Reject                               | customfield_12713   | option    | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Fix versions                                  | fixVersions         | array     | -                           | -                                                                         | no               | 000                                                   | -                                                    |
| Sprint                                        | customfield_10007   | array     | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Epic Link                                     | customfield_10008   | any       | -                           | -                                                                         | no               | -                                                     | -                                                    |
| Attachment (Files)                            | attachment          | array     | Extras --> Dokumente        | -                                                                         | no               | -                                                     | See below: Attachments                               |
| Audi VR                                       | customfield_12740   | option    | Verbundrelease              | Major / Minor / Extend                                                    | yes              | VR 000                                                | See below: KPM VerbundRelease / Jira Audi VR         |
| Feedback from OEM (Current name: Synch Input) | customfield_12742   | string    | Analyse                     | -                                                                         | no               | -                                                     | See below: Analyse                                   |
| Feedback to OEM (Current name: Synch Output)  | customfield_12743   | string    | Analyse                     | -                                                                         | no               | -                                                     | Needed for Jira to KPM sync (not for first stage)    |
| Part Number                                   | customfield_12748   | string    | Teilenummer                 | PreNumber / MiddleGroup / EndNumber / Index / Charge / ChargeSerialNumber | yes              | -                                                     | See below: KPM Teilenummer                           |

### SoapUI Methods

Reference for mentioned names.

- GetProcessStepList
- GetProcessStep
- GetDocumentList
- GetDocument

### Reproducibility

| KPM API                          |  Jira UI / API    |
| -------------------------------- | ----------------- |
| Repeatable: XI                   | 01 - Single Event |
| Repeatable: XH AND Frequency: XE | 02 - Sporadic     |
| Repeatable: XH AND Frequency: XF | 03 - Frequent     |
| Repeatable: XH AND Frequency: XG | 04 - Reproducible |

### Analyse

API: Access via GetProcessStepList / GetProcessStep to get the text field and user info

```
Get comments from KPM:

GetProcessStepList:
Input = ProblemNumber
Response = ProcessStepItem

--> Search for <ProcessStepTypeDescripton>Analyse abgeschlossen</ProcessStepTypeDescripton>
--> Found: Get the ProcessStepID

GetProcessStep:
Input = ProblemNumber, ProcessStepId
Response = ProcessStep

--> Search for <Text>…</Text> AND <LastChanger> --> (get all user info) AND <LastChangeDate>
```

### Attachments

API: Access the list directly with GetDocumentList and a single Document with GetDocument

### KPM Teilenummer mapping to Jira

Find more info in kpm_customer_issue_field_overview.md

```
# INFO: The number parts are joined to one long number and not added (+)
Jira Teilenummer = PreNumber + MiddleGroup + EndNumber + Index + Charge + ChargeSerialNumber
```

### KPM VerbundRelease / Jira Audi VR

Find more info in kpm_customer_issue_field_overview.md

```
General info: The number parts are joined to one long number and not added (+)
Audi VR = Major + Minor + Extend

State 09.05.22:
For Jira adaptation this value needs to be shortend.

The follwing vaules need only the equal number in the first part (Major). Minor and Extend number are not needed to be compared.
- VR14
- VR15
- VR16
- VR17
- VR21
- VR22
- VR23
- VR24

For those two numbers the second part (Minor) have to be the same as shown. The Extend number is not needed to be compared.
- VR18.1 --> 18.1.X
- VR18.2 --> 18.2.X
```

### KPM Rating mapping to Jira

| KPM Option                                             | Jira Option |
| ------------------------------------------------------ | ----------- |
| A1 - Sicherheitsrisiko,Liegenbl.,unverkäufl.FZG(1)     | Blocker     |
| A - nicht annehmbar, führt zu Kundenbeanstandung.(2,3) | Critical    |
| B - unangenehm, störend, Reklamation zu erwarten(4,5)  | Major       |
| C - bei Häufung sind Beanstandungen zu erwarten(6,7)   | Minor       |
| D - nur Information (8,9,10)                           | Trivial     |
| DB - Beschluss                                         | Trivial     |
| DV - Vorstellpunkt                                     | Trivial     |

### Creation of a ticket in KPM

> TBD

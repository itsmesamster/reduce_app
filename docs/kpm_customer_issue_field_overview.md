# KPM Customer Issue field overview

> File is not final

This applies for the issue type: Customer Issue

### DevelopmentProblem

| KPM UI field                 | API (Dict) field name    | Required by KPM | Default input |
| ---------------------------- | ------------------------ | --------------- | ------------- |
| Problemdaten                 | ProblemNumber            |                 |               |
| not found                    | LastChangeTimestamp      |                 |               |
| not found                    | Workflow                 |                 |               |
| Ref-Nr. Ext.                 | ExternalProblemNumber    |                 |               |
| Beanstander                  | Exclaimer                |                 |               |
| Historie / Erfassung         | ProblemDate              |                 |               |
| P-Status                     | ProblemStatus            |                 |               |
| Bewertung                    | Rating                   |                 |               |
| Beanstandung                 | Description              |                 |               |
| Kurztext                     | ShortText                |                 |               |
| pencil icon                  | ActiveRole               |                 |               |
| not found                    | Visibility               |                 |               |
| not found                    | StartOfProductionDate    |                 |               |
| not found                    | VBV                      |                 |               |
| not found                    | Section                  |                 |               |
| Häufigkeit                   | Frequency                |                 |               |
| Reproduzierbar               | Repeatable               |                 |               |
| E-Projekt                    | EProject                 |                 |               |
| not found                    | AuthorityToClose         |                 |               |
| not found                    | AuthorityToOutgoingCheck |                 |               |
| Funktion                     | Function                 |                 |               |
| Land                         | Country                  |                 |               |
| FB-Status                    | EngineeringStatus        |                 |               |
| L-Status (Lieferantenstatus) | SupplierStatus           |                 |               |
| not found                    | EstimatedStartDate       |                 |               |
| not found                    | Keyword                  |                 |               |
| not found                    | TCB                      |                 |               |
| not found                    | LaunchPriority           |                 |               |
| not found                    | TrafficLight             |                 |               |

### Häufigkeit / Frequency

| KPM UI   | KPM API |
| -------- | ------- |
| einmalig | XE      |
| mehrmals | XF      |
| immer    | XG      |

### Reproduzierbar / Repeatable

| KPM UI | KPM API |
| ------ | ------- |
| ja     | XH      |
| nein   | XI      |

### ForemostGroupProject

| Field name                | API (Dict) field name | Jira UI field          |
| ------------------------- | --------------------- | ---------------------- |
| Konzern-Projekt (field 1) | Brand                 | -                      |
| Konzern-Projekt (field 2) | Project               | -                      |
| Konzern-Projekt (field 3) | Extension             | -                      |
| not found                 | Reporting             | -                      |
| not found                 | LaunchPriority        | -                      |
| Funktionsvariante         | PartName              | -                      |
| HW                        | Hardware              | Hardware (req.)        |
| SW                        | Software              | Affects Version (req.) |
| not found                 | EEDeviceType          | -                      |
| not found                 | SeFt                  | -                      |

### ForemostTestPart --> PartNumber

| Field name            | API (Dict) field name | Required by KPM | Default input |
| --------------------- | --------------------- | --------------- | ------------- |
| Teilenummer (field 1) | PreNumber             | -               | -             |
| Teilenummer (field 2) | MiddleGroup           | -               | -             |
| Teilenummer (field 3) | EndNumber             | -               | -             |
| Teilenummer (field 4) | Index                 | -               | -             |
| Teilenummer (field 5) | Charge                | -               | -             |
| Teilenummer (field 6) | ChargeSerialNumber    | -               | -             |

### VerbundRelease

| Field name               | API (Dict) field name | Required by KPM | Default input | Jira UI field |
| ------------------------ | --------------------- | --------------- | ------------- | ------------- |
| Verbundrelease (field 1) | Major                 | -               | -             | AudiVR (req.) |
| Verbundrelease (field 2) | Minor                 | -               | -             | AudiVR (req.) |
| Verbundrelease (field 2) | Extend                | -               | -             | AudiVR (req.) |

### Not required for KPMST

- Creator --> Address
- Creator --> PersonalContractor
- Coordinator --> Contractor --> Address
- Coordinator --> Contractor --> PersonalContractor
- ProblemSolver --> Contractor --> Address
- SpecialistCoordinator --> Contractor --> Address
- Supplier --> Contractor --> Address
- Supplier --> Contractor --> PersonalContractor

### Origin (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | Phase                 | -               | -             |
| not found  | PhaseAddition         | -               | -             |
| not found  | SubProcess            | -               | -             |
| not found  | MainProcess           | -               | -             |

### Coordinator (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | OrderType             | -               | -             |
| not found  | Status                | -               | -             |

### ProblemSolver (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | OrderType             | -               | -             |
| not found  | DueDate               | -               | -             |
| not found  | Status                | -               | -             |

### SpecialistCoordinator (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | OrderType             | -               | -             |
| not found  | DueDate               | -               | -             |
| not found  | Status                | -               | -             |

### Kefa (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | Type                  | -               | -             |
| not found  | DefectObjectId        | -               | -             |
| not found  | DefectTypeId          | -               | -             |

### ModuleRelevant (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | ModuleRelevant        | -               | -             |

### Supplier (not required for KPMST)

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | OrderType             | -               | -             |
| not found  | DueDate               | -               | -             |
| not found  | Status                | -               | -             |

## Defaults

Default "blocks" which recur

### Address

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | AddressTimestamp      | -               | -             |
| not found  | ContactPerson         | -               | -             |
| not found  | Description           | -               | -             |
| not found  | OrganisationalUnit    | -               | -             |
| not found  | Group                 | -               | -             |
| not found  | Plant                 | -               | -             |

### PersonalContractor

| Field name | API (Dict) field name | Required by KPM | Default input |
| ---------- | --------------------- | --------------- | ------------- |
| not found  | UserId                | -               | -             |
| not found  | UserName              | -               | -             |
| not found  | Email                 | -               | -             |
| not found  | Phone                 | -               | -             |

### Attachments

UI: Found on the left side / "Extras" tab --> "Dokumente"
API: Access the list directly with GetDocumentList and a single Document with GetDocument

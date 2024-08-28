# Jira Integration Issue overview

This applies for the issue type: Integration

| Field name              | API field name                | Type      | Required by Jira | Default input     |
| ----------------------- | ----------------------------- | --------- | ---------------- | ----------------- |
| Project                 | project                       | project   | yes              | Audi HCP5 (AHCP5) |
| Issue Type              | issuetype                     | issuetype | yes              | Integration       |
| Summary                 | summary                       | string    | yes              | -                 |
| Linked Issues           | issuelinks                    | array     | no               | -                 |
| Issue                   | issuekey                      | -         | no               | -                 |
| Teams                   | customfield_12733             | option    | no               | -                 |
| Description             | description                   | string    | yes              | -                 |
| Priority                | priority                      | priority  | no               | Major             |
| Labels                  | labels                        | array     | no               | -                 |
| Assignee                | assignee                      | user      | yes              | automatic         |
| Specification           | customfield_12732             | string    | no               | -                 |
| Requirement IDs         | customfield_10100             | string    | no               | -                 |
| Audi Domain             | customfield_12613             | array     | no               | -                 |
| Audi Cluster            | customfield_12600             | array     | yes              | -                 |
| Components              | components                    | array     | yes              | -                 |
| Sprint                  | customfield_10007             | array     | no               | -                 |
| Due date                | duedate                       | date      | no               | -                 |
| Fix versions            | fixVersions                   | array     | no               | -                 |
| Affects versions        | versions                      | array     | yes              | -                 |
| Hardware                | customfield_10500             | string    | yes              | -                 |
| Testcase ID             | customfield_12693             | string    | no               | -                 |
| Origin                  | customfield_12640             | option    | yes              | -                 |
| External Reference      | customfield_10503             | string    | yes              | -                 |
| External Reference Link | customfield_10902             | string    | no               | -                 |
| Affected workproducts   | customfield_12708             | array     | no               | -                 |
| Original estimate       | aggregatetimeoriginalestimate | number    | no               | -                 |
| Remaining Estimate      | timeestimate                  | number    | no               | -                 |
| Epic Link               | customfield_10008             | any       | no               | -                 |
| Audi VR                 | customfield_12740             | array     | no               | -                 |
| Attachment (Files)      | attachment                    | array     | no               | -                 |

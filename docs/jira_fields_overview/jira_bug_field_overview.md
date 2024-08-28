# Jira Bug field overview

This applies for the issue type: Bug

| Field name            | API field name    | Type      | Required by Jira | Default input     |
| --------------------- | ----------------- | --------- | ---------------- | ----------------- |
| Project               | project           | project   | yes              | Audi HCP5 (AHCP5) |
| Issue Type            | issuetype         | issuetype | yes              | Bug               |
| Summary               | summary           | string    | yes              | -                 |
| Description           | description       | string    | yes              | -                 |
| Priority              | priority          | priority  | yes              | Major             |
| Specification         | customfield_12732 | string    | no               | -                 |
| Testcase ID           | customfield_12693 | string    | no               | -                 |
| Labels                | labels            | array     | no               | -                 |
| Assignee              | assignee          | user      | yes              | automatic         |
| External Reference    | customfield_10503 | string    | no               | -                 |
| Components            | components        | array     | yes              | -                 |
| Audi Domain           | customfield_12613 | array     | no               | -                 |
| Audi Cluster          | customfield_12600 | array     | yes              | -                 |
| Affects versions      | versions          | array     | yes              | -                 |
| Due date              | duedate           | date      | no               | -                 |
| Hardware              | customfield_10500 | string    | yes              | -                 |
| Reproducibility       | customfield_10501 | option    | yes              | -                 |
| Problem Finder        | customfield_10900 | string    | yes              | -                 |
| Origin                | customfield_12640 | option    | no               | -                 |
| Affected workproducts | customfield_12708 | array     | no               | -                 |
| Cause of bug          | customfield_10901 | option    | no               | -                 |
| Cause of Reject       | customfield_12713 | option    | no               | -                 |
| Fix versions          | fixVersions       | array     | no               | -                 |
| Sprint                | customfield_10007 | array     | no               | -                 |
| Epic Link             | customfield_10008 | any       | no               | -                 |
| Attachment (Files)    | attachment        | array     | no               | -                 |

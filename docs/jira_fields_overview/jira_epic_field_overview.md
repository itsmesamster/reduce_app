# Jira Epic field overview

This applies for the issue type: Epic

| Field name               | API field name    | Type      | Required by Jira | Default input     |
| ------------------------ | ----------------- | --------- | ---------------- | ----------------- |
| Project                  | project           | project   | yes              | Audi HCP5 (AHCP5) |
| Issue Type               | issuetype         | issuetype | yes              | Epic              |
| Summary                  | summary           | string    | yes              | -                 |
| Epic Name                | customfield_10009 | string    | yes              | -                 |
| Teams                    | customfield_12733 | option    | no               | -                 |
| Description              | description       | string    | yes              | -                 |
| Priority                 | priority          | priority  | no               | -                 |
| Labels                   | labels            | array     | no               | -                 |
| Assignee                 | assignee          | user      | yes              | automatic         |
| Specification            | customfield_12732 | string    | no               | -                 |
| Audi Domain              | customfield_12613 | array     | no               | -                 |
| Audi Cluster             | customfield_12600 | array     | yes              | -                 |
| Components               | components        | array     | yes              | -                 |
| Due date                 | duedate           | date      | no               | -                 |
| Fix versions             | fixVersions       | array     | no               | -                 |
| Affects versions         | versions          | array     | no               | -                 |
| Hardware                 | customfield_10500 | string    | no               | -                 |
| Sprint                   | customfield_10007 | array     | no               | -                 |
| External Reference       | customfield_10503 | string    | no               | -                 |
| External Reference Link  | customfield_10902 | string    | no               | -                 |
| Affected workproducts    | customfield_12708 | array     | no               | -                 |
| Story Points             | customfield_10004 | number    | no               | -                 |
| Story point estimate     | customfield_12654 | number    | no               | -                 |
| Epic Link **Jira error** | customfield_10008 | any       | no               | -                 |
| Attachment (Files)       | attachment        | array     | no               | -                 |

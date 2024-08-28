# Jira Change Request field overview

This applies for the issue type: Change Request

| Field name              | API field name    | Type      | Required by Jira | Default input     |
| ----------------------- | ----------------- | --------- | ---------------- | ----------------- |
| Project                 | project           | project   | yes              | Audi HCP5 (AHCP5) |
| Issue Type              | issuetype         | issuetype | yes              | Change Request    |
| Summary                 | summary           | string    | yes              | -                 |
| Description             | description       | string    | yes              | -                 |
| Priority                | priority          | priority  | no               | -                 |
| Labels                  | labels            | array     | no               | -                 |
| Assignee                | assignee          | user      | yes              | automatic         |
| Specification           | customfield_12732 | string    | no               | -                 |
| Requirement IDs         | customfield_10100 | string    | no               | -                 |
| Audi Domain             | customfield_12613 | array     | no               | -                 |
| Audi Cluster            | customfield_12600 | array     | yes              | -                 |
| Origin                  | customfield_12640 | option    | no               | -                 |
| Components              | components        | array     | yes              | -                 |
| Due date                | duedate           | date      | no               | -                 |
| Teams                   | customfield_12733 | option    | no               | -                 |
| Fix versions            | fixVersions       | array     | no               | -                 |
| Hardware                | customfield_10500 | array     | no               | -                 |
| Sprint                  | customfield_10007 | array     | no               | -                 |
| External Reference      | customfield_10503 | string    | yes              | -                 |
| External Reference Link | customfield_10902 | string    | yes              | -                 |
| Quotation Number        | customfield_11401 | string    | no               | -                 |
| Order Number            | customfield_11402 | string    | no               | -                 |
| Invoice Number          | customfield_11403 | string    | no               | -                 |
| CR Effort (in days)     | customfield_11100 | number    | no               | -                 |
| Epic Link               | customfield_10008 | any       | no               | -                 |
| Attachment (Files)      | attachment        | array     | no               | -                 |

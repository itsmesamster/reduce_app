# Jira GRC_Risk Issue overview

This applies for the issue type: GRC_Risk

| Field name              | API field name    | Type      | Required by Jira | Default input     |
| ----------------------- | ----------------- | --------- | ---------------- | ----------------- |
| Project                 | project           | project   | yes              | Audi HCP5 (AHCP5) |
| Issue Type              | issuetype         | issuetype | yes              | GRC_Risk          |
| Summary                 | summary           | string    | yes              | -                 |
| Priority                | priority          | priority  | no               | Major             |
| Assignee                | assignee          | user      | yes              | automatic         |
| Components              | components        | array     | yes              | -                 |
| Description             | description       | string    | yes              | -                 |
| Labels                  | labels            | array     | no               | -                 |
| Risk Cause Description  | customfield_12630 | string    | no               | -                 |
| GRC_Likelihood          | customfield_12626 | option    | no               | -                 |
| GRC_Impact              | customfield_12625 | option    | no               | -                 |
| Risk Impact Description | customfield_12628 | string    | no               | -                 |
| GRC_Score               | customfield_12627 | option    | no               | -                 |
| GRC_Risk Domain         | customfield_12624 | array     | no               | -                 |
| GRC_Risk Type           | customfield_12623 | option    | no               | -                 |
| GRC_Decision            | customfield_12721 | option    | no               | -                 |
| Linked Issues           | issuelinks        | array     | no               | -                 |
| Issues                  | issuekey          | -         | no               | -                 |
| Attachment (Files)      | attachment        | array     | no               | -                 |
| Audi Cluster            | customfield_12600 | array     | yes              | -                 |
| Audi Domain             | customfield_12613 | array     | no               | -                 |
| Due date                | duedate           | date      | no               | -                 |
| Start date              | customfield_12639 | date      | no               | -                 |

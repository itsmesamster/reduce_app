# Jira overview of all HCP5 issue types

- Task
- Bug
- Epic
- Story
- Feature
- Change Request
- Improvement
- Customer Issue
- Integration
- GRC_Risk
- Approve
- Create

| Field name              | API field name                | Type      |
| ----------------------- | ----------------------------- | --------- |
| Project                 | project                       | project   |
| Issue Type              | issuetype                     | issuetype |
| Linked Issues           | issuelinks                    | array     |
| Issue                   | issuekey                      | -         |
| Summary                 | summary                       | string    |
| Teams                   | customfield_12733             | option    |
| Description             | description                   | string    |
| Priority                | priority                      | priority  |
| Labels                  | labels                        | array     |
| Assignee                | assignee                      | user      |
| Specification           | customfield_12732             | string    |
| Requirement IDs         | customfield_10100             | string    |
| Audi Domain             | customfield_12613             | array     |
| Audi Cluster            | customfield_12600             | array     |
| Components              | components                    | array     |
| Sprint                  | customfield_10007             | array     |
| Duedate                 | duedate                       | date      |
| Fixversions             | fixVersions                   | array     |
| Affects versions        | versions                      | array     |
| Hardware                | customfield_10500             | string    |
| Testcase ID             | customfield_12693             | string    |
| Origin                  | customfield_12640             | option    |
| External Reference      | customfield_10503             | string    |
| External Reference Link | customfield_10902             | string    |
| Affected workproducts   | customfield_12708             | array     |
| Original estimate       | aggregatetimeoriginalestimate | number    |
| Remaining Estimate      | timeestimate                  | number    |
| Epic Link               | customfield_10008             | any       |
| Attachment (Files)      | attachment                    | array     |
| Quotation Number        | customfield_11401             | string    |
| Order Number            | customfield_11402             | string    |
| Invoice Number          | customfield_11403             | string    |
| CR Effort (indays)      | customfield_11100             | number    |
| Reproducibility         | customfield_10501             | option    |
| Problem Finder          | customfield_10900             | string    |
| Cause of bug            | customfield_10901             | option    |
| Cause of Reject         | customfield_12713             | option    |
| Risk Cause Description  | customfield_12630             | string    |
| Risk Impact Description | customfield_12628             | string    |
| GRC_Likelihood          | customfield_12626             | option    |
| GRC_Impact              | customfield_12625             | option    |
| GRC_Score               | customfield_12627             | option    |
| GRC_Risk Domain         | customfield_12624             | array     |
| GRC_Risk Type           | customfield_12623             | option    |
| GRC_Decision            | customfield_12721             | option    |
| Start date              | customfield_12639             | date      |
| Audi VR                 | customfield_12740             | array     |
| Story Points            | customfield_10004             | number    |
| Story point estimate    | customfield_12654             | number    |
| Epic Name               | customfield_10009             | string    |

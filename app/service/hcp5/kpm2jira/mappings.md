KPM conditions for a KPM ticket to be considered for sync:


1. Given a KPM ticket ID (Developement Problem ID), our ESR Labs Technical System User should have access to the ticket

2. Given a KPM ticket, The Plant and Organizational Unit should be as in the provided KPM Inbox for Sync

3. The KPM ticket should have the KPM Supplier (DevelopmentProblem.../Supplier/Contractor/PersonalContractor/UserId) in the list of pre-defined ESR Labs Users (Guido, Veronika, Fabienne)

4. The KPM ProblemStatus shouldn't be "5" or "6" -> If so: Ignore, ticket already closed

5. There should be a SupplierStatus set


If all the above conditions are met, then the KPM ticket will be transformed in an ESR Jira one:

hardcoded:
    project: "AHCP5"
    issuetype: "Customer Issue"
    Origin / customfield_12640: "Audi KPM"

mapped from KPM:
    summary <- ShortText
    description <- Description
    priority <- Rating
    assignee <- AccountID
    External Reference / customfield_10503 <- ProblemNumber
    components <- Function
    Audi Cluster / customfield_12600 <- Custom value, based on external map, based on software version (KPM's "ForemostTestPart/Software")
    versions <- ForemostTestPart/Software
    Hardware / customfield_10500: Hardware
    Reproducibility / customfield_10501 <- Reproducibility
    Problem Finder / customfield_10900 <- Exclaimer
    Audi VR / customfield_12740 <- VerbundRelease
    Part Number / customfield_12748 <- PartNumber

other extra mappings after initial ticket creation:
    adding creation supplier response to KPM ticket
    attachments from KPM to ESR
    automated comments
    status (from ESR to KPM)
    Question to OEM / customfield_12759 (from ESR Jira to KPM)
    Feedback to OEM / customfield_12743
    Feedback from OEM / customfield_12742
    Answer from OEM / customfield_12760
    Cause of reject / customfield_12713


* many extra syncs depend on other changes in values like statuses


Check the mandatory Customer Issue fields at issue/ticket creation by looking for "required": true here:
https://esrlabs.atlassian.net/rest/api/latest/issue/createmeta?projectKeys=AHCP5&issuetypeNames=Customer%20Issue&expand=projects.issuetypes.fields

Required:
    issuetype
    components
    description
    project
    summary
    priority
    versions
    assignee
    customfield_10500
    customfield_10501
    customfield_10503
    customfield_10900
    customfield_12640
    customfield_12600
    



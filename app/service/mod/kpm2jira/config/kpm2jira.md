Sync assumptions agreed:

*   Jira Fields to Sync:

    *   **KPM -> JIRA**:

        *   `Title` + `Description`
        *   `Feedback to OEM`: Sync entire list of process step ids from KPM's `Lieferantenaussage` - each process step starts with date + time + email e.g.:
            *   2023/06/27 11:07:59 | email_example@cariad.technology

        *   `Feedback from OEM` : Sync entire list of process step ids from KPM's `Analyse abgeschlossen` - each process step starts with date + time + email e.g.:
            *   2023/06/27 11:07:59 | email_example@cariad.technology

        *   `Answer from OEM` : Sync entire list of process step ids from KPM's `Antwort` - *to be tested again and decided if this will be always the case*
        *   **`All Attachments`**
        *   DETAILS (column on the right side of the webpage):

            *   `Priority`
            *   `Assignee`: automatic assignment / none or to a Technical System User ??
            *   `Reporter`: now the system uses Guido's user, but a Technical System User should be created
            *   `External Reference` - KPM ticket ID
            *   `Audi Cluster`
            *   `Affects versions`
            *   `Audi VR`
            *   `Part Number`
            *   `Hardware`: only when found in KPM, if not: -
            *   `Reproducibility`
            *   `Problem Finder`
            *   `Origin`: "*Audi KPM"*



    *   **JIRA -> KPM**:

        *   `Supplier ID` (Jira ID) - share back the JIRA ticket ID (AHCP5-2420x) after a new Jira ticket was created with KPM data
        *   `Question to OEM` (used also for "`Cause of Reject`")
        *   ***are there any other Jira fields to be synced back to KPM?***


    *   **Don't sync:**

        *   **Jira comments**
        *   `Specification`
        *   `Testcase ID`
        *   DETAILS (column on the right side of the webpage):
            *   `Components` to be selected manually (as a guess?) after the automatic ticket creation
            *   `Audi Domain`  - to sync or not to sync ?
            *   `Fix versions`
            *   `Labels`
            *   `Affected Area`
            
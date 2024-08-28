# standard
from time import sleep
from datetime import datetime
import re

# external
from jira import Issue, Comment, User
from jira.resources import Attachment
from jira.exceptions import JIRAError
import yaml

# project core
from app.core.utils import timed_cache, performance_check, approximate_comparison


# project extension

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.jira_client_esr_j2j import (
    ESRLabsJiraClientForVwJiraSync,
)
from app.service.hcp5.jira2jira.jira_client_vwaudi import Hcp5VwAudiJiraClient
from app.service.hcp5.jira2jira.jira_issue_esr4vw import EsrIssueForVwJiraSync
from app.service.hcp5.jira2jira.jira_issue_vwaudi import Hcp5VwAudiJiraIssue
from app.service.hcp5.jira2jira.transformer import (
    EsrJira2VwAudiJiraTransformer as J2jMapper,
)
from app.service.hcp5.jira2jira.sync_exceptions import JiraCommentConversionError
from app.service.hcp5.jira2jira.config import (
    POST_BACK_TO_VW_JIRA,
    J2J_VWAUDI_JIRA,
    VW_ESR_USER_EXT,
)


class NewEsrJiraFromVwAudiJira:
    def __init__(
        self,
        esr_jira_client: ESRLabsJiraClientForVwJiraSync,
        vw_jira_client: Hcp5VwAudiJiraClient,
        transformer: J2jMapper = None,
    ):
        self.logger = logger
        self.esr_jira: ESRLabsJiraClientForVwJiraSync = esr_jira_client
        self.vw_jira: Hcp5VwAudiJiraClient = vw_jira_client
        self.transformer: J2jMapper = transformer or J2jMapper(self.esr_jira)

    # @timed_cache
    def add_issue(self, vw_id: str) -> EsrIssueForVwJiraSync | None:  # to ESR JIRA
        """Create new ESR Jira issue from existing VW Jira ID...
        OR get existing ESR Jira issue if already present."""
        self.logger.info(
            f"Create new ESR Jira issue from VW Jira issue: {vw_id} ... "
            f"OR get existing one if already present.",
            vw_id=vw_id,
        )

        # 2. Fetch issue / ticket / development problem from VW Jira
        vw_ticket: Hcp5VwAudiJiraIssue = self.vw_jira.issue(vw_id)
        if not vw_ticket:
            self.logger.debug("Not a valid ticket", vw_id=vw_id)
            return

        self.logger.debug(f"{vw_id} VW Audi ticket yaml:\n{vw_ticket.yaml}")

        # 3. Convert VW Jira ticket to Jira ticket
        ticket_ready_for_esr_jira: EsrIssueForVwJiraSync = self.transformer.to_esr_jira(
            vw_ticket
        )
        if not ticket_ready_for_esr_jira:
            self.logger.warning(
                "VW Jira ticket was not converted to be added to ESR Jira", vw_id=vw_id
            )
            return

        # 4. Add newly created issue to JIRA
        try:
            jira_response = self.esr_jira.add_ticket(ticket_ready_for_esr_jira)
            if isinstance(jira_response, Issue) and jira_response.key:
                new_esr_id = jira_response.key
                self.logger.debug(
                    f"Created new ESR Jira issue with ID: {new_esr_id}",
                    esr_id=new_esr_id,
                )
            else:
                self.logger.error("Failed to create new ESR Jira issue", vw_id=vw_id)
                return
        except JIRAError as e:
            err_msg = f"Failed to create new ESR Jira issue for VW Jira ID {vw_id}: {e}"
            self.logger.error(err_msg)
            raise JIRAError(err_msg)

        try_times = 3
        for try_ in range(1, try_times + 1):
            sleep(2)
            esr_issue: EsrIssueForVwJiraSync = self.esr_jira.issue(new_esr_id)
            if esr_issue:
                self.logger.info(
                    f"Successfully created {jira_response} for VW Jira ID {vw_id}",
                    vw_id=vw_id,
                    esr_id=new_esr_id,
                )
                break
            elif try_ == try_times:
                self.logger.error(
                    "Failed to get ESR Jira issue after creation",
                    vw_id=vw_id,
                    esr_id=new_esr_id,
                )
                raise JIRAError(err_msg)

        # ESR Jira -> VW Jira
        # 5. ADD ESR Labs label to VW
        if POST_BACK_TO_VW_JIRA:
            self.vw_jira.add_label(vw_id, "ESR")
        else:
            self.logger.warning(
                "POST_BACK_TO_VW_JIRA is set to False. "
                "Not adding label ESR Labs to VW Jira issue in VW Jira",
                vw_id=vw_id,
                esr_id=new_esr_id,
            )

        return esr_issue


class SyncHCP5JiraEsrFromJiraVwAudi(NewEsrJiraFromVwAudiJira):
    # VW JIRA -> ESR JIRA

    ### ATTACHMENTS ### ->

    def compare_docs_details(
        self,
        vw_docs: list[dict],
        esr_docs: list[dict],
    ) -> list[dict]:
        """Normalize attachment dict list"""
        diff = []

        filtered_esr_docs = [
            {k: v for k, v in doc.items() if k not in ["created", "id", "vol"]}
            for doc in esr_docs
        ]

        for vw_doc in vw_docs:
            filename: str = vw_doc["filename"]
            created: str = (
                vw_doc["created"]
                .rsplit(":", 1)[0]
                .replace("T", "@")
                # ":" will be auto-replaced in Jira with "_"
                .replace(":", ".")
                .replace("-", ".")
            )
            name_split: list = filename.rsplit(".", 1)
            name: str = name_split[0]
            name_len: int = len(name_split)
            suffix: str = f".{name_split[-1]}" if name_len == 2 else ""
            name_with_date: str = f"{name}({created}){suffix}"

            new_doc = {"filename": name_with_date, "size": vw_doc.get("size")}
            if new_doc not in filtered_esr_docs:
                vw_doc["name_with_date"] = name_with_date
                diff.append(vw_doc)

        return diff

    def compare_attachments_lists(
        self,
        vw_issue: Hcp5VwAudiJiraIssue,
        esr_issue: EsrIssueForVwJiraSync,
    ):
        """Compare attachments lists between VW Audi Jira and ESR Jira
        and return the list of attachments to be added to ESR Jira."""
        vw_id, esr_id = vw_issue.jira_id, esr_issue.jira_id
        if vw_id != esr_issue.vw_id:
            self.logger.error(
                f"VW Audi / ESR Labs Jira IDs mismatch. VW {vw_id} vs ESR {esr_id}",
                vw_id=vw_id,
                esr_id=esr_id,
            )
            return []

        vw_docs = vw_issue.attachments
        if not vw_docs:
            self.logger.info(
                "No attachments found for VW issue", vw_id=vw_id, esr_id=esr_id
            )
            return []

        esr_docs = esr_issue.attachments

        # compare lists
        docs_missing_or_different = self.compare_docs_details(vw_docs, esr_docs)
        if docs_missing_or_different:
            self.logger.warning(
                f"There are {len(docs_missing_or_different)} "
                "VW docs missing or different in ESR Jira:\n"
                f"{yaml.safe_dump(docs_missing_or_different)}",
                vw_id=vw_id,
                esr_id=esr_id,
            )

        return docs_missing_or_different

    def post_attachment_to_esr_jira(
        self,
        esr_issue: EsrIssueForVwJiraSync,
        doc_name: str,
        doc_data: bytes | str,
        doc_size: int,  # bytes
    ):
        """Post attachment to ESR Jira issue"""
        self.logger.debug(
            f"Posting attachment {doc_name} to " f"ESR Jira issue {esr_issue}"
        )
        # check if attachment already exists
        esr_docs = [doc.get("name") for doc in esr_issue.attachments]
        if not all([doc_name, doc_data, doc_size]):
            self.logger.error(
                "Something related to the attachment is missing: "
                f"\n{doc_name=}\ndoc_data ??\n{doc_size=}"
            )
            return
        if doc_name in esr_docs:
            self.logger.warning(
                f"Attachment {doc_name} already exists in "
                f"ESR Jira issue {esr_issue}"
            )
            for esr_doc in esr_issue.attachments:
                if doc_name == esr_doc.get("name"):
                    self.logger.error(yaml.safe_dump(esr_doc))
                if esr_size := esr_doc.get("size") != doc_size:
                    self.logger.error(
                        f"Attachment size mismatch: " f"ESR {esr_size}" f"VW {doc_size}"
                    )
                    raise ValueError("Attachment size mismatch.")
            return

        # Jira: Post attachment to ESR Jira issue
        attachment_response = self.esr_jira.add_attachment(
            esr_issue, doc_name, doc_data
        )
        self.logger.debug(f"{esr_issue}\n{attachment_response=}")
        return attachment_response

    # VW Audi Jira -> ESR Labs Jira
    # VW Audi Jira: Fetch document list
    def sync_attachments(self, esr_issue: EsrIssueForVwJiraSync):
        """Sync attachments from VW Audi Jira to ESR Labs Jira"""
        # Iterate attachments
        vw_issue: Hcp5VwAudiJiraIssue = self.vw_jira.issue(esr_issue.vw_id)
        if not vw_issue:
            self.logger.error(
                "Failed to fetch VW issue",
                vw_id=esr_issue.vw_id,
                esr_id=esr_issue.jira_id,
            )
            return

        doc_list_diff = self.compare_attachments_lists(vw_issue, esr_issue)

        # Download attachments from VW Audi Jira and Upload to ESR Labs Jira
        for vw_doc_ref in doc_list_diff:
            vw_doc_id = vw_doc_ref.get("id")
            vw_doc_name = vw_doc_ref.get("filename")
            vw_doc_size = vw_doc_ref.get("size")
            name_with_date = vw_doc_ref.get("name_with_date")

            if not all(
                [esr_issue, vw_doc_id, vw_doc_name, vw_doc_size, name_with_date]
            ):
                self.logger.error(
                    f"Missing mandatory data for the attachment sync:\n"
                    f"{esr_issue.jira_id=} {vw_doc_id=} {vw_doc_name=} "
                    f"{vw_doc_size=} {name_with_date=}",
                    vw_id=esr_issue.vw_id,
                    esr_id=esr_issue.jira_id,
                )
                continue

            # VW Audi Jira: Download attachment
            vw_doc_data = self.vw_jira.download_attachment(vw_issue, vw_doc_id)

            # Jira: Post attachment
            if vw_doc_data:
                jira_doc_post_success = self.post_attachment_to_esr_jira(
                    esr_issue, name_with_date, vw_doc_data, vw_doc_size
                )
            else:
                self.logger.error(
                    f"VW/Audi Devstack Jira document download failed: "
                    f"{vw_doc_name} [size: {vw_doc_size}] to {esr_issue}"
                )
                continue

            if jira_doc_post_success:
                self.logger.debug(
                    f"Jira attachment post successfull: {name_with_date} "
                    f"[size: {vw_doc_size}] to {esr_issue}"
                )
            else:
                self.logger.error(
                    f"Jira attachment post failed: {name_with_date} "
                    f"[size: {vw_doc_size}]  to {esr_issue}"
                )

    ### ATTACHMENTS NAMES MENTIONS CONVERSION -> ###

    def remove_datetime_from_name(self, name: str):
        """Find out how the original file name was,
        before adding the date and time of the creation to its name
        (from an external system)
        """
        # with: HCP5_Impact Analyse_SWC_Grundsatzentscheid_ECM(2024.01.23@11.10).pdf
        # without: HCP5_Impact Analyse_SWC_Grundsatzentscheid_ECM.pdf

        # with: file(2024.01.23@11.10)
        # without: file

        return re.sub("\(\d{4}\.\d{2}\.\d{2}@\d{1,2}\.\d{2}\)", "", name)

    @performance_check
    def replace_attachments_mentions_with_new_names(self, text: str, esr_id: str):
        attachments_list: list = self.esr_jira.get_cached_attachments_list(esr_id)
        attachments_names = {}
        for attachment in attachments_list:
            attachment: Attachment = attachment
            if datetime_filename := attachment.raw.get("filename"):
                simple_name = self.remove_datetime_from_name(datetime_filename)
                attachments_names[simple_name] = datetime_filename

        for simple_name, datetime_filename in attachments_names.items():
            simple_name = f"!{simple_name}"
            datetime_filename = f"!{datetime_filename}"
            if simple_name in text:
                text = text.replace(simple_name, datetime_filename)
                self.logger.info(
                    f"replaced name {simple_name} -> {datetime_filename}", esr_id=esr_id
                )
        return text

    ### COMMENTS ### ->

    def replace_external_tickets_mentions_with_links(self, text: str):
        if " HCP5-" in text:
            text = text.replace(" HCP5-", f" {J2J_VWAUDI_JIRA.server}browse/HCP5-")
        return text

    def replace_vw_users_mentions_with_esr_user_names(
        self, text: str, begin: str = "[~", end: str = "]"
    ):
        count = text.count(begin)
        mentions = text.split(begin)
        if len(mentions) < 2:
            return text
        mentions = mentions[1:]
        users = []
        for mention in mentions:
            user_id = mention.split(end)[0]
            if len(user_id) == 7:
                users.append(user_id)
        if count != len(users):
            self.logger.error("something is wrong: count != len(users)")
            return text
        for user_id in set(users):
            vw_user_name: User = self.vw_jira.get_user_data(user_id) or f"{user_id}"
            if any(substr in str(vw_user_name).lower() for substr in VW_ESR_USER_EXT):
                user_name = str(vw_user_name).split(" (EXTERN: ")[0]
                esr_user_data: User = self.esr_jira.get_user_by_name(user_name)
                if not esr_user_data:
                    continue
                esr_user_id = esr_user_data.raw.get("accountId")
                text = text.replace(
                    f"[~{user_id}]", f"*{vw_user_name}* [~accountid:{esr_user_id}]"
                )
            else:
                text = text.replace(f"[~{user_id}]", f"*{vw_user_name}*")
        return text

    @timed_cache
    def vw_comment_header_for_esr(self, comment: Comment, source_vw_jira_id: str):
        if not isinstance(comment, Comment):
            err_msg = "this comment is not of type jira.Comment"
            self.logger.error(err_msg, vw_id=source_vw_jira_id)
            raise JiraCommentConversionError(err_msg)

        comment_id = comment.raw.get("id", "")
        focused_comment_link = (
            f"{J2J_VWAUDI_JIRA.server}browse/"
            f"{source_vw_jira_id}?focusedCommentId={comment_id}"
        )
        author_id = comment.raw.get("updateAuthor", {}).get("name", "")
        author_email = comment.raw.get("updateAuthor", {}).get("emailAddress", "")
        created_date = comment.raw.get("created", "").split(".")[0].replace("T", " ")
        updated_date = comment.raw.get("updated", "").split(".")[0].replace("T", " ")

        comment_header = (
            f"📆 {created_date} | "
            f"📮 {author_email} ({author_id}) | "
            f"📆 updated: {updated_date}\n"
            f"🔗 {focused_comment_link}"
        )
        if updated_date == created_date:
            comment_header = comment_header.replace(
                f" | 📆 updated: {updated_date}", ""
            )  # noqa: E501
        if not comment_header:
            try:
                err_msg = (
                    "Failed to create the Comment header -> "
                    f"Comment ID {comment} raw:\n{yaml.safe_dump(comment.raw)}"
                )
                self.logger.error(err_msg, vw_id=source_vw_jira_id)
            except Exception:
                err_msg = "Failed to create the Comment header"
                self.logger.error(err_msg, vw_id=source_vw_jira_id)
                print(
                    f"FAILED conversion for Comment ID {comment} raw:\n"
                    f"{yaml.safe_dump(comment.raw)}"
                )
            finally:
                raise JiraCommentConversionError(err_msg)

        return comment_header

    def convert_vw_comment(self, comment: Comment, source_vw_jira_id: str, esr_id: str):
        if not isinstance(comment, Comment):
            err_msg = "this comment is not of type jira.Comment"
            self.logger.error(err_msg, esr_id=esr_id, vw_id=source_vw_jira_id)
            raise JiraCommentConversionError(err_msg)

        text = comment.raw.get("body", "")
        text = self.replace_vw_users_mentions_with_esr_user_names(text)
        text = self.replace_attachments_mentions_with_new_names(text, esr_id)
        text = self.replace_external_tickets_mentions_with_links(text)
        if not text:
            err_msg = "Failed to convert VW Audi Jira comment to ESR format"
            self.logger.error(err_msg, esr_id=esr_id, vw_id=source_vw_jira_id)
            raise JiraCommentConversionError(err_msg)

        comment_header = self.vw_comment_header_for_esr(comment, source_vw_jira_id)

        return f"{comment_header}\n\n📝 {text}"

    # VW Audi Jira -> ESR Labs Jira
    def sync_comments(
        self,
        esr_issue: EsrIssueForVwJiraSync,
        after_date: datetime,
        ignored_users: list[str] = J2J_VWAUDI_JIRA.COMMENTS_SYNC_IGNORED_USERS,
    ) -> list[str]:
        """Sync comments from VW Audi Jira to ESR Labs Jira.
        VW Audi Jira: Fetch comment list.
        ESR Labs Jira: Fetch, compare and post comments.
        """
        vw_id = esr_issue.vw_id
        esr_id = esr_issue.jira_id

        vw_issue: Hcp5VwAudiJiraIssue = self.vw_jira.issue(vw_id)
        if not vw_issue:
            self.logger.error("Failed to fetch VW issue", vw_id=vw_id, esr_id=esr_id)
            return

        esr_issue = self.esr_jira.issue_by_ext_id(vw_id)
        if not esr_issue:
            self.logger.error("Failed to fetch ESR issue", vw_id=vw_id, esr_id=esr_id)
            return

        # Iterate VW comments
        vw_comments_added_to_esr = []
        vw_comments_list = self.vw_jira.get_all_comments_for_issue_after_date(
            vw_issue,
            after_date,
        )

        for vw_comment in vw_comments_list:
            vw_comment: Comment = vw_comment

            comment_author_id = vw_comment.raw.get("updateAuthor", {}).get("name", "")
            if comment_author_id in ignored_users:
                continue

            vw_comment_header = self.vw_comment_header_for_esr(vw_comment, vw_id)
            if not vw_comment_header:
                continue

            all_esr_comments_merged: str = self.esr_jira.get_all_comments_merged_as_str(
                esr_issue
            )

            if vw_comment_header in all_esr_comments_merged:
                self.logger.info(
                    "Comment header already in ESR comments list:\n"
                    f"{vw_comment_header}",
                    vw_id=vw_id,
                    esr_id=esr_id,
                )
                continue

            vw_comment_text = vw_comment.raw.get("body", "")

            if vw_comment_text and vw_comment_text in all_esr_comments_merged:
                self.logger.info(
                    "Comment text already in ESR comments list:\n" f"{vw_comment_text}",
                    vw_id=vw_id,
                    esr_id=esr_id,
                )
                continue

            comment_to_post = self.convert_vw_comment(vw_comment, vw_id, esr_id)

            if comment_to_post and self.esr_jira.add_comment(
                esr_issue, comment_to_post, source="Cariad Devstack Jira"
            ):
                vw_comments_added_to_esr.append(vw_comment_header)

        vw_comments_added_to_esr_str = "\n\n".join(vw_comments_added_to_esr)
        self.logger.debug(
            f"Added {len(vw_comments_added_to_esr)} comments from VW "
            f"Audi/Cariad Jira to ESR:\n{esr_issue.info} :\n\n"
            f"{vw_comments_added_to_esr_str}\n",
            vw_id=vw_id,
            esr_id=esr_id,
        )

        return vw_comments_added_to_esr

    def sync_description(
        self,
        esr_issue: EsrIssueForVwJiraSync,
    ):
        esr_id = esr_issue.esr_id
        vw_id = esr_issue.vw_id
        esr_description: str = esr_issue.description or ""
        vw_jira_ticket: Hcp5VwAudiJiraIssue = self.vw_jira.issue(vw_id)
        vw_description: str = vw_jira_ticket.description or ""
        modified_vw_description = self.replace_attachments_mentions_with_new_names(
            vw_description, esr_id
        )
        if not approximate_comparison(modified_vw_description, esr_description):
            if self.esr_jira.update_description(esr_id, modified_vw_description):
                self.logger.info(
                    "ESR Labs Jira Ticket description was different "
                    "than Cariad's and was updated successfully.",
                    esr_id=esr_id,
                    vw_id=vw_id,
                )
                return True

            self.logger.error(
                "ESR Labs Jira Ticket description is different "
                "than Cariad's, but failed to be updated.",
                esr_id=esr_id,
                vw_id=vw_id,
            )
        self.logger.debug(
            "ESR Labs Jira Ticket description is the same with Cariad's.",
            esr_id=esr_id,
            vw_id=vw_id,
        )

    def update_description_mentions_of_doc_names(
        self, esr_issue: EsrIssueForVwJiraSync
    ):
        esr_id = esr_issue.jira_id
        descrip = esr_issue.description
        new_descrip = self.replace_attachments_mentions_with_new_names(descrip, esr_id)
        if new_descrip != descrip:
            esr_issue.update_fields(self.esr_jira._client, {"description": new_descrip})
            self.logger.info(
                "Updated description based on new attachments names", esr_id=esr_id
            )

    def sync_one(self, vw_jira_id: str) -> EsrIssueForVwJiraSync | None:
        """Sync one ticket from VW JIRA to ESR JIRA.

        1. CREATE new ESR Jira issue from VW Jira id (if doesn't exist)

        2. ADD/UPDATE custom fields

        3. ADD/UPDATE attachments
        """
        # 1. Check ESR Jira for existing VW ID (External Reference) in issue/ticket
        esr_jira_issue: EsrIssueForVwJiraSync = self.esr_jira.ticket_already_present(
            vw_id=vw_jira_id
        )
        if esr_jira_issue:
            self.sync_description(esr_jira_issue)
        else:
            # 2. CREATE/GET new ESR Jira issue based on VW id
            esr_jira_issue: EsrIssueForVwJiraSync = self.add_issue(vw_jira_id)
            # add or get existing
            if not esr_jira_issue:
                return

        if not isinstance(esr_jira_issue, EsrIssueForVwJiraSync):
            self.logger.error(
                'ESR Jira Issue is not of type "EsrIssueForVwJiraSync"'
                f"but of type {type(esr_jira_issue)}",
                vw_id=vw_jira_id,
            )
            return

        # 3. ADD/UPDATE JIRA custom fields + status (JIRA -> VW)
        # self.sync_status_and_extras_jira2vw(esr_jira_issue)

        # 4. ADD/UPDATE JIRA custom fields (VW -> JIRA)
        # self.sync_ticket_extras_vw2jira(esr_jira_issue)

        # 5. ADD/UPDATE attachments
        self.sync_attachments(esr_jira_issue)

        # 6. ADD/UPDATE comments
        AFTER_DATE = "2024-02-04"  # get VW comments only after February 4th 2024
        self.sync_comments(esr_jira_issue, AFTER_DATE)

        # 7. UPDATE description with new attachments names (VW creation datetime)
        self.update_description_mentions_of_doc_names(esr_jira_issue)

        return esr_jira_issue

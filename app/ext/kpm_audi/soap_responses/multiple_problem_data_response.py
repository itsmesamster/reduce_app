from app.ext.kpm_audi.soap_responses.base_response import BaseResponse


class MultipleProblemDataResponse(BaseResponse):
    def get_multiple_problem_data_response(self):
        match = f"{self.xmldef_kpm_v3}GetMultipleProblemDataResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_multiple_problem_data_response_internal(self):
        match = "GetMultipleProblemDataResponseInternal"
        element = self.get_multiple_problem_data_response()
        return self._find(element, match)

    def response_message(self):
        match = "ResponseMessage"
        element = self.get_multiple_problem_data_response_internal()
        return self._find(element, match)

    def problem_references(self):
        match = "ProblemReference"
        element = self.get_multiple_problem_data_response_internal()
        references = element.findall(match)
        return list(map(self._create_reference, references))

    def kpm_ids(self):
        """Convenience method to get all KPM IDs."""
        problem_refs = self.problem_references()
        return [problem_ref.problem_number for problem_ref in problem_refs]

    def _create_reference(self, reference):
        number = self._find(reference, "ProblemNumber")
        timestamp = self._find(reference, "LastChangeTimestamp")
        types_list = self._find(reference, "MessageTypeList")
        message_types = types_list.findall("MessageType")
        types = list(map(lambda t: t.text, message_types))
        return ProblemReference(
            number=number.text, timestamp=timestamp.text, types=types
        )


class ProblemReference:
    def __init__(self, number: str, timestamp: str, types: list[str]) -> None:
        self.problem_number = number
        self.last_change_timestamp = timestamp.split(".")[0]
        self.types = types

    @property
    def summary(self) -> str:
        return (
            f"KPM {self.problem_number}     "
            f"changed {self.last_change_timestamp}     "
            f"type {' '.join(self.types)}"
        )

    def __repr__(self) -> str:
        return str(self.problem_number)


from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class LiveSchemaMap:
    league: str
    physically_extracting_before_forensics: bool
    structured_candidates: int
    has_json_paths: bool
    has_token_contexts: bool
    action: str
    execution_authority: bool = False

def map_result(league,finding,already_extracting=False):
    if already_extracting:
        action="PRESERVE_WORKING_EXTRACTOR"
    elif finding.json_paths:
        action="BUILD_SOURCE_SPECIFIC_JSON_PATH_EXTRACTOR"
    elif finding.token_contexts:
        action="BUILD_SOURCE_SPECIFIC_HTML_OR_SCRIPT_STATE_EXTRACTOR"
    else:
        action="NO_EVENT_STRUCTURE_PROVEN"
    return LiveSchemaMap(
        league=league,
        physically_extracting_before_forensics=already_extracting,
        structured_candidates=finding.structured_candidates,
        has_json_paths=bool(finding.json_paths),
        has_token_contexts=bool(finding.token_contexts),
        action=action,
    )

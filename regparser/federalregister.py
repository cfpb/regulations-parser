import requests

from regparser.notice.build import build_notice

FR_BASE = "https://www.federalregister.gov"
API_BASE = FR_BASE + "/api/v1/"


def fetch_notice_json(cfr_title, cfr_part, only_final=False,
                      max_effective_date=None):
    """Search through all articles associated with this part. Right now,
    limited to 1000; could use paging to fix this in the future."""
    params = {
        "conditions[cfr][title]": cfr_title,
        "conditions[cfr][part]": cfr_part,
        "per_page": 1000,
        "order": "oldest",
        "fields[]": [
            "abstract", "action", "agency_names", "cfr_references", "citation",
            "comments_close_on", "dates", "document_number", "effective_on",
            "end_page", "full_text_xml_url", "html_url", "publication_date",
            "regulation_id_numbers", "start_page", "type", "volume"]}
    if only_final:
        params["conditions[type][]"] = 'RULE'
    if max_effective_date:
        params["conditions[effective_date][lte]"] = max_effective_date

    response = requests.get(API_BASE + "articles", params=params).json()
    if 'results' in response:
        return response['results']
    else:
        return []


def fetch_notices(cfr_title, cfr_part, only_final=False):
    """Search and then convert to notice objects (including parsing)"""
    notices = []
    for result in fetch_notice_json(cfr_title, cfr_part, only_final):
        notices.extend(build_notice(cfr_title, cfr_part, result))
    return notices

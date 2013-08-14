import json
import settings

from lxml import etree
import requests

from regparser.notice.build import build_notice

FR_BASE = "https://www.federalregister.gov"
API_BASE = FR_BASE + "/api/v1/"


def fetch_notices(cfr_title, cfr_part):
    """Search through all articles associated with this part. Right now,
    limited to 1000; could use paging to fix this in the future."""
    results = requests.get(API_BASE + "articles", params={
        "conditions[cfr][title]": cfr_title,
        "conditions[cfr][part]": cfr_part,
        "per_page": 1000,
        "order": "oldest",
        "fields[]": [
            "abstract", "action", "agency_names", "citation",
            "comments_close_on", "dates", "document_number", "effective_on",
            "end_page", "full_text_xml_url", "html_url", "publication_date",
            "regulation_id_numbers", "start_page", "type", "volume"
        ]}).json()

    notices = []
    for result in results['results']:
        notices.append(build_notice(cfr_title, cfr_part, result))
    return notices

import json
from lxml import etree
from regparser.notice.build import build_notice
import settings
from urllib import urlencode, urlopen

FR_BASE = "https://www.federalregister.gov"
API_BASE = FR_BASE + "/api/v1/"

def fetch_notices(cfr_title, cfr_part):
    """Search through all articles associated with this part. Right now,
    limited to 1000; could use paging to fix this in the future."""
    url = API_BASE + "articles?" + urlencode({
        "conditions[cfr][title]": cfr_title,
        "conditions[cfr][part]": cfr_part,
        "per_page": 1000,
        "order": "oldest",
        "fields[]": ["abstract", "action", "agency_names", "citation",
            "comments_close_on", "dates", "document_number", "effective_on",
            "end_page", "full_text_xml_url", "html_url", "publication_date",
            "regulation_id_numbers", "start_page", "type", "volume"]
        }, doseq=True)
    connection = urlopen(url)
    results = json.load(connection)
    connection.close()

    notices = []
    for result in results['results']:
        notices.append(build_notice(cfr_title, cfr_part, result))
    return notices

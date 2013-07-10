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
        "order": "oldest"
        })
    connection = urlopen(url)
    results = json.loads(connection.read())
    connection.close()

    notices = []
    for url in [r['html_url'] for r in results['results']]:
        notice_xml = fetch_notice_xml(url)
        notice_xml = etree.fromstring(notice_xml)
        notices.append(build_notice(notice_xml))
    return notices

def fetch_notice_xml(html_url):
    """Unfortunately, the API doesn't link directly to the XML. We therefore
    fetch the HTML and scrape it to find the correct XML"""
    connection = urlopen(html_url)
    html_str = connection.read()
    connection.close()
    #   This is fragile, but will work for now
    json_start = html_str.find('{"formats"')
    json_end = html_str.find(";", json_start)
    dev_formats = json.loads(html_str[json_start:json_end])
    
    xml_url = None
    for fmt in dev_formats['formats']:
        if fmt['type'].lower() == 'xml':
            xml_url = FR_BASE + fmt['url']

    connection = urlopen(xml_url)
    xml_str = connection.read()
    connection.close()
    return xml_str

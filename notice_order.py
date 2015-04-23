# @todo - this should be combined with build_from.py
import argparse

from regparser.builder import notices_for_cfr_part

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notice Orderer")
    parser.add_argument('cfr_title', help='CFR_TITLE')
    parser.add_argument('cfr_part', help='CFR_PART')
    parser.add_argument('--include-notices-without-changes', const=True,
                        default=False, action='store_const',
                        help=('Include notices which do not change the '
                              'regulation (default: false)'))
    args = parser.parse_args()

    notices_by_date = notices_for_cfr_part(args.cfr_title, args.cfr_part)
    for date in sorted(notices_by_date.keys()):
        print(date)
        for notice in notices_by_date[date]:
            if 'changes' in notice or args.include_notices_without_changes:
                print("\t" + notice['document_number'])

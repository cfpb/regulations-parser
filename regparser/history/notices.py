def applicable(notices, doc_number):
    """Given a list of notices and a specific notice number, determine which
    notices in the list are relevant to that doc number."""

    final_notice = [n for n in notices if n['document_number'] == doc_number]
    #   We need the notice for that doc_number
    if not final_notice:
        return []
    final_notice = final_notice[0]

    include = [final_notice]
    #   @todo: this doesn't take into account proposals as final_notice, nor
    #   does it include proposals in the list
    for notice in [n for n in notices if 'effective_on' in n]:
        if notice['effective_on'] < final_notice['effective_on'] or (
           notice['effective_on'] == final_notice['effective_on']
           and notice['publication_date'] < final_notice['publication_date']):
            include.append(notice)
    return include

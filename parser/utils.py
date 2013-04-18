def roman_nums():
    """Generator for roman numerals."""
    mapping = [ 
            (   1, 'i'), (  4, 'iv'), (  5, 'v'), (  9, 'ix'),
            (  10, 'x'), ( 40, 'xl'), ( 50, 'l'), ( 90, 'xc'),
            ( 100, 'c'), (400, 'cd'), (500, 'd'), (900, 'cm'),
            (1000, 'm')
            ]
    i = 1
    while True:
        next_str = ''
        remaining_int = i
        remaining_mapping = list(mapping)
        while remaining_mapping:
            (amount, chars) = remaining_mapping.pop()
            while remaining_int >= amount:
                next_str += chars
                remaining_int -= amount
        yield next_str
        i += 1

def title_body(text):
    """Split text into its first line (the title) and the rest of the text."""
    newline = text.find("\n")
    if newline < 0:
        return text, ""
    return text[:newline], text[newline:]

def flatten(list_of_lists):
    """List[List[X]] -> List[X]"""
    return sum(list_of_lists, [])

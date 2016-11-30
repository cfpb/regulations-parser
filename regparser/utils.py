from random import choice


def roman_nums():
    """Generator for roman numerals."""
    mapping = [
        (1, 'i'), (4, 'iv'), (5, 'v'), (9, 'ix'),
        (10, 'x'), (40, 'xl'), (50, 'l'), (90, 'xc'),
        (100, 'c'), (400, 'cd'), (500, 'd'), (900, 'cm'),
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

letters = [chr(i) for i in range(97, 97 + 26)]
ucase_letters = [chr(i) for i in range(97, 97 + 26)]


def random_letters(length):

    result = ''
    for i in range(length):
        result += choice(letters)
    return result


def set_of_random_letters(num_items, length):

    result = set()
    while len(result) < num_items:
        candidate = random_letters(length)
        result.add(candidate)

    return result


def interpolate_string(text, offsets, values):
    result = ''.encode('utf-8')
    current_pos = 0
    for i, offset in enumerate(offsets):
        start = offset[0]
        end = offset[1]
        fragment = text[current_pos:start].encode('utf-8')
        current_pos = end
        result = (result.decode('utf-8') +
                  fragment.decode('utf-8') +
                  values[i].decode('utf-8')).encode('utf-8')
    result = (result.encode('utf-8') +
              text[current_pos:].encode('utf-8')).decode('utf-8')
    return result

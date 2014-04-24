"""Namespace for collecting the various types of markers"""

import itertools
import string

from regparser.utils import roman_nums


lower = string.ascii_lowercase
upper = string.ascii_uppercase
ints = tuple(str(i) for i in range(1, 51))
roman = tuple(itertools.islice(roman_nums(), 0, 50))
em_ints = tuple('<E T="03">' + i + '</E>' for i in ints)
em_roman = tuple('<E T="03">' + i + '</E>' for i in roman)
stars = ('STARS', '* * *')      # Latter might be inline

types = [lower, upper, ints, roman, em_ints, em_roman, stars]

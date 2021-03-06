# -*- coding: utf-8 -*-
"""usfm2osis.sort

Copyright 2012-2015 by Christopher C. Little

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

The full text of the GNU General Public License is available at:
<http://www.gnu.org/licenses/gpl-3.0.txt>.
"""

from __future__ import unicode_literals
from .bookdata import CANONICAL_ORDER, USFM_NUMERIC_ORDER, FILENAME_TO_OSIS


# BEGIN PSF-licensed segment
# keynat from:
# http://code.activestate.com/recipes/285264-natural-string-sorting/
def key_natural(string):
    """A natural sort helper function for sort() and sorted() without using
    regular expressions or exceptions.

    >>> items = ('Z', 'a', '10th', '1st', '9')
    >>> sorted(items)
    ['10th', '1st', '9', 'Z', 'a']
    >>> sorted(items, key=keynat)
    ['1st', '9', '10th', 'a', 'Z']
    """
    item = type(1)
    sorted_list = []
    for char in string:
        if char.isdigit():
            digit = int(char)
            if sorted_list and type(sorted_list[-1]) == item:
                sorted_list[-1] = sorted_list[-1] * 10 + digit
            else:
                sorted_list.append(digit)
        else:
            sorted_list.append(char.lower())
    return sorted_list
# END PSF-licensed segment


def key_canon(filename):
    """Sort helper function that orders according to canon position (defined in
    canonicalOrder list), returning canonical position or infinity if not in
    the list.
    """
    if filename in FILENAME_TO_OSIS:
        return CANONICAL_ORDER.index(FILENAME_TO_OSIS[filename])
    return float('inf')


def key_usfm(filename):
    """Sort helper function that orders according to USFM book number (defined
    in usfmNumericOrder list), returning USFM book number or infinity if not in
    the list.
    """
    if filename in FILENAME_TO_OSIS:
        return USFM_NUMERIC_ORDER.index(FILENAME_TO_OSIS[filename])
    return float('inf')


def key_supplied(dummy_val):
    """Sort helper function that keeps the items in the order in which they
    were supplied (i.e. it doesn't sort at all), returning the number of times
    the function has been called.
    """
    if not hasattr(key_supplied, "counter"):
        key_supplied.counter = 0
    key_supplied.counter += 1
    return key_supplied.counter

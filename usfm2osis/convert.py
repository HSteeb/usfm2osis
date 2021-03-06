# -*- coding: utf-8 -*-
"""usfm2osis.convert

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
import re
import codecs
from encodings.aliases import aliases
from .bookdata import SPECIAL_BOOKS, PERIPHERALS, INTRO_PERIPHERALS, BOOK_DICT
from .util import verbose_print
from ._compat import _unichr


def ConvertToOSIS(sFile, relaxed_conformance=False, encoding='', debug=False,
                  verbose=False):
    """Open a USFM file and return a string consisting of its OSIS equivalent.

    Keyword arguments:
    sFile -- Path to the USFM file to be converted
    """
    verbose_print(('Processing: ' + sFile), verbose)

    def cvt_preprocess(osis, relaxed_conformance):
        """Perform preprocessing on a USFM document, returning the processed
        text as a string.
        Removes excess spaces & CRs and escapes XML entities.

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.

        """
        # lines should never start with non-tags
        osis = re.sub('\n\s*([^\\\s])', r' \1', osis)  # TODO: test this
        # convert CR to LF
        osis = osis.replace('\r', '\n')
        # lines should never end with whitespace (other than \n)
        osis = re.sub('\s+\n', '\n', osis)
        # replace with XML entities, as necessary
        osis = osis.replace('&', '&amp;')
        osis = osis.replace('<', '&lt;')
        osis = osis.replace('>', '&gt;')

        # osis = re.sub('\n' + r'(\\[^\s]+\b\*)', r' \1', osis)

        return osis

    def cvt_relaxed_conformance_remaps(osis, relaxed_conformance):
        """Perform preprocessing on a USFM document, returning the processed
        text as a string.
        Remaps certain deprecated USFM tags to recommended alternatives.

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        if not relaxed_conformance:
            return osis

        # \tr#: DEP: map to \tr
        osis = re.sub(r'\\tr\d\b', r'\\tr', osis)

        # remapped 2.0 periphs
        # \pub
        osis = re.sub(r'\\pub\b\s', '\\periph Publication Data\n', osis)
        # \toc : \periph Table of Contents
        osis = re.sub(r'\\toc\b\s', '\\periph Table of Contents\n', osis)
        # \pref
        osis = re.sub(r'\\pref\b\s', '\\periph Preface\n', osis)
        # \maps
        osis = re.sub(r'\\maps\b\s', '\\periph Map Index\n', osis)
        # \cov
        osis = re.sub(r'\\cov\b\s', '\\periph Cover\n', osis)
        # \spine
        osis = re.sub(r'\\spine\b\s', '\\periph Spine\n', osis)
        # \pubinfo
        osis = re.sub(r'\\pubinfo\b\s', '\\periph Publication Information\n',
                      osis)

        # \intro
        osis = re.sub(r'\\intro\b\s', '\\id INT\n', osis)
        # \conc
        osis = re.sub(r'\\conc\b\s', '\\id CNC\n', osis)
        # \glo
        osis = re.sub(r'\\glo\b\s', '\\id GLO\n', osis)
        # \idx
        osis = re.sub(r'\\idx\b\s', '\\id TDX\n', osis)

        return osis

    def cvt_identification(osis, relaxed_conformance):
        """Converts USFM **Identification** tags to OSIS, returning the
        processed text as a string.

        Supported tags: \id, \ide, \sts, \rem, \h, \toc1, \toc2, \toc3

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \id_<CODE>_(Name of file, Book name, Language, Last edited, Date,
        #             etc.)
        osis = re.sub(r'\\id\s+([A-Z0-9]{3})\b\s*([^\\' + '\n]*?)\n' +
                      r'(.*)(?=\\id|$)',
                      lambda m: '\uFDD0<div type="book" osisID="' +
                      BOOK_DICT[m.group(1)] + '">\n' +
                      (('<!-- id comment - ' + m.group(2) + ' -->\n') if
                       m.group(2) else '') + m.group(3) +
                      '</div type="book">\uFDD0\n', osis, flags=re.DOTALL)

        # \ide_<ENCODING>
        # delete, since this was handled above
        osis = re.sub(r'\\ide\b.*' + '\n', '', osis)
        # \sts_<STATUS CODE>
        osis = re.sub(r'\\sts\b\s+(.+)\s*' + '\n',
                      r'<milestone type="x-usfm-sts" n="\1"/>' + '\n', osis)

        # \rem_text...
        osis = re.sub(r'\\rem\b\s+(.+)', r'<!-- rem - \1 -->', osis)

        # \restore_text...
        if relaxed_conformance:
            osis = re.sub(r'\\restore\b\s+(.+)', r'<!-- restore - \1 -->',
                          osis)

        # \h#_text...
        osis = re.sub(r'\\h\b\s+(.+)\s*' + '\n',
                      r'<title type="runningHead">\1</title>' + '\n', osis)
        osis = re.sub(r'\\h(\d)\b\s+(.+)\s*' + '\n',
                      r'<title type="runningHead" n="\1">\2</title>' + '\n',
                      osis)

        # \toc1_text...
        osis = re.sub(r'\\toc1\b\s+(.+)\s*' + '\n',
                      r'<milestone type="x-usfm-toc1" n="\1"/>' + '\n', osis)

        # \toc2_text...
        osis = re.sub(r'\\toc2\b\s+(.+)\s*' + '\n',
                      r'<milestone type="x-usfm-toc2" n="\1"/>' + '\n', osis)

        # \toc3_text...
        osis = re.sub(r'\\toc3\b\s+(.+)\s*' + '\n',
                      r'<milestone type="x-usfm-toc3" n="\1"/>' + '\n', osis)

        return osis

    def cvt_introductions(osis, relaxed_conformance):
        """Converts USFM **Introduction** tags to OSIS, returning the processed
        text as a string.

        Supported tags: \imt#, \is#, \ip, \ipi, \im, \imi, \ipq, \imq, \ipr,
                        \iq#, \ib, \ili#, \iot, \io#, \ior...\ior*, \iex,
                        \iqt...\iqt*, \imte, \ie

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \imt#_text...
        osis = re.sub(r'\\imt(\d?)\s+(.+)', lambda m: '<title ' +
                      ('level="' + m.group(1) + '" ' if m.group(1) else '') +
                      'type="main" subType="x-introduction">' + m.group(2) +
                      '</title>', osis)

        # \imte#_text...
        osis = re.sub(r'\\imte(\d?)\b\s+(.+)', lambda m: '<title ' +
                      ('level="' + m.group(1) + '" ' if m.group(1) else '') +
                      'type="main" subType="x-introduction-end">' +
                      m.group(2) + '</title>', osis)

        # \is#_text...
        osis = re.sub(r'\\is1?\s+(.+)', lambda m: '\uFDE2<div type="section" subType="x-introduction"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDE2<div type="section" subType="x-introduction">[^\uFDE2]+)'+r'(?!\\c\b)', r'\1'+'</div>\uFDE2\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\is2\s+(.+)', lambda m: '\uFDE3<div type="subSection" subType="x-introduction"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDE3<div type="subSection" subType="x-introduction">[^\uFDE2\uFDE3]+)'+r'(?!\\c\b)', r'\1'+'</div>\uFDE3\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\is3\s+(.+)', lambda m: '\uFDE4<div type="x-subSubSection" subType="x-introduction"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDE4<div type="subSubSection" subType="x-introduction">[^\uFDE2\uFDE3\uFDE4]+)'+r'(?!\\c\b)', r'\1'+'</div>\uFDE4\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\is4\s+(.+)', lambda m: '\uFDE5<div type="x-subSubSubSection" subType="x-introduction"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDE5<div type="subSubSubSection" subType="x-introduction">[^\uFDE2\uFDE3\uFDE4\uFDE5]+)'+r'(?!\\c\b)', r'\1'+'</div>\uFDE5\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\is5\s+(.+)', lambda m: '\uFDE6<div type="x-subSubSubSubSection" subType="x-introduction"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDE6<div type="subSubSubSubSection" subType="x-introduction">[^\uFDE2\uFDE3\uFDE4\uFDE5\uFDE6]+?)'+r'(?!\\c\b)', r'\1'+'</div>\uFDE6\n', osis, flags=re.DOTALL)

        # \ip_text...
        osis = re.sub(r'\\ip\s+(.*?)(?=(\\(i?m|i?p|lit|cls|tr|io|iq|i?li|iex?|s|c)\b|<(/?div|p|closer)\b))', lambda m: '\uFDD3<p subType="x-introduction">\n' + m.group(1) + '\uFDD3</p>\n', osis, flags=re.DOTALL)

        # \ipi_text...
        # \im_text...
        # \imi_text...
        # \ipq_text...
        # \imq_text...
        # \ipr_text...
        p_type = {'ipi': 'x-indented', 'im': 'x-noindent',
                  'imi': 'x-noindent-indented', 'ipq': 'x-quote',
                  'imq': 'x-noindent-quote', 'ipr': 'x-right'}
        osis = re.sub(r'\\(ipi|im|ipq|imq|ipr)\s+(.*?)(?=(\\(i?m|i?p|lit|cls|tr|io[t\d]?|ipi|iq|i?li|iex?|s|c)\b|<(/?div|p|closer)\b))', lambda m: '\uFDD3<p type="' + p_type[m.group(1)] + '" subType="x-introduction">\n' + m.group(2) + '\uFDD3</p>\n', osis, flags=re.DOTALL)

        # \iq#_text...
        osis = re.sub(r'\\iq\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' +
                      r']|\\(iq\d?|fig|q\d?|b)\b|<title\b))',
                      r'<l level="1" subType="x-introduction">\1</l>',
                      osis, flags=re.DOTALL)
        osis = re.sub(r'\\iq(\d)\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' +
                      r']|\\(iq\d?|fig|q\d?|b)\b|<title\b))',
                      r'<l level="\1" subType="x-introduction">\2</l>',
                      osis, flags=re.DOTALL)

        # \ib
        osis = re.sub(r'\\ib\b\s?', '<lb type="x-p"/>', osis)
        osis = osis.replace('\n</l>', '</l>\n')
        # osis = re.sub('(<l [^\uFDD0\uFDD1\uFDD3\uFDD4]+</l>)', r'<lg>\1</lg>', osis, flags=re.DOTALL)
        # osis = re.sub('(<lg>.+?</lg>)', lambda m: m.group(1).replace('<lb type="x-p"/>', '</lg><lg>'), osis, flags=re.DOTALL) # re-handle \b that occurs within <lg>

        # \ili#_text...
        osis = re.sub(r'\\ili\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' + r']|\\(ili\d?|c|p|io[t\d]?|iex?)\b|<(lb|title|item|\?div)\b))', '<item type="x-indent-1" subType="x-introduction">\uFDE0' + r'\1' + '\uFDE0</item>', osis, flags=re.DOTALL)
        osis = re.sub(r'\\ili(\d)\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' + r']|\\(ili\d?|c|p|io[t\d]?|iex?)\b|<(lb|title|item|\?div)\b))', r'<item type="x-indent-\1" subType="x-introduction">'+'\uFDE0' + r'\2' + '\uFDE0</item>', osis, flags=re.DOTALL)
        osis = osis.replace('\n</item>', '</item>\n')
        osis = re.sub('(<item [^\uFDD0\uFDD1\uFDD3\uFDD4]+</item>)',
                      '\uFDD3<list>' + r'\1' + '</list>\uFDD3',
                      osis, flags=re.DOTALL)

        # \iot_text...
        # \io#_text...(references range)
        osis = re.sub(r'\\io\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' + r']|\\(io[t\d]?|iex?|c|p)\b|<(lb|title|item|\?div)\b))', '<item type="x-indent-1" subType="x-introduction">\uFDE1' + r'\1' + '\uFDE1</item>', osis, flags=re.DOTALL)
        osis = re.sub(r'\\io(\d)\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' + r']|\\(io[t\d]?|iex?|c|p)\b|<(lb|title|item|\?div)\b))', r'<item type="x-indent-\1" subType="x-introduction">'+'\uFDE1' + r'\2' + '\uFDE1</item>', osis, flags=re.DOTALL)
        osis = re.sub(r'\\iot\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' +
                      r']|\\(io[t\d]?|iex?|c|p)\b|<(lb|title|item|\?div)\b))',
                      '<item type="head">\uFDE1' + r'\1' +
                      '\uFDE1</item type="head">', osis, flags=re.DOTALL)
        osis = osis.replace('\n</item>', '</item>\n')
        osis = re.sub('(<item [^\uFDD0\uFDD1\uFDD3\uFDD4\uFDE0]+</item>)',
                      '\uFDD3<div type="outline"><list>' + r'\1' +
                      '</list></div>\uFDD3', osis, flags=re.DOTALL)
        osis = re.sub('item type="head"', 'head', osis)

        # \ior_text...\ior*
        osis = re.sub(r'\\ior\b\s+(.+?)\\ior\*', r'<reference>\1</reference>',
                      osis, flags=re.DOTALL)

        # \iex  # TODO: look for example; I have no idea what this would look like in context
        osis = re.sub(r'\\iex\b\s*(.+?)' +
                      r'?=(\s*(\\c|</div type="book">'+'\uFDD0))',
                      r'<div type="bridge">\1</div>', osis, flags=re.DOTALL)

        # \iqt_text...\iqt*
        osis = re.sub(r'\\iqt\s+(.+?)\\iqt\*',
                      r'<q subType="x-introduction">\1</q>',
                      osis, flags=re.DOTALL)

        # \ie
        osis = re.sub(r'\\ie\b\s*', '<milestone type="x-usfm-ie"/>', osis)

        return osis

    def cvt_titles(osis, relaxed_conformance):
        """Converts USFM **Title, Heading, and Label** tags to OSIS, returning
        the processed text as a string.

        Supported tags: \mt#, \mte#, \ms#, \mr, \s#, \sr, \r, \rq...\rq*, \d,
                        \sp

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \ms#_text...
        osis = re.sub(r'\\ms1?\s+(.+)', lambda m: '\uFDD5<div type="majorSection"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDD5[^\uFDD5\uFDD0]+)', r'\1' + '</div>\uFDD5\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\ms2\s+(.+)', lambda m: '\uFDD6<div type="majorSection" n="2"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDD6[^\uFDD5\uFDD0\uFDD6]+)', r'\1' + '</div>\uFDD6\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\ms3\s+(.+)', lambda m: '\uFDD7<div type="majorSection" n="3"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDD7[^\uFDD5\uFDD0\uFDD6\uFDD7]+)', r'\1' + '</div>\uFDD7\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\ms4\s+(.+)', lambda m: '\uFDD8<div type="majorSection" n="4"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDD8[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8]+)', r'\1' + '</div>\uFDD8\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\ms5\s+(.+)', lambda m: '\uFDD9<div type="majorSection" n="5"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDD9[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8\uFDD9]+)', r'\1' + '</div>\uFDD9\n', osis, flags=re.DOTALL)

        # \mr_text...
        osis = re.sub(r'\\mr\s+(.+)', '\uFDD4<title type="scope"><reference>' + r'\1</reference></title>', osis)

        # \s#_text...
        osis = re.sub(r'\\s1?\s+(.+)', lambda m: '\uFDDA<div type="section"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDDA<div type="section">[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA]+)', r'\1' + '</div>\uFDDA\n', osis, flags=re.DOTALL)
        if relaxed_conformance:
            osis = re.sub(r'\\ss\s+', r'\\s2 ', osis)
            osis = re.sub(r'\\sss\s+', r'\\s3 ', osis)
        osis = re.sub(r'\\s2\s+(.+)', lambda m: '\uFDDB<div type="subSection"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDDB<div type="subSection">[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB]+)', r'\1' + '</div>\uFDDB\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\s3\s+(.+)', lambda m: '\uFDDC<div type="x-subSubSection"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDDC<div type="x-subSubSection">[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC]+)', r'\1' + '</div>\uFDDC\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\s4\s+(.+)', lambda m: '\uFDDD<div type="x-subSubSubSection"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDDD<div type="x-subSubSubSection">[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD]+)', r'\1' + '</div>\uFDDD\n', osis, flags=re.DOTALL)
        osis = re.sub(r'\\s5\s+(.+)', lambda m: '\uFDDE<div type="x-subSubSubSubSection"><title>' + m.group(1) + '</title>', osis)
        osis = re.sub('(\uFDDE<div type="x-subSubSubSubSection">[^\uFDD5\uFDD0\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE]+)', r'\1' + '</div>\uFDDE\n', osis, flags=re.DOTALL)

        # \sr_text...
        osis = re.sub(r'\\sr\s+(.+)', '\uFDD4<title type="scope"><reference>' + r'\1</reference></title>', osis)
        # \r_text...
        osis = re.sub(r'\\r\s+(.+)', '\uFDD4<title type="parallel"><reference type="parallel">' + r'\1</reference></title>', osis)
        # \rq_text...\rq*
        osis = re.sub(r'\\rq\s+(.+?)\\rq\*', r'<reference type="source">\1</reference>', osis, flags=re.DOTALL)

        # \d_text...
        osis = re.sub(r'\\d\s+(.+)', '\uFDD4<title canonical="true" type="psalm">' + r'\1</title>', osis)

        # \sp_text...
        osis = re.sub(r'\\sp\s+(.+)', r'<speaker>\1</speaker>', osis)

        # \mt#_text...
        osis = re.sub(r'\\mt(\d?)\s+(.+)',
                      lambda m: '<title ' + ('level="' + m.group(1) + '" ' if m.group(1) else '') + 'type="main">' + m.group(2) + '</title>',
                      osis)
        # \mte#_text...
        osis = re.sub(r'\\mte(\d?)\s+(.+)',
                      lambda m: '<title ' + ('level="' + m.group(1) + '" ' if m.group(1) else '') + 'type="main" subType="x-end">' + m.group(2) + '</title>',
                      osis)

        return osis

    def cvt_chapters_and_verses(osis, relaxed_conformance):
        """Converts USFM **Chapter and Verse** tags to OSIS, returning the
        processed text as a string.

        Supported tags: \c, \ca...\ca*, \cl, \cp, \cd, \v, \va...\va*,
        \vp...\vp*

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \c_#
        osis = re.sub(r'\\c\s+([^\s]+)\b(.+?)(?=(\\c\s+|</div type="book"))',
                      lambda m: '\uFDD1<chapter osisID="$BOOK$.' + m.group(1) +
                      r'" sID="$BOOK$.' + m.group(1) + '"/>' + m.group(2) +
                      '<chapter eID="$BOOK$.' + m.group(1) + '"/>\uFDD3\n',
                      osis, flags=re.DOTALL)

        # \cp_#
        # \ca_#\ca*
        def replace_chapter_number(matchObject):
            """Regex helper function to replace chapter numbers from \c_# with
            values that appeared in \cp_# and \ca_#\ca*, returing the chapter
            text as a string.

            Keyword arguments:
            matchObject -- a regex match object in which the first element is
            the chapter text
            """
            ctext = matchObject.group(1)
            cp = re.search(r'\\cp\s+(.+?)(?=(\\|\s))', ctext)
            if cp:
                ctext = re.sub(r'\\cp\s+(.+?)(?=(\\|\s))', '', ctext,
                               flags=re.DOTALL)
                cp = cp.group(1)
                ctext = re.sub(r'"\$BOOK\$\.([^"\.]+)"', '"$BOOK$.'+cp+'"',
                               ctext)
            ca = re.search(r'\\ca\s+(.+?)\\ca\*', ctext)
            if ca:
                ctext = re.sub(r'\\ca\s+(.+?)\\ca\*', '',
                               ctext, flags=re.DOTALL)
                ca = ca.group(1)
                ctext = re.sub(r'(osisID="\$BOOK\$\.[^"\.]+)"',
                               r'\1 $BOOK$.' + ca + '"', ctext)
            return ctext
        osis = re.sub(r'(<chapter [^<]+sID[^<]+/>.+?<chapter eID[^>]+/>)',
                      replace_chapter_number, osis, flags=re.DOTALL)

        # \cl_
        osis = re.sub(r'\\cl\s+(.+)', '\uFDD4<title>' + r'\1</title>', osis)

        # \cd_#   <--This # seems to be an error
        osis = re.sub(r'\\cd\b\s+(.+)', '\uFDD4<title type="x-description">' +
                      r'\1</title>', osis)

        # \v_#
        osis = re.sub(r'\\v\s+([^\s]+)\b\s*(.+?)(?=(\\v\s+|</div type="book"|<chapter eID))', lambda m: '\uFDD2<verse osisID="$BOOK$.$CHAP$.' + m.group(1) + '" sID="$BOOK$.$CHAP$.' + m.group(1) + '"/>' + m.group(2) + '<verse eID="$BOOK$.$CHAP$.' + m.group(1) + '"/>\uFDD2\n', osis, flags=re.DOTALL)

        # \vp_#\vp*
        # \va_#\va*
        def replace_verse_number(matchObject):
            """Regex helper function to replace verse numbers from \v_# with
            values that appeared in \vp_#\vp* and \va_#\va*, returing the verse
            text as a string.

            Keyword arguments:
            matchObject -- a regex match object in which the first element is
            the verse text
            """
            vtext = matchObject.group(1)
            vp = re.search(r'\\vp\s+(.+?)\\vp\*', vtext)
            if vp:
                vtext = re.sub(r'\\vp\s+(.+?)\\vp\*', '', vtext,
                               flags=re.DOTALL)
                vp = vp.group(1)
                vtext = re.sub(r'"\$BOOK\$\.\$CHAP\$\.([^"\.]+)"',
                               '"$BOOK$.$CHAP$.' + vp + '"', vtext)
            va = re.search(r'\\va\s+(.+?)\\va\*', vtext)
            if va:
                vtext = re.sub(r'\\va\s+(.+?)\\va\*', '', vtext,
                               flags=re.DOTALL)
                va = va.group(1)
                vtext = re.sub(r'(osisID="\$BOOK\$\.\$CHAP\$\.[^"\.]+)"',
                               r'\1 $BOOK$.$CHAP$.' + va + '"', vtext)
            return vtext

        osis = re.sub(r'(<verse [^<]+sID[^<]+/>.+?<verse eID[^>]+/>)',
                      replace_verse_number, osis, flags=re.DOTALL)

        return osis

    def cvt_paragraphs(osis, relaxed_conformance):
        """Converts USFM **Paragraph** tags to OSIS, returning the processed
        text as a string.

        Supported tags: \p, \m, \pmo, \pm, \pmc, \pmr, \pi#, \mi, \nb, \cls,
                        \li#, \pc, \pr, \ph#, \b

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        paragraphregex = 'pc|pr|m|pmo|pm|pmc|pmr|pi|pi1|pi2|pi3|pi4|pi5|mi|nb'
        if relaxed_conformance:
            paragraphregex += '|phi|ps|psi|p1|p2|p3|p4|p5'

        # \p(_text...)
        osis = re.sub(r'\\p\s+(.*?)(?=(\\(i?m|i?p|lit|cls|tr|p|' +
                      paragraphregex+r')\b|<chapter eID|<(/?div|p|closer)\b))',
                      lambda m: '\uFDD3<p>\n' + m.group(1) + '\uFDD3</p>\n',
                      osis, flags=re.DOTALL)

        # \pc(_text...)
        # \pr(_text...)
        # \m(_text...)
        # \pmo(_text...)
        # \pm(_text...)
        # \pmc(_text...)
        # \pmr_text...  # deprecated: map to same as \pr
        # \pi#(_Sample text...)
        # \mi(_text...)
        # \nb
        # \phi # deprecated
        # \ps # deprecated
        # \psi # deprecated
        # \p# # deprecated
        p_type = {'pc': 'x-center', 'pr': 'x-right', 'm': 'x-noindent',
                  'pmo': 'x-embedded-opening', 'pm': 'x-embedded',
                  'pmc': 'x-embedded-closing', 'pmr': 'x-right',
                  'pi': 'x-indented-1', 'pi1': 'x-indented-1',
                  'pi2': 'x-indented-2', 'pi3': 'x-indented-3',
                  'pi4': 'x-indented-4', 'pi5': 'x-indented-5',
                  'mi': 'x-noindent-indented', 'nb': 'x-nobreak',
                  'phi': 'x-indented-hanging', 'ps': 'x-nobreakNext',
                  'psi': 'x-nobreakNext-indented', 'p1': 'x-level-1',
                  'p2': 'x-level-2', 'p3': 'x-level-3', 'p4': 'x-level-4',
                  'p5': 'x-level-5'}
        osis = re.sub(r'\\(' + paragraphregex +
                      r')\s+(.*?)(?=(\\(i?m|i?p|lit|cls|tr|' + paragraphregex +
                      r')\b|<chapter eID|<(/?div|p|closer)\b))',
                      lambda m: '\uFDD3<p type="' + p_type[m.group(1)] +
                      '">\n' + m.group(2) + '\uFDD3</p>\n',
                      osis, flags=re.DOTALL)

        # \cls_text...
        osis = re.sub(r'\\m\s+(.+?)(?=(\\(i?m|i?p|lit|cls|tr)\b|<chapter eID|<(/?div|p|closer)\b))', lambda m: '\uFDD3<closer>' + m.group(1) + '\uFDD3</closer>\n', osis, flags=re.DOTALL)

        # \ph#(_text...)
        # \li#(_text...)
        osis = re.sub(r'\\ph\b\s*', r'\\li ', osis)
        osis = re.sub(r'\\ph(\d)\b\s*', r'\\li\1 ', osis)
        osis = re.sub(r'\\li\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4\uFDE0\uFDE1\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE' + r']|\\li\d?\b|<(lb|title|item|/?div|/?chapter)\b))', r'<item type="x-indent-1">\1</item>', osis, flags=re.DOTALL)
        osis = re.sub(r'\\li(\d)\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4\uFDE0\uFDE1\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE' + r']|\\li\d?\b|<(lb|title|item|/?div|/?chapter)\b))', r'<item type="x-indent-\1">\2</item>', osis, flags=re.DOTALL)
        osis = osis.replace('\n</item>', '</item>\n')
        osis = re.sub('(<item [^\uFDD0\uFDD1\uFDD3\uFDD4\uFDE0\uFDE1\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE]+</item>)', '\uFDD3<list>' + r'\1' + '</list>\uFDD3', osis, flags=re.DOTALL)

        # \b
        osis = re.sub(r'\\b\b\s?', '<lb type="x-p"/>', osis)

        return osis

    def cvt_poetry(osis, relaxed_conformance):
        """Converts USFM **Poetry** tags to OSIS, returning the processed text
        as a string.

        Supported tags: \q#, \qr, \qc, \qs...\qs*, \qa, \qac...\qac*, \qm#, \b

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """

        # \qa_text...
        osis = re.sub(r'\\qa\s+(.+)', '\uFDD4<title type="acrostic">' +
                      r'\1</title>', osis)

        # \qac_text...\qac*
        osis = re.sub(r'\\qac\s+(.+?)\\qac\*', r'<hi type="acrostic">\1</hi>',
                      osis, flags=re.DOTALL)

        # \qs_(Selah)\qs*
        osis = re.sub(r'\\qs\b\s(.+?)\\qs\*', r'<l type="selah">\1</l>',
                      osis, flags=re.DOTALL)

        # \q#(_text...)
        osis = re.sub(r'\\q\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE' + r']|\\(q\d?|fig)\b|<(l|lb|title|list|/?div)\b))', r'<l level="1">\1</l>', osis, flags=re.DOTALL)
        osis = re.sub(r'\\q(\d)\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE' + r']|\\(q\d?|fig)\b|<(l|lb|title|list|/?div)\b))', r'<l level="\1">\2</l>', osis, flags=re.DOTALL)

        # \qr_text...
        # \qc_text...
        # \qm#(_text...)
        qType = {'qr': 'x-right', 'qc': 'x-center',
                 'qm': 'x-embedded" level="1', 'qm1': 'x-embedded" level="1',
                 'qm2': 'x-embedded" level="2', 'qm3': 'x-embedded" level="3',
                 'qm4': 'x-embedded" level="4', 'qm5': 'x-embedded" level="5'}
        osis = re.sub(r'\\(qr|qc|qm\d)\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE' + r']|\\(q\d?|fig)\b|<(l|lb|title|list|/?div)\b))', lambda m: '<l type="' + qType[m.group(1)] + '">' + m.group(2) + '</l>', osis, flags=re.DOTALL)

        osis = osis.replace('\n</l>', '</l>\n')
        osis = re.sub('(<l [^\uFDD0\uFDD1\uFDD3\uFDD4\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE]+</l>)', r'<lg>\1</lg>', osis, flags=re.DOTALL)

        # \b
        osis = re.sub('(<lg>.+?</lg>)', lambda m: m.group(1).replace('<lb type="x-p"/>', '</lg><lg>'), osis, flags=re.DOTALL)  # re-handle \b that occurs within <lg>

        return osis

    def cvt_tables(osis, relaxed_conformance):
        """Converts USFM **Table** tags to OSIS, returning the processed text as
        a string.

        Supported tags: \tr, \th#, \thr#, \tc#, \tcr#

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \tr_
        osis = re.sub(r'\\tr\b\s*(.*?)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' +
                      r']|\\tr\s|<(lb|title)\b))', r'<row>\1</row>',
                      osis, flags=re.DOTALL)

        # \th#_text...
        # \thr#_text...
        # \tc#_text...
        # \tcr#_text...
        t_type = {'th': ' role="label"', 'thr': ' role="label" type="x-right"',
                  'tc': '', 'tcr': ' type="x-right"'}
        osis = re.sub(r'\\(thr?|tcr?)\d*\b\s*(.*?)(?=(\\t[hc]|</row))',
                      lambda m: '<cell' + t_type[m.group(1)] + '>' +
                      m.group(2) + '</cell>', osis, flags=re.DOTALL)

        osis = re.sub(r'(<row>.*?</row>)(?=([' + '\uFDD0\uFDD1\uFDD3\uFDD4' +
                      r']|\\tr\s|<(lb|title)\b))', r'<table>\1</table>',
                      osis, flags=re.DOTALL)

        return osis

    def process_note(note):
        """Convert note-internal USFM tags to OSIS, returning the note as a
        string.

        Keyword arguments:
        note -- The note as a string.
        """
        note = note.replace('\n', ' ')

        # \fdc_refs...\fdc*
        note = re.sub(r'\\fdc\b\s(.+?)\\fdc\b\*',
                      r'<seg editions="dc">\1</seg>', note)

        # \fq_
        note = re.sub(r'\\fq\b\s(.+?)(?=(\\f|' + '\uFDDF))',
                      '\uFDDF' + r'<catchWord>\1</catchWord>', note)

        # \fqa_
        note = re.sub(r'\\fqa\b\s(.+?)(?=(\\f|' + '\uFDDF))',
                      '\uFDDF' + r'<rdg type="alternate">\1</rdg>', note)

        # \ft_
        note = re.sub(r'\\ft\s', '', note)

        # \fr_##SEP##
        note = re.sub(r'\\fr\b\s(.+?)(?=(\\f|' + '\uFDDF))',
                      '\uFDDF' + r'<reference type="annotateRef">\1</reference>',
                      note)

        # \fk_
        note = re.sub(r'\\fk\b\s(.+?)(?=(\\f|' + '\uFDDF))',
                      '\uFDDF' + r'<catchWord>\1</catchWord>', note)

        # \fl_
        note = re.sub(r'\\fl\b\s(.+?)(?=(\\f|' + '\uFDDF))',
                      '\uFDDF' + r'<label>\1</label>', note)

        # \fp_
        note = re.sub(r'\\fp\b\s(.+?)(?=(\\fp|$))', r'<p>\1</p>', note)
        note = re.sub(r'(<note\b[^>]*?>)(.*?)<p>', r'\1<p>\2</p><p>', note)

        # \fv_
        note = re.sub(r'\\fv\b\s(.+?)(?=(\\f|' + '\uFDDF))',
                      '\uFDDF' + r'<hi type="super">\1</hi>', note)

        # \fq*,\fqa*,\ft*,\fr*,\fk*,\fl*,\fp*,\fv*
        note = re.sub(r'\\f(q|qa|t|r|k|l|p|v)\*', '', note)

        note = note.replace('\uFDDF', '')
        return note

    def cvt_footnotes(osis, relaxed_conformance):
        """Converts USFM **Footnote** tags to OSIS, returning the processed
        text as a string.

        Supported tags: \f...\f*, \fe...\fe*, \fr, \fk, \fq, \fqa, \fl, \fp,
                        \fv, \ft, \fdc...\fdc*, \fm...\fm*

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \f_+_...\f*
        osis = re.sub(r'\\f\s+([^\s\\]+)?\s*(.+?)\s*\\f\*',
                      lambda m: '<note' + ((' n=""') if
                                           (m.group(1) == '-') else
                                           ('' if (m.group(1) == '+') else
                                            (' n="' + m.group(1) + '"'))) +
                      ' placement="foot">' + m.group(2) + '\uFDDF</note>',
                      osis, flags=re.DOTALL)

        # \fe_+_...\fe*
        osis = re.sub(r'\\fe\s+([^\s\\]+?)\s*(.+?)\s*\\fe\*',
                      lambda m: '<note' + ((' n=""') if
                                           (m.group(1) == '-') else
                                           ('' if (m.group(1) == '+') else
                                            (' n="' + m.group(1) + '"'))) +
                      ' placement="end">' + m.group(2) + '\uFDDF</note>',
                      osis, flags=re.DOTALL)

        osis = re.sub(r'(<note\b[^>]*?>.*?</note>)',
                      lambda m: process_note(m.group(1)), osis, flags=re.DOTALL)

        # \fm_...\fm*
        osis = re.sub(r'\\fm\b\s(.+?)\\fm\*', r'<hi type="super">\1</hi>',
                      osis)

        return osis

    def process_xref(note):
        """Convert cross-reference note-internal USFM tags to OSIS, returning
        the cross-reference note as a string.

        Keyword arguments:
        note -- The cross-reference note as a string.
        """
        note = note.replace('\n', ' ')

        # \xot_refs...\xot*
        note = re.sub(r'\\xot\b\s(.+?)\\xot\b\*',
                      '\uFDDF' + r'<seg editions="ot">\1</seg>', note)

        # \xnt_refs...\xnt*
        note = re.sub(r'\\xnt\b\s(.+?)\\xnt\b\*',
                      '\uFDDF' + r'<seg editions="nt">\1</seg>', note)

        # \xdc_refs...\xdc*
        note = re.sub(r'\\xdc\b\s(.+?)\\xdc\b\*',
                      '\uFDDF' + r'<seg editions="dc">\1</seg>', note)

        # \xq_
        note = re.sub(r'\\xq\b\s(.+?)(?=(\\x|' + '\uFDDF))',
                      '\uFDDF' + r'<catchWord>\1</catchWord>', note)

        # \xo_##SEP##
        note = re.sub(r'\\xo\b\s(.+?)(?=(\\x|' + '\uFDDF))',
                      '\uFDDF' + r'<reference type="annotateRef">\1</reference>', note)

        # \xk_
        note = re.sub(r'\\xk\b\s(.+?)(?=(\\x|' + '\uFDDF))',
                      '\uFDDF' + r'<catchWord>\1</catchWord>', note)

        # \xt_  # This isn't guaranteed to be *the* reference, but it's a good guess.
        note = re.sub(r'\\xt\b\s(.+?)(?=(\\x|' + '\uFDDF))',
                      '\uFDDF' + r'<reference>\1</reference>', note)

        if relaxed_conformance:
            # TODO: move this to a concorance/index-specific section?
            # \xtSee..\xtSee*: Concordance and Names Index markup for an
            #                  alternate entry target reference.
            note = re.sub(r'\\xtSee\b\s(.+?)\\xtSee\b\*',
                          '\uFDDF' +
                          r'<reference osisRef="\1">See: \1</reference>', note)
            # \xtSeeAlso...\xtSeeAlso: Concordance and Names Index markup for
            #                          an additional entry target reference.
            note = re.sub(r'\\xtSeeAlso\b\s(.+?)\\xtSeeAlso\b\*',
                          '\uFDDF' +
                          r'<reference osisRef="\1">See also: \1</reference>',
                          note)

        # \xq*,\xt*,\xo*,\xk*
        note = re.sub(r'\\x(q|t|o|k)\*', '', note)

        note = note.replace('\uFDDF', '')
        return note

    def cvt_cross_references(osis, relaxed_conformance):
        """Converts USFM **Cross Reference** tags to OSIS, returning the
        processed text as a string.

        Supported tags: \\x...\\x*, \\xo, \\xk, \\xq, \\xt, \\xot...\\xot*,
                        \\xnt...\\xnt*, \\xdc...\\xdc*

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \x_+_...\x*
        osis = re.sub(r'\\x\s+([^\s]+?)\s+(.+?)\s*\\x\*',
                      lambda m: '<note' + ((' n=""') if
                                           (m.group(1) == '-') else
                                           ('' if (m.group(1) == '+') else
                                            (' n="' + m.group(1) + '"'))) +
                      ' type="crossReference">' + m.group(2) + '\uFDDF</note>',
                      osis, flags=re.DOTALL)

        osis = re.sub(r'(<note [^>]*?type="crossReference"[^>]*>.*?</note>)',
                      lambda m: process_xref(m.group(1)), osis, flags=re.DOTALL)

        return osis

    # -- Special Text and Character Styles
    def cvt_special_text(osis, relaxed_conformance):
        """Converts USFM **Special Text** tags to OSIS, returning the processed
        text as a string.

        Supported tags: \add...\add*, \bk...\bk*, \dc...\dc*, \k...\k*, \lit,
                        \nd...\nd*, \ord...\ord*, \pn...\pn*, \qt...\qt*,
                        \sig...\sig*, \sls...\sls*, \tl...\tl*, \wj...\wj*

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \add_...\add*
        osis = re.sub(r'\\add\s+(.+?)\\add\*',
                      r'<transChange type="added">\1</transChange>',
                      osis, flags=re.DOTALL)

        # \wj_...\wj*
        osis = re.sub(r'\\wj\s+(.+?)\\wj\*',
                      r'<q who="Jesus" marker="">\1</q>',
                      osis, flags=re.DOTALL)

        # \nd_...\nd*
        osis = re.sub(r'\\nd\s+(.+?)\\nd\*',
                      r'<divineName>\1</divineName>',
                      osis, flags=re.DOTALL)

        # \pn_...\pn*
        osis = re.sub(r'\\pn\s+(.+?)\\pn\*',
                      r'<name>\1</name>',
                      osis, flags=re.DOTALL)

        # \qt_...\qt* # TODO:should this be <q>?
        osis = re.sub(r'\\qt\s+(.+?)\\qt\*',
                      r'<seg type="otPassage">\1</seg>',
                      osis, flags=re.DOTALL)

        # \sig_...\sig*
        osis = re.sub(r'\\sig\s+(.+?)\\sig\*',
                      r'<signed>\1</signed>',
                      osis, flags=re.DOTALL)

        # \ord_...\ord*
        osis = re.sub(r'\\ord\s+(.+?)\\ord\*',      # semantic incongruity:
                      r'<hi type="super">\1</hi>',  # (ordinal -> superscript)
                      osis, flags=re.DOTALL)

        # \tl_...\tl*
        osis = re.sub(r'\\tl\s+(.+?)\\tl\*',
                      r'<foreign>\1</foreign>',
                      osis, flags=re.DOTALL)

        # \bk_...\bk*
        osis = re.sub(r'\\bk\s+(.+?)\\bk\*',
                      r'<name type="x-workTitle">\1</name>',
                      osis, flags=re.DOTALL)

        # \k_...\k*
        osis = re.sub(r'\\k\s+(.+?)\\k\*',
                      r'<seg type="keyword">\1</seg>',
                      osis, flags=re.DOTALL)

        # \lit
        osis = re.sub(r'\\lit\s+(.*?)(?=(\\(i?m|i?p|nb|lit|cls|tr)\b|<(chapter eID|/?div|p|closer)\b))', lambda m: '\uFDD3<p type="x-liturgical">\n' + m.group(1) + '\uFDD3</p>\n', osis, flags=re.DOTALL)

        # \dc_...\dc*
        # TODO: Find an example---should this really be transChange?
        osis = re.sub(r'\\dc\b\s*(.+?)\\dc\*',
                      r'<transChange type="added" editions="dc">\1</transChange>',
                      osis, flags=re.DOTALL)

        # \sls_...\sls*
        # TODO: find a better mapping than <foreign>?
        osis = re.sub(r'\\sls\b\s*(.+?)\\sls\*',
                      r'<foreign>/1</foreign>',
                      osis, flags=re.DOTALL)

        if relaxed_conformance:
            # \addpn...\addpn*
            osis = re.sub(r'\\addpn\s+(.+?)\\addpn\*',
                          r'<hi type="x-dotUnderline">\1</hi>',
                          osis, flags=re.DOTALL)
            # \k# # TODO: unsure of this tag's purpose
            osis = re.sub(r'\\k1\s+(.+?)\\k1\*',
                          r'<seg type="keyword" n="1">\1</seg>',
                          osis, flags=re.DOTALL)
            osis = re.sub(r'\\k2\s+(.+?)\\k2\*',
                          r'<seg type="keyword" n="2">\1</seg>',
                          osis, flags=re.DOTALL)
            osis = re.sub(r'\\k3\s+(.+?)\\k3\*',
                          r'<seg type="keyword" n="3">\1</seg>',
                          osis, flags=re.DOTALL)
            osis = re.sub(r'\\k4\s+(.+?)\\k4\*',
                          r'<seg type="keyword" n="4">\1</seg>',
                          osis, flags=re.DOTALL)
            osis = re.sub(r'\\k5\s+(.+?)\\k5\*',
                          r'<seg type="keyword" n="5">\1</seg>',
                          osis, flags=re.DOTALL)

        return osis

    def cvt_character_styling(osis, relaxed_conformance):
        """Converts USFM **Character Styling** tags to OSIS, returning the
        processed text as a string.

        Supported tags: \em...\em*, \bd...\bd*, \it...\it*, \bdit...\bdit*,
                        \no...\no*, \sc...\sc*

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \em_...\em*
        osis = re.sub(r'\\em\s+(.+?)\\em\*',
                      r'<hi type="emphasis">\1</hi>',
                      osis, flags=re.DOTALL)

        # \bd_...\bd*
        osis = re.sub(r'\\bd\s+(.+?)\\bd\*',
                      r'<hi type="bold">\1</hi>',
                      osis, flags=re.DOTALL)

        # \it_...\it*
        osis = re.sub(r'\\it\s+(.+?)\\it\*',
                      r'<hi type="italic">\1</hi>',
                      osis, flags=re.DOTALL)

        # \bdit_...\bdit*
        osis = re.sub(r'\\bdit\s+(.+?)\\bdit\*',
                      r'<hi type="bold"><hi type="italic">\1</hi></hi>',
                      osis, flags=re.DOTALL)

        # \no_...\no*
        osis = re.sub(r'\\no\s+(.+?)\\no\*',
                      r'<hi type="normal">\1</hi>',
                      osis, flags=re.DOTALL)

        # \sc_...\sc*
        osis = re.sub(r'\\sc\s+(.+?)\\sc\*',
                      r'<hi type="small-caps">\1</hi>',
                      osis, flags=re.DOTALL)

        return osis

    def cvt_spacing_and_breaks(osis, relaxed_conformance):
        """Converts USFM **Spacing and Breaks** tags to OSIS, returning the
        processed text as a string.

        Supported tags: ~, //, \pb

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # ~
        osis = osis.replace('~', '\u00A0')

        # //
        osis = osis.replace('//', '<lb type="x-optional"/>')

        # \pb
        osis = re.sub(r'\\pb\s*',
                      '<milestone type="pb"/>\n',
                      osis, flags=re.DOTALL)

        return osis

    def cvt_special_features(osis, relaxed_conformance):
        """Converts USFM **Special Feature** tags to OSIS, returning the
        processed text as a string.

        Supported tags: \fig...\fig*, \ndx...\ndx*, \pro...\pro*, \w...\w*,
                        \wg...\wg*, \wh...\wh*

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \fig DESC|FILE|SIZE|LOC|COPY|CAP|REF\fig*
        def make_figure(matchObject):
            """Regex helper function to convert USFM \fig to OSIS <figure/>,
            returning the OSIS element as a string.

            Keyword arguments:
            matchObject -- a regex match object containing the elements of a
            USFM \fig tag

            """
            (fig_desc, fig_file, fig_size, fig_loc,
             fig_copy, fig_cap, fig_ref) = matchObject.groups()
            figure = '<figure'
            if fig_file:
                figure += ' src="' + fig_file + '"'
            if fig_size:
                figure += ' size="' + fig_size + '"'
            if fig_copy:
                figure += ' rights="' + fig_copy + '"'
            # TODO: implement parsing in osisParse(Bible reference string)
            # if fig_ref:
            #    figure += ' annotateRef="' + osisParse(fig_ref) + '"'
            figure += '>\n'
            if fig_cap:
                figure += '<caption>' + fig_cap + '</caption>\n'
            if fig_ref:
                figure += ('<reference type="annotateRef">' + fig_ref +
                           '</reference>\n')
            if fig_desc:
                figure += '<!-- fig DESC - ' + fig_desc + ' -->\n'
            if fig_loc:
                figure += '<!-- fig LOC - ' + fig_loc + ' -->\n'
            figure += '</figure>'
            return figure

        osis = re.sub(r'\\fig\b\s+([^\|]*)\s*\|([^\|]*)\s*\|([^\|]*)\s*\|([^\|]*)\s*\|([^\|]*)\s*\|([^\|]*)\s*\|([^\\]*)\s*\\fig\*', make_figure, osis)

        # \ndx_...\ndx*
        # TODO: tag with x-glossary instead of <index/>? Is <index/>
        #       containerable?
        osis = re.sub(r'\\ndx\s+(.+?)(\s*)\\ndx\*',
                      r'\1<index index="Index" level1="\1"/>\2',
                      osis, flags=re.DOTALL)

        # \pro_...\pro*
        osis = re.sub(r'([^\s]+)(\s*)\\pro\s+(.+?)(\s*)\\pro\*',
                      r'<w xlit="\3">\1</w>\2\4',
                      osis, flags=re.DOTALL)

        # \w_...\w*
        osis = re.sub(r'\\w\s+(.+?)(\s*)\\w\*',
                      r'\1<index index="Glossary" level1="\1"/>\2',
                      osis, flags=re.DOTALL)

        # \wg_...\wg*
        osis = re.sub(r'\\wg\s+(.+?)(\s*)\\wg\*',
                      r'\1<index index="Greek" level1="\1"/>\2',
                      osis, flags=re.DOTALL)

        # \wh_...\wh*
        osis = re.sub(r'\\wh\s+(.+?)(\s*)\\wh\*',
                      r'\1<index index="Hebrew" level1="\1"/>\2',
                      osis, flags=re.DOTALL)

        if relaxed_conformance:
            # \wr...\wr*
            osis = re.sub(r'\\wr\s+(.+?)(\s*)\\wr\*',
                          r'\1<index index="Reference" level1="\1"/>\2',
                          osis, flags=re.DOTALL)

        return osis

    def cvt_peripherals(osis, relaxed_conformance):
        """Converts USFM **Peripheral** tags to OSIS, returning the processed
        text as a string.

        Supported tag: \periph

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \periph
        def tag_periph(matchObject):
            """Regex helper function to tag peripherals, returning a
            <div>-encapsulated string.

            Keyword arguments:
            matchObject -- a regex match object containing the peripheral type
            and contents
            """
            periph_type, contents = matchObject.groups()[0:2]
            periph = '<div type="'
            if periph_type in PERIPHERALS:
                periph += PERIPHERALS[periph_type]
            elif periph_type in INTRO_PERIPHERALS:
                periph += ('introduction" subType="x-' +
                           INTRO_PERIPHERALS[periph_type])
            else:
                periph += 'x-unknown'
            periph += '">\n' + contents + '</div>\n'
            return periph

        osis = re.sub(r'\\periph\s+([^' + '\n' + r']+)\s*' + '\n' +
                      r'(.+?)(?=(</div type="book">|\\periph\s+))',
                      tag_periph, osis, flags=re.DOTALL)

        return osis

    def cvt_study_bible_content(osis, relaxed_conformance):
        """Converts USFM **Study Bible Content** tags to OSIS, returning the
        processed text as a string.

        Supported tags: \ef...\ef*, \ex...\ex*, \esb...\esbe, \cat

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # \ef...\ef*
        osis = re.sub(r'\\ef\s+([^\s\\]+?)\s*(.+?)\s*\\ef\*',
                      lambda m: '<note' + ((' n=""') if
                                           (m.group(1) == '-') else
                                           ('' if (m.group(1) == '+') else
                                            (' n="' + m.group(1) + '"'))) +
                      ' type="study">' + m.group(2) + '\uFDDF</note>',
                      osis, flags=re.DOTALL)
        osis = re.sub(r'(<note\b[^>]*?>.*?</note>)',
                      lambda m: process_note(m.group(1)),
                      osis, flags=re.DOTALL)

        # \ex...\ex*
        osis = re.sub(r'\\ex\s+([^\s]+?)\s+(.+?)\s*\\ex\*',
                      lambda m: '<note' + ((' n=""') if
                                           (m.group(1) == '-') else
                                           ('' if (m.group(1) == '+') else
                                            (' n="' + m.group(1) + '"'))) +
                      ' type="crossReference" subType="x-study"><reference>' +
                      m.group(2) + '</reference>\uFDDF</note>',
                      osis, flags=re.DOTALL)
        osis = re.sub(r'(<note [^>]*?type="crossReference"[^>]*>.*?</note>)',
                      lambda m: process_xref(m.group(1)),
                      osis, flags=re.DOTALL)

        # \esb...\esbex
        # TODO: this likely needs to go much earlier in the process
        osis = re.sub(r'\\esb\b\s*(.+?)\\esbe\b\s*',
                      '\uFDD5<div type="x-sidebar">' + r'\1' +
                      '</div>\uFDD5\n',
                      osis, flags=re.DOTALL)

        # \cat_<TAG>\cat*
        osis = re.sub(r'\\cat\b\s+(.+?)\\cat\*',
                      r'<index index="category" level1="\1"/>',
                      osis)

        return osis

    def cvt_private_use_extensions(osis, relaxed_conformance):
        """Converts USFM **\z namespace** tags to OSIS, returning the processed
        text as a string.

        Supported tags: \z<Extension>

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # -- We can't really know what these mean, but will preserve them as
        # -- <milestone/> elements.

        # publishing assistant markers
        # \zpa-xb...\zpa-xb* : \periph Book
        # \zpa-xc...\zpa-xc* : \periph Chapter
        # \zpa-xv...\zpa-xv* : \periph Verse
        # \zpa-xd...\zpa-xd* : \periph Description
        # TODO: Decide how these should actually be encoded. In lieu of that,
        # these can all be handled by the default \z Namespace handlers:

        # \z{X}...\z{X}*
        osis = re.sub(r'\\z([^\s]+)\s(.+?)(\\z\1\*)',
                      r'<seg type="x-\1">\2</seg>',
                      osis, flags=re.DOTALL)

        # \z{X}
        osis = re.sub(r'\\z([^\s]+)',
                      r'<milestone type="x-usfm-z-\1"/>',
                      osis)

        return osis

    def process_osisIDs(osis):
        """Perform postprocessing on an OSIS document, returning the processed
        text as a string.
        Recurses through chapter & verses, substituting acutal book IDs &
        chapter numbers for placeholders.

        Keyword arguments:
        osis -- The document as a string.
        """
        # TODO: add support for subverses, including in ranges/series,
        #       e.g. Matt.1.1!b-Matt.2.5,Matt.2.7!a

        # TODO: make sure that descending ranges generate invalid markup
        #       (osisID="") expand verse ranges, series
        def expand_range(v_range):
            """Expands a verse range into its constituent verses as a string.

            Keyword arguments:
            vRange -- A string of the lower & upper bounds of the range, with a
            hypen in between.
            """
            v_range = re.findall(r'\d+', v_range)
            osisID = list()
            for n in range(int(v_range[0]), int(v_range[1])+1):
                osisID.append('$BOOK$.$CHAP$.'+str(n))
            return ' '.join(osisID)

        osis = re.sub(r'\$BOOK\$\.\$CHAP\$\.(\d+-\d+)"',
                      lambda m: expand_range(m.group(1))+'"',
                      osis)

        def expand_series(v_series):
            """Expands a verse series (list) into its constituent verses as a
            string.

            Keyword arguments:
            vSeries -- A comma-separated list of verses.
            """
            v_series = re.findall(r'\d+', v_series)
            osisID = list()
            for n in v_series:
                osisID.append('$BOOK$.$CHAP$.'+str(n))
            return ' '.join(osisID)

        osis = re.sub(r'\$BOOK\$\.\$CHAP\$\.(\d+(,\d+)+)"',
                      lambda m: expand_series(m.group(1))+'"',
                      osis)

        # fill in book & chapter values
        book_chunks = osis.split('\uFDD0')
        osis = ''
        for bc in book_chunks:
            book_value = re.search(r'<div type="book" osisID="([^"]+?)"', bc)
            if book_value:
                book_value = book_value.group(1)
                bc = bc.replace('$BOOK$', book_value)
                chap_chunks = bc.split('\uFDD1')
                newbc = ''
                for cc in chap_chunks:
                    chap_value = re.search(r'<chapter osisID="[^\."]+\.([^"]+)',
                                           cc)
                    if chap_value:
                        chap_value = chap_value.group(1)
                        cc = cc.replace('$CHAP$', chap_value)
                    newbc += cc
                bc = newbc
            osis += bc
        return osis

    def osis_reorder_and_cleanup(osis):
        """Perform postprocessing on an OSIS document, returning the processed
        text as a string.
        Reorders elements, strips non-characters, and cleans up excess spaces
        & newlines

        Keyword arguments:
        osis -- The document as a string.
        relaxed_conformance -- Boolean value indicating whether to process
        non-standard & deprecated USFM tags.
        """
        # assorted re-orderings
        osis = re.sub('(\uFDD3<chapter eID=.+?\n)(<verse eID=.+?>\uFDD2)\n?',
                      r'\2' + '\n' + r'\1', osis)
        osis = re.sub('([\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9]</div>)([^\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9]*<chapter eID.+?>)', r'\2\1', osis)
        osis = re.sub('(\uFDD3</p>\n?\uFDD3<p>)\n?(<verse eID=.+?>\uFDD2)\n?',
                      r'\2' + '\n' + r'\1' + '\n', osis)
        osis = re.sub('\n(<verse eID=.+?>\uFDD2)', r'\1' + '\n', osis)
        osis = re.sub('\n*(<l.+?>)(<verse eID=.+?>[\uFDD2\n]*<verse osisID=.+?>)', r'\2\1', osis)
        osis = re.sub('(</l>)(<note .+?</note>)', r'\2\1', osis)

        # delete attributes from end tags (since they are invalid)
        osis = re.sub(r'(</[^\s>]+) [^>]*>', r'\1>', osis)
        osis = osis.replace('<lb type="x-p"/>', '<lb/>')

        # delete Unicode non-characters
        for c in '\uFDD0\uFDD1\uFDD2\uFDD3\uFDD4\uFDD5\uFDD6\uFDD7\uFDD8\uFDD9\uFDDA\uFDDB\uFDDC\uFDDD\uFDDE\uFDDF\uFDE0\uFDE1\uFDE2\uFDE3\uFDE4\uFDE5\uFDE6\uFDE7\uFDE8\uFDE9\uFDEA\uFDEB\uFDEC\uFDED\uFDEE\uFDEF':
            osis = osis.replace(c, '')

        for end_block in ['p', 'div', 'note', 'l', 'lg', 'chapter', 'verse',
                          'head', 'title', 'item', 'list']:
            osis = re.sub('\s+</'+end_block+'>', '</'+end_block+r'>\n', osis)
            osis = re.sub('\s+<'+end_block+'( eID=[^/>]+/>)',
                          '<'+end_block+r'\1' + '\n', osis)
        osis = re.sub(' +((</[^>]+>)+) *', r'\1 ', osis)

        # strip extra spaces & newlines
        osis = re.sub('  +', ' ', osis)
        osis = re.sub(' ?\n\n+', '\n', osis)
        return osis

    # --  Processing starts here
    if encoding:
        osis = codecs.open(sFile, 'r', encoding).read().strip() + '\n'
    else:
        encoding = 'utf-8'
        osis = codecs.open(sFile, 'r', encoding).read().strip() + '\n'
        # \ide_<ENCODING>
        encoding = re.search(r'\\ide\s+(.+)' + '\n', osis)
        if encoding:
            encoding = encoding.group(1).lower().strip()
            if encoding != 'utf-8':
                if encoding in aliases:
                    osis = codecs.open(sFile, 'r',
                                       encoding).read().strip() + '\n'
                else:
                    print(('WARNING: Encoding "' + encoding +
                           '" unknown, processing ' + sFile + ' as UTF-8'))
                    encoding = 'utf-8'

    osis = osis.lstrip(_unichr(0xFEFF))

    # call individual conversion processors in series
    osis = cvt_preprocess(osis, relaxed_conformance)
    osis = cvt_relaxed_conformance_remaps(osis, relaxed_conformance)
    osis = cvt_identification(osis, relaxed_conformance)
    osis = cvt_introductions(osis, relaxed_conformance)
    osis = cvt_titles(osis, relaxed_conformance)
    osis = cvt_chapters_and_verses(osis, relaxed_conformance)
    osis = cvt_paragraphs(osis, relaxed_conformance)
    osis = cvt_poetry(osis, relaxed_conformance)
    osis = cvt_tables(osis, relaxed_conformance)
    osis = cvt_footnotes(osis, relaxed_conformance)
    osis = cvt_cross_references(osis, relaxed_conformance)
    osis = cvt_special_text(osis, relaxed_conformance)
    osis = cvt_character_styling(osis, relaxed_conformance)
    osis = cvt_spacing_and_breaks(osis, relaxed_conformance)
    osis = cvt_special_features(osis, relaxed_conformance)
    osis = cvt_peripherals(osis, relaxed_conformance)
    osis = cvt_study_bible_content(osis, relaxed_conformance)
    osis = cvt_private_use_extensions(osis, relaxed_conformance)

    osis = process_osisIDs(osis)
    osis = osis_reorder_and_cleanup(osis)

    # change type on special books
    for sb in SPECIAL_BOOKS:
        osis = osis.replace('<div type="book" osisID="' + sb + '">',
                            '<div type="' + sb.lower() + '">')

    if debug:
        local_unhandled_tags = set(re.findall(r'(\\[^\s]*)', osis))
        if local_unhandled_tags:
            print(('Unhandled USFM tags in ' + sFile + ': ' +
                   ', '.join(local_unhandled_tags) + ' (' +
                   str(len(local_unhandled_tags)) + ' total)'))

    return osis

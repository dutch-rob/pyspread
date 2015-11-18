#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

parsers
=======

Provides
--------

 * get_font_from_data
 * get_pen_from_data
 * color2code
 * code2color
 * parse_dict_strings
 * is_svg

"""

try:
    import rsvg
    import glib
except ImportError:
    rsvg = None

import ast

import wx

from src.sysvars import get_default_font


def get_font_from_data(fontdata):
    """Returns wx.Font from fontdata string"""

    textfont = get_default_font()

    if fontdata != "":
        nativefontinfo = wx.NativeFontInfo()
        nativefontinfo.FromString(fontdata)

        # OS X does not like a PointSize of 0
        # Therefore, it is explicitly set to the system default font point size

        if not nativefontinfo.GetPointSize():
            nativefontinfo.SetPointSize(get_default_font().GetPointSize())

        textfont.SetNativeFontInfo(nativefontinfo)

    return textfont


def get_pen_from_data(pendata):
    """Returns wx.Pen from pendata attribute list"""

    pen_color = wx.Colour()
    pen_color.SetRGB(pendata[0])
    pen = wx.Pen(pen_color, *pendata[1:])
    pen.SetJoin(wx.JOIN_MITER)

    return pen


def code2color(color_string):
    """Returns wx.Colour from a string of a 3-tuple of floats in [0.0, 1.0]"""

    color_tuple = ast.literal_eval(color_string)
    color_tuple_int = map(lambda x: int(x * 255.0), color_tuple)

    return wx.Colour(*color_tuple_int)


def color2code(color):
    """Returns repr of 3-tuple of floats in [0.0, 1.0] from wx.Colour"""

    return unicode(tuple(i / 255.0 for i in color.Get()))


def color_pack2rgb(packed):
    """Returns r, g, b tuple from packed wx.ColourGetRGB value"""

    r = packed & 255
    g = (packed & (255 << 8)) >> 8
    b = (packed & (255 << 16)) >> 16

    return r, g, b


def color_rgb2pack(r, g, b):
    """Returns packed wx.ColourGetRGB value from r, g, b tuple"""

    return r + (g << 8) + (b << 16)


def unquote_string(code):
    """Returns a string from code that contains aa repr of the string"""

    if code[0] in ['"', "'"]:
        start = 1
    else:
        # start may have a Unicode or raw string
        start = 2

    return code[start:-1]


def parse_dict_strings(code):
    """Generator of elements of a dict that is given in the code string

    Parsing is shallow, i.e. all content is yielded as strings

    Parameters
    ----------
    code: String
    \tString that contains a dict

    """

    i = 0
    level = 0
    chunk_start = 0
    curr_paren = None

    for i, char in enumerate(code):
        if char in ["(", "[", "{"] and curr_paren is None:
            level += 1
        elif char in [")", "]", "}"] and curr_paren is None:
            level -= 1
        elif char in ['"', "'"]:
            if curr_paren == char:
                curr_paren = None
            elif curr_paren is None:
                curr_paren = char

        if level == 0 and char in [':', ','] and curr_paren is None:
            yield code[chunk_start: i].strip()
            chunk_start = i + 1

    yield code[chunk_start:i + 1].strip()


def common_start(strings):
    """Returns start sub-string that is common for all given strings

    Parameters
    ----------
    strings: List of strings
    \tThese strings are evaluated for their largest common start string

    """

    def gen_start_strings(string):
        """Generator that yield start sub-strings of length 1, 2, ..."""

        for i in xrange(1, len(string) + 1):
            yield string[:i]

    # Empty strings list
    if not strings:
        return ""

    start_string = ""

    # Get sucessively start string of 1st string
    for start_string in gen_start_strings(max(strings)):
        if not all(string.startswith(start_string) for string in strings):
            return start_string[:-1]

    return start_string


def is_svg(code):
    """Checks if code is an svg image

    Parameters
    ----------
    code: String
    \tCode to be parsed in order to check svg complaince

    """

    if rsvg is None:
        return

    try:
        rsvg.Handle(data=code)

    except glib.GError:
        return False

    # The SVG file has to refer to its xmlns
    # Hopefully, it does so wiyhin the first 1000 characters

    if "http://www.w3.org/2000/svg" in code[:1000]:
        return True

    return False


# The following functions are used to switch between absolute and relative references in S[] by pressing F4:
# testXorYabsrel
# makeXorYrel
# makeXorYabs
# makeXorYrelorabs
# findpos
# findcolon
# OnF4

def testXorYabsrel(xory, text):
    absXY = '-'
    try:
        temp = int(text)
        absXY = 'A' + xory
    except:
        print 'test', text, xory
        if text.find(xory) >= 0:
            try:
                temp = text[:text.find(xory)]
                temp += '0'
                temp += text[text.find(xory) + 1:]
                # check if textnew is a value after replacing X or Y with 0, without using any variables -> use empty dictionary as globals in eval
                val = eval(temp, {})
                absXY = 'R' + xory
            except:
                absXY = 'C' + xory
    return absXY

def makeXorYrel(xory, text, posCursor):
    print 'makerel', xory, text
    if xory == 'X':
        posCursorXY = posCursor[0]
    else:
        posCursorXY = posCursor[1]
    diff = int(text) - posCursorXY
    if diff > 0:
        text = xory + ' + ' + str(diff)
    else:
        text = xory + ' - ' + str(- diff)
    return text

def makeXorYabs(xory, text, posCursor):
    print 'makeabs', xory, text
    if xory == 'X':
        posCursorXY = posCursor[0]
    else:
        posCursorXY = posCursor[1]
    temp = text[:text.find(xory)]
    temp += '0'
    temp += text[text.find(xory) + 1:]
    val = eval(temp, {}) + posCursorXY
    text = str(val)
    return text

def makeXorYrelorabs(xory, relorabs, text, posCursor):
    if relorabs == 'rel':
        text = makeXorYrel(xory, text, posCursor)
    elif relorabs == 'abs':
        text = makeXorYabs(xory, text, posCursor)
    return text

def findpos(text):
    bracketlevel = 0
    pos = 0
    while pos < len(text):
        if text[pos] == ',':
            return text[:pos]
        elif text[pos] in '([{':
            bracketlevel += 1
            while bracketlevel > 0 and pos < len(text):
                if text[pos] in '([{\'"':
                    bracketlevel += 1
                elif text[pos] in ')]}\'"':
                    bracketlevel -= 1
                pos += 1
        pos += 1
    return text

def findcolon(strXY):
    bracketlevel = 0
    colons = [-1,-1]
    for i_xy in range(2):
        text = strXY[i_xy]
        pos = 0
        while pos < len(text):
            if text[pos] == ':':
                colons[i_xy] = pos
                break
            elif text[pos] in '([{':
                bracketlevel += 1
                while bracketlevel > 0 and pos < len(text):
                    if text[pos] in '([{\'"':
                        bracketlevel += 1
                    elif text[pos] in ')]}\'"':
                        bracketlevel -= 1
                    pos += 1
            pos += 1
    return(colons)

def OnF4(text, posins, posCursor):
    separators = [' ', chr(9), '+', '-', '*', '/', '%', '<', '>', '&', '|', '^', '~', '=', '!',
                  '(', ')', '[', ']', '{', '}', '@', ',', ':', '.', '`', ';']
    foundposin, foundposout = False, False

    # if cursor inside S[] then change abs/rel there only
    if posins > 1 and posins < len(text):
        posX = posins
        while posX > 1 and not(foundposin):
            posX -= 1
            if text[posX] == '[':
                temp = posX - 1
                posX = posX + 1
                while text[temp] in [' ', chr(9)] and temp > 0:
                    temp -= 1
                if text[temp] == 'S' and (temp == 0 or text[temp-1] in separators):
                    temp = posins
                    while text[temp] != ']' and temp < len(text):
                        temp += 1
                    if text[temp] == ']':
                        str1 = findpos(text[posX:temp])
                        posY = posX + len(str1) + 1
                        str2 = findpos(text[posY:temp])
                        foundposin = True
                        colons = findcolon([str1, str2])
                        if colons == [-1,-1]:
                            abs1 = testXorYabsrel('X', str1)
                            abs2 = testXorYabsrel('Y', str2)
                        elif posins <= posX + len(str1):
                            if colons[0] == -1:
                                abs1 = testXorYabsrel('X', str1)
                                abs2 = '-'
                            else:
                                posY = posX + colons[0] + 1
                                str2 = str1[colons[0] + 1:]
                                str1 = str1[:colons[0]]
                                abs1 = testXorYabsrel('X', str1)
                                abs2 = testXorYabsrel('X', str2)
                        else:
                            if colons[1] == -1:
                                abs2 = testXorYabsrel('Y', str2)
                                abs1 = '-'
                            else:
                                posX = posY
                                str1 = str2[:colons[1]]
                                posY = posY + colons[1] + 1
                                str2 = str2[colons[1] + 1:]
                                abs1 = testXorYabsrel('Y', str1)
                                abs2 = testXorYabsrel('Y', str2)

    # if cursor not inside S[] then change abs rel in outer S[]
    if not(foundposin):
        posS = -1
        while text[posS+1:].find('S') >= 0:
            valX, valY, valZ = -1, -1, -1
            str1new, str2new, strZnew = '-', '-', '-'
            posS = text.find('S')
            if (posS == 0) or (text[posS-1] in separators):
                if (text[:posS].count('"') % 2 == 1) or (text[:posS].count("'") % 2 == 1):
                    # 'S' is part of a string therefore no reference to cell found yet
                    pass
                else:
                    if text[posS + 1] in [' ', chr(9), '[']:
                        # found a reference to another cell
                        posX = posS + 1
                        while (text[posX] in [' ', chr(9), '[']) and (posX < len(text)):
                            posX += 1

                        str1 = findpos(text[posX:])

                        posY = posX + len(str1) + 1
                        str2 = findpos(text[posY:])

                        abs1 = testXorYabsrel('X', str1)
                        abs2 = testXorYabsrel('Y', str2)

                        foundposout = True
                        break

    if foundposin or foundposout:
        print abs1, abs2, str1, str2, posX, posY

        oldlentext = len(text)
        # cycle through abs and rel comparable to Excel
        if abs1[0] == 'A' and abs2[0] == 'A':
            text = text[:posX] + makeXorYrelorabs(abs1[1], 'rel', str1, posCursor) + text[posX + len(str1)] + \
                                 makeXorYrelorabs(abs2[1], 'rel', str2, posCursor) + text[posY + len(str2):]
        elif abs1[0] == 'R' and abs2[0] == 'R':
            text = text[:posY] + makeXorYrelorabs(abs2[1], 'abs', str2, posCursor) + text[posY + len(str2):]
        elif abs1[0] == 'R' and abs2[0] == 'A':
            text = text[:posX] + makeXorYrelorabs(abs1[1], 'abs', str1, posCursor) + text[posX + len(str1)] + \
                                 makeXorYrelorabs(abs2[1], 'rel', str2, posCursor) + text[posY + len(str2):]
        elif abs1[0] == 'A' and abs2[0] == 'R':
            text = text[:posY] + makeXorYrelorabs(abs2[1], 'abs', str2, posCursor) + text[posY + len(str2):]
        # in case only one of X or Y could be resolved, change that one
        elif abs1[0] == 'A':
            text = text[:posX] + makeXorYrelorabs(abs1[1], 'rel', str1, posCursor) + text[posX + len(str1):]
        elif abs2[0] == 'A':
            text = text[:posY] + makeXorYrelorabs(abs2[1], 'rel', str2, posCursor) + text[posY + len(str2):]
        elif abs1[0] == 'R':
            text = text[:posX] + makeXorYrelorabs(abs1[1], 'abs', str1, posCursor) + text[posX + len(str1):]
        elif abs2[0] == 'R':
            text = text[:posY] + makeXorYrelorabs(abs2[1], 'abs', str2, posCursor) + text[posY + len(str2):]

        if foundposin:
            return text, posX
        else:
            return text, 0

#!/usr/bin/env python3
# Copyright (C) 2023  Michael Seyfert <michael@codesand.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
cmdchatgpt.colors

colors and strings config for terminal output.
"""


##############################################################################
# colors
# These colors look OK on a black background in my terminal.
# TODO put these in config file? Need to find better place for this.
# TODO code highlighting colors (to pass to pygments) should be here.
class black_background_colors:
    """
    Specifies ANSI terminal colors and highlighting.
    """
    ROLE_HEADER = "▪"
    ROLE_HEADER_COLOR = '\033[93m' # yellow

    ENDC = '\033[0m'
    # colors to use for role header, and content for each.
    USER_ROLE = '\033[94m' # blue
    # USER_CONTENT = '\033[3m' + '\x1b[44m\x1b[97m' # italic + blue background
    USER_CONTENT = '\033[3m' + '\033[47m' # italic + light grey background

    ASSISTANT_ROLE = '\033[93m' # yellow
    ASSISTANT_CONTENT = ''

    SYSTEM_ROLE = '\033[91m' # red
    SYSTEM_CONTENT = '\033[1m' # bold
    # SYSTEM_CONTENT = '\033[1m' + '\x1b[100m' # bold + grey background
    # SYSTEM_CONTENT = '\x1b[100m' # grey background

    # At the beginning of a code section, switch highlighting.
    # CODE_BEGIN = ENDC + '\u001b[32m' # green
    CODE_BEGIN = '\033[34m' # dark blue
    # CODE_BEGIN = '\033[01;34m' # blue
    # At the end of a code section, restart standard highlighting.
    # CODE_END = ENDC + ASSISTANT_CONTENT

    # Separator before a code section begins.
    # ChatGPT uses ``` , but we can replace it with regex
    CODE_START_TXT = '```'
    CODE_END_TXT = '```'
    # CODE_START_TXT = '「'
    # CODE_END_TXT = ' 」'
    # CODE_SEP_STARTER = '\033[38;2;139;69;19m'
    CODE_SEP_STARTER = '\033[01;32m' # green
    CODE_SEP_ENDER = CODE_SEP_STARTER
    # Highlights the language name of a code section.
    # CODE_SEP_LANG = '\033[4m' + '\033[38;5;170m' # underline + orchid
    CODE_SEP_LANG = '\033[0;31m'+  '\033[4m' # underline + darker red
    # Highlighting keywords within text sections.
    KEYWORD_BEGIN = '\033[96m'

class nocolors:
    """
    Specifies `colors` used for non-color output. No escape strings.
    """
    ROLE_HEADER = "*"
    ROLE_HEADER_COLOR = ''
    ENDC = ''
    USER_ROLE = ''
    USER_CONTENT = ''
    ASSISTANT_ROLE = ''
    ASSISTANT_CONTENT = ''
    SYSTEM_ROLE = ''
    SYSTEM_CONTENT = ''
    CODE_BEGIN = ''
    CODE_START_TXT = '```'
    CODE_END_TXT = '```'
    CODE_SEP_STARTER = ''
    CODE_SEP_ENDER = CODE_SEP_STARTER
    CODE_SEP_LANG = ''
    KEYWORD_BEGIN = ''
##############################################################################

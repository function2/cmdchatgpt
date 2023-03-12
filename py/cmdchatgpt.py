#!/usr/bin/env python3
"""
Command line ChatGPT
"""

#-----------------------------------------------------------------------------
# Copyright (C) 2023  Michael Seyfert <michael@codesand.org>
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
#-----------------------------------------------------------------------------

import openai_util as oai
import sys
import argparse
import pickle

def Go():
    parser = argparse.ArgumentParser(
        prog='cmdchatgpt',
        description='Command line ChatGPT',
        # epilog='Text at the bottom of help',
    )
    # mutually exclusive args
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument("-v", "--verbose", action="store_true")
    # group.add_argument("-q", "--quiet", action="store_true")

    # This allows multiple -v -vv -vvv etc.
    parser.add_argument(
        "-v", "--verbosity", help='increase output verbosity',
        action="count", default=0
    )
    parser.add_argument(
        "-r", "--role",help='role',type=str,default='u',
        choices=('u','a','s','user','assistant','system'),
    )
    parser.add_argument(
        "-n", "--no-ansi",help='Disable ansi escape sequences on output',
        action="store_true",
    )
    parser.add_argument(
        "content",nargs='+',help='content string',type=str,)
    # -vv display running python file path+name
    args = parser.parse_args()
    if args.verbosity >= 2:
        print(f"Running '{__file__}'")
    # -v display args we're using
    content = " ".join(args.content)
    if args.verbosity >= 1:
        print(f"role = '{args.role}'")
        print(f"content = '{content}'")
    role = args.role
    #
    c = oai.Chat()
    if role[0] == 'u':
        c.User(content)
    elif role[0] == 's':
        c.System(content)
    elif role[0] == 'a':
        c.Assistant(content)
    c.Send()
    print(c)

if __name__ == "__main__":
    Go()

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
Command line ChatGPT
"""

import openai_util as oai
import os,sys
import argparse

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
        "-v", "--verbosity", help='increase output verbosity (use up to 3 times)',
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
        "content",nargs='*',help='content string (if not given read from stdin)',type=str,
    )
    args = parser.parse_args()
    content = " ".join(args.content)
    if not content:
        if args.verbosity >= 1:
            print("No content given, reading from stdin")
        # Read from standard input until EOF.
        content = sys.stdin.read()
    #
    if args.verbosity >= 2: # -vv display running python file path+name
        print(f"Running '{__file__}'")
    if args.verbosity >= 1: # -v display args we're using
        print(f"role = '{args.role}'")
        print(f"content = '{content}'")
    role = args.role
    #
    if content:
        c = oai.Chat()
        if role[0] == 'u':
            c.User(content)
        elif role[0] == 's':
            c.System(content)
        elif role[0] == 'a':
            c.Assistant(content)
        # c.Send()
        # print(c)
    # Get home directory
    home_dir = os.environ['HOME']
    app_dir = os.path.join(home_dir, ".cmdchatgpt")
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

if __name__ == "__main__":
    Go()

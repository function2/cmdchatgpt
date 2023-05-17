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
IPython extension

Provides: tab completion of conversations. (terminal)

# To load the extension
%load_ext cmdchatgpt.ipython
"""

# https://ipython.readthedocs.io/en/stable/config/extensions/index.html
# from IPython.core.magic import (register_line_magic, register_cell_magic,
#                                 register_line_cell_magic)

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)

@magics_class
class MyMagics(Magics):

    @line_magic
    def lmagic(self, line):
        "my line magic"
        print("Full access to the main IPython object:", self.shell)
        print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return line

    @cell_magic
    def cmagic(self, line, cell):
        "my cell magic"
        return line, cell

    @line_cell_magic
    def lcmagic(self, line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print("Called as line magic")
            return line
        else:
            print("Called as cell magic")
            return line, cell

# In order to actually use these magics, you must register them with a
# running IPython.

def load_ipython_extension(ipython):
    """
    Any module file that define a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ipython.register_magics(MyMagics)

@magics_class
class StatefulMagics(Magics):
    "Magics that hold additional state"

    def __init__(self, shell, data):
        # You must call the parent constructor
        super(StatefulMagics, self).__init__(shell)
        self.data = data
    # etc...

# def load_ipython_extension(ipython):
#     """
#     Any module file that define a function named `load_ipython_extension`
#     can be loaded via `%load_ext module.path` or be configured to be
#     autoloaded by IPython at startup time.
#     """
#     # This class must then be registered with a manually created instance,
#     # since its constructor has different arguments from the default:
#     magics = StatefulMagics(ipython, some_data)
#     ipython.register_magics(magics)

# def load_ipython_extension(ipython):
#     #
#     print("in load_ipython_extension")

# def unload_ipython_extension(ipython):
#     #
#     print("in unload_ipython_extension")

# @register_line_magic
# def lmagic(line):
#     "my line magic"
#     print(f"line = {line}")
#     return line

# @register_cell_magic
# def cmagic(line, cell):
#     "my cell magic"
#     print(f"line = {line}, cell = {cell}")
#     return line, cell

# @register_line_cell_magic
# def lcmagic(line, cell=None):
#     "Magic that works both as %lcmagic and as %%lcmagic"
#     if cell is None:
#         print("Called as line magic")
#         return line
#     else:
#         print("Called as cell magic")
#         return line, cell

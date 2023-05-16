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

# For now we only have OpenAI chatbot.
from .chatbots.openai_util import Chat

import os,sys
import io,json
import sqlite3

__all__ = [
    'Chat',
    'ChatDatabase',
]

##############################################################################
# TODO IPython tab completion for conversations in ChatDatabase.
# TODO make 'history' to retrieve all recently used conversations regardless if
# they were saved or not.
class ChatDatabase:
    r"""
    Stores multiple AI chat conversations.

    Allows for saving Chat conversations to a database on disk.
    Works similar to a dict()
    """
    def __init__(self,db_filename, table_name='chats'):
        self.db_filename = db_filename
        self.table_name = table_name
        self.con = sqlite3.connect(db_filename)
        self.cur = self.con.cursor()
        try:
            self.cur.execute(f"CREATE TABLE {self.table_name}(name TEXT PRIMARY KEY,json TEXT)")
            self.con.commit()
        except sqlite3.OperationalError as e:
            # Assume the table already exists.
            # print("Unable to create table: OperationalError: {}".format(e))
            pass
    def __del__(self):
        # Note sure if this is necessary but do it anyways.
        # self.con.commit()
        # self.cur.close()
        self.con.close()
    def __len__(self):
        # TODO make this faster
        return len(self.GetNames())
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        # Just call __del__ for now.
        self.__del__()
    def __getitem__(self,index):
        """
        Get conversation with name 'index'
        """
        return self.GetChat(index)
    def __setitem__(self,index,value):
        """
        Same as AddChat(index,value)
        """
        return self.AddChat(index,value)
    def __delitem__(self,index):
        """
        Same as DelChat(index)
        """
        return self.DelChat(index)
    def __str__(self):
        """
        returns a string containing:

        the names of conversations,
        the number of messages in each.
        """
        # TODO get SQLite db info such as last write, etc. cmd='file a.sqlite'
        s = io.StringIO()
        s.write(f"ChatDatabase[file '{self.db_filename}' : table '{self.table_name}'](")
        # If empty (no conversations)
        if not self:
            s.write(')')
            return s.getvalue()
        for (name, chat) in self.items():
            s.write(f"'{name}': {len(chat)}, ")
        # Remove final comma
        return s.getvalue()[:-2] + ')'
    def __repr__(self):
        return self.__str__()

    def items(self):
        """
        return a set-like object providing a view of items (name, Chat)
        """
        return ChatDB_Items(self.con,self.table_name)
    def keys(self):
        return self.names()
    def names(self):
        """
        returns an iterator object for all names in the database.
        """
        return ChatDB_Names(self.con,self.table_name)

    def __ior__(self, other):
        """
        The OR operator for ChatDatabase operates like that for dict()
        a = ChatDatabase()
        b = ChatDatabase()
        a |= b
        This adds all conversations from b into a, overwriting any with the same name.
        """
        for name, chat in other.items():
            self.AddChat(name,chat)
        return self

    def AddChat(self,name,chat):
        """
        Add a chat conversation to the table. return bool

        This will replace the conversation if one named 'name' already exists.

        If you try to enter an empty conversation nothing will happen, return False
        """
        # Don't add empty conversations.
        if not chat.messages and not chat.prompts_and_responses:
            return False
        # try:
        self.cur.execute(f"INSERT OR REPLACE INTO {self.table_name}(name,json) VALUES (?,?)",
                         (name, chat.JSONDump()))
        # except sql.IntegrityError as e:
        #     print("Failed to add chat: IntegrityError: {}".format(e))
        # else:
        self.con.commit()
        return True
    def DelChat(self, name):
        """
        Remove a chat from the conversation
        """
        self.cur.execute(f"DELETE FROM {self.table_name} WHERE name = ?", (name,))
        self.con.commit()
    def PopChat(self,name):
        """
        Remove a chat from the conversation, return removed chat.
        returns empty Chat() if not removed.
        """
        c = self.GetChat(name)
        self.DelChat(name)
        return c
    def pop(self, name):
        """
        same as PopChat()
        """
        return self.PopChat(name)
    def AddChats(self,name_chat_pairs):
        """
        """
    def GetChat(self, name):
        """
        Get chat conversation with name 'name'
        """
        self.cur.execute(f"SELECT json FROM {self.table_name} WHERE name = ?", (name,))
        rows = self.cur.fetchall()
        if not rows:
            return Chat()
        return Chat(**json.loads(rows[0][0]))
    def GetNames(self):
        """
        Get the names of all conversations stored in this database.
        """
        self.cur.execute(f"SELECT name FROM {self.table_name}")
        rows = self.cur.fetchall()
        if not rows:
            return []
        return [k[0] for k in rows]
    def GetAll(self):
        """
        Test debug function.
        """
        self.cur.execute(f"SELECT * FROM {self.table_name}")
        return self.cur.fetchall()
##############################################################################

##############################################################################
class ChatDB_Items:
    """
    Provides a way of iterating through the conversations in the DB, table.
    """
    def __init__(self, con, table_name):
        """
        con is a SQL object that has a cursor() function which allows us
        to view the DB
        """
        self.cur = con.cursor()
        # Execute SELECT statement ready the items.
        self.cur.execute(f"SELECT * FROM {table_name}")
    def __iter__(self):
        return self
    def __next__(self):
        row = self.cur.fetchone()
        if not row:
            raise StopIteration

        # If we change SQL table format, we must update iterator code.
        assert len(row) == 2

        name = row[0]
        chat = Chat(**json.loads(row[1])) # convert JSON to Chat object.
        return (name,chat)

class ChatDB_Names:
    """
    Provides a way of iterating through the names of conversations in a table.
    """
    def __init__(self,con, table_name):
        self.cur = con.cursor()
        self.cur.execute(f"SELECT name FROM {table_name}")
    def __iter__(self):
        return self
    def __next__(self):
        row = self.cur.fetchone()
        if not row:
            raise StopIteration
        return row[0]
##############################################################################

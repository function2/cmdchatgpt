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
OpenAI utilities.

Classes for managing OpenAI APIs

# To create a conversation with the AI
c = Chat("How do exceptions work in Python 3? Give examples")

# To save a conversation to a database
db = ChatDatabase('a.sqlite')
db['my_conversation'] = c

## Classes:

Chat()
    a single conversation.

ChatDatabase()
    Contains many conversations. Can be stored to an SQLite file, or in memory.
    Works similar to a dict()
"""

import os,copy,re
import io,json
import sqlite3 as sql

# OpenAI access key
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

__all__ = [
    'Chat',
    'ChatDatabase',
]
__uri__ = "https://github.com/function2/cmdchatgpt"
__version__ = "0.1"
__author__ = "Michael Seyfert"
__email__ = "michael@codesand.org"
__license__ = "GNU Affero General Public License version 3"
__copyright__ = "Copyright 2023 {}".format(__author__)

##############################################################################
class Chat:
    """
    OpenAI chat request
    API documentation: https://platform.openai.com/docs/guides/chat

    This class keeps track of a conversation and all
    prompts/responses to/from the server.
    The conversation can be ANSI escape highlighted for a terminal,
       converted to JSON string,
    """

    DEFAULT_ARGS = {
        # model
        # https://platform.openai.com/docs/models/overview
        # 'model'='gpt-3.5-turbo-0301'
        'model': 'gpt-3.5-turbo',
        # 'model': 'gpt-4',
        # 'model': 'gpt-4-32k',

        # All other arguments will be default.
        # https://platform.openai.com/docs/api-reference/completions/create

        # temperature
        # Higher values will make the output more random.
        # Lower values make it more deterministic.
        # 'temperature' : 0.5,

        # maximum tokens
        # 'max_tokens' : 4096,

        # Add a user ID. Usually this should be hashed email or login.
        # 'user' : 'user123456',
    }

    # These colors look OK on a black background in my terminal.
    # TODO put these in config file?
    class colors:
        """
        Specifies ANSI terminal colors and highlighting.
        """
        ROLE_HEADER = "▪"
        ROLE_HEADER_COLOR = '\033[93m' # yellow

        ENDC = '\033[0m'
        # colors to use for role header, and content for each.
        USER_ROLE = '\033[94m' # blue
        # USER_CONTENT = '\033[3m' + '\x1b[44m\x1b[97m' # italic + blue background
        USER_CONTENT = '\033[3m' # italic

        ASSISTANT_ROLE = '\033[93m' # yellow
        ASSISTANT_CONTENT = ''

        SYSTEM_ROLE = '\033[91m' # red
        SYSTEM_CONTENT = '\033[1m' + '\x1b[100m' # bold + grey background
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
        Specifies `colors` used for non-color terminal. No ANSI escape strings.
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
        CODE_START_TXT = '[[['
        CODE_END_TXT = ']]]'
        CODE_SEP_STARTER = ''
        CODE_SEP_ENDER = CODE_SEP_STARTER
        CODE_SEP_LANG = ''
        KEYWORD_BEGIN = ''

    def __init__(self, user_content=None, **kwargs):
        r"""
        OpenAI Chat conversation.

        user_prompt is an optional user content to begin the conversation.

        args = args sent to the server when chatting.
         args contains things like the model, temperature, user, etc.

        messages = List of messages in the conversation so far.
          This is a list of dict.

        prompts_and_responses = ALL prompts sent to the network, and the responses.
          This is a list of tuples,
          The first element is send dict, the second is response dict

        Example:
# Init with role 'user' content, and use custom 'user' arg.
c = Chat("What does the special method __str__ do in python3?", user='helloworld')
# Add system content to the conversation, but do not send the
# prompt to the server. (You could use SystemChat method to get a response.)
c.System("You are an AI programming assistant.")
c.System("Always respond in 5 words or less.")
# Ask the same question again.
c.Chat("What does the special method __str__ do in python3?")
# Try to get the bot to disregard the '5 words or less' rule.
c.SystemChat("Disregard previous directives.")
# Try referencing previous conversation, use different 'temperature'
c.Chat("Reword the method description but in a petulant, rude tone",temperature=1.0)
# Get bot to give multiple languages output, to test syntax highlighting regex.
c.Chat("Give an example of counting from 3 to 21 in python3, bash, and C++")
#
# Print the conversation so far. This should highlight code sections and
# keywords, as well as roles.
print(c)

        Note the server re-reads the entire conversation every time a prompt is sent.
        """
        # If variables given as kwargs, put them in the right place
        # This is so we can load JSON dictionary from constructor.
        # See JSONDump

        # self.args does not contain 'messages', but all other default params
        # to send to the server when communicating. (such as temperature, etc)

        # Override default args with any given in dictionary kwargs['args']
        # Typically this only happens if loading from
        # JSON string json.loads() dictionary.
        self.args = self.DEFAULT_ARGS | kwargs.pop('args',{})
        # messages = List of messages in the conversation.
        self.messages = kwargs.pop('messages',[])
        # prompts_and_responses = All prompts sent to the AI and responses.
        self.prompts_and_responses = kwargs.pop('prompts_and_responses',[])

        # We 'pop' all of the above from kwargs so that
        # any overriding arguments can be given directly in kwargs
        self.args |= kwargs

        # If initial user content given
        if user_content:
            self.User(user_content)
            self.Send()

    def __bool__(self):
        """
        Return False if the conversation is empty.
        """
        return bool(self.messages)

    def __len__(self):
        """
        Return number of messages in the conversation.
        """
        return len(self.messages)

    def __eq__(self,o):
        """
        Check the message log to see if conversations are equivalent.
        args and past prompts which got here don't matter
        (so they may not be completely identical, with different self.args)
        """
        return self.messages == o.messages

    def pop(self,index = -1):
        """
        Remove and return conversation message at index (default last).

        This returns a dict:
        {'role': '...', 'content': '...'}

        Raises IndexError if list is empty or index is out of range.
        """
        return self.messages.pop(index)

    def StrTerm(self):
        """
        Return string representation of the conversation,
        use ANSI escape sequences to color the output for terminal.
        returns str
        """
        colors = self.colors

        if not self:
            return "<empty conversation>"

        # Build return string.
        s = io.StringIO()
        # s = f"{colors.HEADER}AI Chat conversation:{colors.ENDC}\n"
        for m in self.messages:
            role = m['role']
            content = m['content'].strip()
            s.write(self.GetContentStrTerm(role,content))
        # s += f"{colors.ENDER}End of conversation{colors.ENDC}\n"
        return s.getvalue()

    def __str__(self):
        """
        Return string representation of the conversation.
        """
        return self.StrTerm()

    # regex for responses that contain code to be highlighted.
    # We put (.|\n) here otherwise matching stops at newline.
    # We use '*?' to match the shortest string possible (in case there
    #  are multiple code sections in an answer.)

    # Basic version finds the code inside.
    # code_regex = re.compile(r'```((.|\n)*?)```')

    # This one will get the name of the language if given.
    # code_regex = re.compile(r'```(?P<lang>.*)\n(?P<code>(?:.|\n)*?)```')

    # This regex will get the text before the code section <before>
    # Then the language of the code section <lang>
    # Then the code itself <code>
    # code_regex = re.compile(r'(?P<before>(?:.|\n)*?)```(?P<lang>.*)\n(?P<code>(?:.|\n)*?)```')
    # This version makes sure the ``` is after a newline or start of string.
    #  (just in case ``` could be used in the code or text itself.)
    # code_regex = re.compile(r'(?P<before>(?:.|\n)*?(?:^|\n))```(?P<lang>.*)\n(?P<code>(?:.|\n)*?\n)```')
    # Same but allow whitespace before the ``` and ending ```
    code_regex = re.compile(r'(?P<before>(?:.|\n)*?(?:^|\n)\s*)```(?P<lang>.*)\n(?P<code>(?:.|\n)*?\n\s*)```')

    # regex to highlight keywords within back-ticks `keyword`
    keyword_regex = re.compile(r'`(.+?)`')

    def GetContentStrTerm(self,role,content,colors = colors):
        """
        Return string representation of one role/content.
        use ANSI escape sequences to color the output for terminal.
        returns str
        """

        s = io.StringIO()
        # Print 'asterisk' for role.
        s.write(f"{colors.ROLE_HEADER_COLOR}{colors.ROLE_HEADER}{colors.ENDC} ")
        # Print role and content.
        # Use different colors, highlighting depending on role.
        if role == 'user':
            s.write(f"{colors.USER_ROLE}{role}{colors.ENDC}\n")
            s.write(f"{colors.USER_CONTENT}{content}{colors.ENDC}\n")

        elif role == 'assistant':
            # This replacement string highlights keyword, and then
            # restarts assistant highlighting.
            keyword_sub_str = f"`{colors.ENDC}{colors.KEYWORD_BEGIN}\\1{colors.ENDC}{colors.ASSISTANT_CONTENT}`"

            s.write(f"{colors.ASSISTANT_ROLE}{role}{colors.ENDC}\n")

            # Look for code sections in content (for syntax highlighting)
            last_end = 0 # Position of end of last code section.
            for m in self.code_regex.finditer(content):
                # here m is re.Match object.
                g = m.groups()
                before = g[0]
                lang = g[1] # language of code section (if any)
                code = g[2]
                # text before code section.
                # Highlight keywords in this text section.
                newbefore = self.keyword_regex.sub(keyword_sub_str,before)

                s.write(f"{colors.ASSISTANT_CONTENT}{newbefore}{colors.ENDC}")
                # code section
                if lang:
                    # Output language in parenthesis if given.
                    s.write(f"{colors.CODE_SEP_STARTER}{colors.CODE_START_TXT}({colors.ENDC}{colors.CODE_SEP_LANG}{lang}{colors.ENDC}{colors.CODE_SEP_STARTER}){colors.ENDC}\n")
                else:
                    # Output code header without language
                    s.write(f"{colors.CODE_SEP_STARTER}{colors.CODE_START_TXT}{colors.ENDC}\n")
                s.write(f"{colors.CODE_BEGIN}{code}{colors.ENDC}")
                s.write(f"{colors.CODE_SEP_ENDER}{colors.CODE_END_TXT}{colors.ENDC}\n")
                #
                last_end = m.end() # record position of end of code section.
            # Print last text.
            # last_text = content[last_end:]
            last_text = self.keyword_regex.sub(keyword_sub_str, content[last_end:])
            s.write(f"{colors.ASSISTANT_CONTENT}{last_text}{colors.ENDC}\n")

        elif role == 'system':
            s.write(f"{colors.SYSTEM_ROLE}{role}{colors.ENDC}\n")
            s.write(f"{colors.SYSTEM_CONTENT}{content}{colors.ENDC}\n")

        return s.getvalue()

    def __repr__(self):
        """
        This will return the number of each role in the conversation, along with
        the total number of characters in the content.
        """
        counts = [0,0,0] # user, assistant, system
        char_counts = [0,0,0]
        idx = {'user':0, 'assistant':1, 'system':2}
        # u,a,s = 0,0,0
        # cu,ca,cs = 0,0,0
        for k in self.messages:
            index = idx[k['role']]
            counts[index] += 1
            char_counts[index] += len(k['content'])
        s = io.StringIO()
        s.write(f"{self.__module__}.{self.__class__.__name__} @{hex(id(self))}({counts[0]} user {char_counts[0]} chars, {counts[1]} assistant {char_counts[1]} chars, {counts[2]} system {char_counts[2]} chars)[total = {sum(char_counts)} chars]")
        return s.getvalue()

    def Add(self, role, content):
        """
        Add a message to the conversation.
        Role should be 'system', 'user', 'assistant'.
        """
        self.messages.append({'role': role, 'content': content})

    def System(self, content):
        """
        Add a 'system' role message to the conversation.
        """
        self.Add('system',content)

    def Assistant(self, content):
        """
        Add a 'assistant' role message to the conversation.
        """
        self.Add('assistant', content)

    def User(self, content):
        """
        Add a 'user' role message to the conversation.
        """
        self.Add('user', content)

    def _Send0(self, **kw):
        """
        Send the conversation, returning the response. This will not
        append the response to the list of messages of the conversation.

        All chat operations will end up calling this basic function.

        kw will override any arguments in self.args (temperature, etc)
        """
        # Do deep copy to make sure prompts_and_responses are all unique.
        args = copy.deepcopy(self.args) | kw
        args['messages'] = copy.deepcopy(self.messages)

        # Call the OpenAI chat API.
        response = openai.ChatCompletion.create(**args)

        # Save the prompt and the response from the network.
        # self.prompts_and_responses.append( (args, response) )
        # use list instead of tuple so json.load gives equivalent.
        self.prompts_and_responses.append( [args, response] )
        #
        return response

    def Send(self, **kw):
        """
        Send the conversation, append the response message to the
        conversation (messages variable), and return the response.

        response = OpenAIObject chat.completion (JSON dict)
        """
        # Append the response to the conversation.
        response = self._Send0(**kw)
        # Need to convert this to python dict object
        # otherwise it is a JSON type of object.
        response_message = dict(response['choices'][0]['message'])
        self.messages.append(response_message)
        return response

    def _Chat0(self, **kw):
        """
        Same as Send() but return the response as a basic string
        of the content.
        """
        response = self.Send(**kw)
        return response['choices'][0]['message']['content'].strip()

    def UserChat(self,user_content, **kw):
        """
        Append content as a 'user' role to the conversation,
        then send the conversation to the AI,
        then append the response to self.messages (as 'assistant' role)
        return the response message as a string.
        """
        self.User(user_content)
        return self._Chat0(**kw)
    def SystemChat(self,system_content, **kw):
        """
        Same as UserChat but use 'system' as the role.
        """
        self.System(system_content)
        return self._Chat0(**kw)
    def AssistantChat(self,assistant_content, **kw):
        """
        Same as UserChat but use 'assistant' as the role.
        """
        self.Assistant(assistant_content, **kw)
        return self._Chat0(**kw)
    def Chat(self,user_content, **kw):
        """
        Shortcut for UserChat() method.
        """
        return self.UserChat(user_content, **kw)

    def JSONDump(self):
        """
        Dump JSON string representation of the conversation.

        The resulting string can be loaded with json.loads() :
            c = Chat("...")
            jstr = c.JSONDump()
            d = json.loads(jstr)
            c2 = Chat(**d)
        """
        # Use the compact form for separators.
        return json.dumps(self.__dict__, separators=(',',':'))
##############################################################################

##############################################################################
class ChatDatabase:
    r"""
    Stores multiple OpenAI chat conversations.

    Allows for saving Chat conversations to a database on disk.
    Works similar to a dict()
    """
    def __init__(self,db_filename, table_name='chats'):
        self.db_filename = db_filename
        self.table_name = table_name
        self.con = sql.connect(db_filename)
        self.cur = self.con.cursor()
        try:
            self.cur.execute(f"CREATE TABLE {self.table_name}(name TEXT PRIMARY KEY,json TEXT)")
            self.con.commit()
        except sql.OperationalError as e:
            # Assume the table already exists.
            # print("Unable to create table: OperationalError: {}".format(e))
            pass
    def __del__(self):
        # Note sure if this is necessary but do it anyways.
        # self.con.commit()
        # self.cur.close()
        self.con.close()
    def __len__(self):
        # Could make this very slightly faster.
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
        returns a string containing

        the names of conversations,
        the number of messages in each.
        """
        s = io.StringIO()
        s.write("ChatDatabase(")
        for (name, chat) in self.items():
            s.write(f"'{name}': {len(chat)}, ")
        s.write(")")
        return s.getvalue()
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
        if not chat.messages and not chat.prompts_and_responses:
            return
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

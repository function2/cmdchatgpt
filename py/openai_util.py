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

Chat() object keeps a conversation.
ChatDatabase() object keeps a database of many conversations.
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
    Conversation can be ANSI highlighted for terminal,
       converted to JSON string,
       ...
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
        # CODE_START_TXT = '```'
        # CODE_END_TXT = '```'
        CODE_START_TXT = '「'
        CODE_END_TXT = ' 」'
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
        args and past prompts which got here don't matter.
        """
        return self.messages == o.messages

    def StrTerm(self):
        """
        Return string representation of the conversation,
        use ANSI escape sequences to color the output for terminal.
        """
        colors = self.colors

        if not self:
            return "<empty conversation>"

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
        # This replacement string highlights keyword, and then
        # restarts assistant highlighting.
        keyword_sub_str = f"`{colors.ENDC}{colors.KEYWORD_BEGIN}\\1{colors.ENDC}{colors.ASSISTANT_CONTENT}`"

        # Build return string.
        s = io.StringIO()
        # s = f"{colors.HEADER}AI Chat conversation:{colors.ENDC}\n"
        for m in self.messages:
            role = m['role']
            content = m['content'].strip()

            # Print 'asterisk' for role.
            s.write(f"{colors.ROLE_HEADER_COLOR}{colors.ROLE_HEADER}{colors.ENDC} ")
            # Print role and content.
            # Use different colors, highlighting depending on role.
            if role == 'user':
                s.write(f"{colors.USER_ROLE}{role}{colors.ENDC}\n")
                s.write(f"{colors.USER_CONTENT}{content}{colors.ENDC}\n")

            elif role == 'assistant':
                s.write(f"{colors.ASSISTANT_ROLE}{role}{colors.ENDC}\n")

                # Look for code sections in content (for syntax highlighting)
                last_end = 0 # Position of end of last code section.
                for m in code_regex.finditer(content):
                    # here m is re.Match object.
                    g = m.groups()
                    before = g[0]
                    lang = g[1] # language of code section (if any)
                    code = g[2]
                    # text before code section.
                    # Highlight keywords in this text section.
                    newbefore = keyword_regex.sub(keyword_sub_str,before)

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
                last_text = keyword_regex.sub(keyword_sub_str, content[last_end:])
                s.write(f"{colors.ASSISTANT_CONTENT}{last_text}{colors.ENDC}\n")

            elif role == 'system':
                s.write(f"{colors.SYSTEM_ROLE}{role}{colors.ENDC}\n")
                s.write(f"{colors.SYSTEM_CONTENT}{content}{colors.ENDC}\n")
        # s += f"{colors.ENDER}End of conversation{colors.ENDC}\n"
        return s.getvalue()

    def __str__(self):
        """
        Return string representation of the conversation.
        """
        return self.StrTerm()

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
    """
    def __init__(self,db_filename, table_name='chats'):
        self.db_filename = db_filename
        self.table_name = table_name
        self.con = sql.connect(db_filename)
        self.cur = self.con.cursor()
        try:
            self.cur.execute("CREATE TABLE {}(name TEXT PRIMARY KEY,json TEXT)".format(self.table_name))
            self.con.commit()
        except sql.OperationalError as e:
            print("Unable to create table: OperationalError: {}".format(e))
    def __del__(self):
        # Note sure if this is necessary but do it anyways.
        self.con.commit()
        self.cur.close()
        self.con.close()
    def AddChat(self,name,chat):
        """
        Add a chat conversation to the table.

        This will replace the conversation if one named 'name' already exists.
        """
        # try:
        self.cur.execute("INSERT OR REPLACE INTO {}(name,json) VALUES (?,?)".format(self.table_name),
                         (name, chat.JSONDump()))
        # except sql.IntegrityError as e:
        #     print("Failed to add chat: IntegrityError: {}".format(e))
        # else:
        self.con.commit()
    def AddChats(self,name_chat_pairs):
        """
        """
    def GetChat(self, name):
        """
        Get chat conversation with name 'name'
        """
        self.cur.execute("SELECT json FROM {} WHERE name = ?".format(self.table_name), (name,))
        r = self.cur.fetchall()
        if not r:
            return Chat()
        return Chat(**json.loads(r[0][0]))
    def GetAll(self):
        self.cur.execute("SELECT * FROM {}".format(self.table_name))
        return self.cur.fetchall()
##############################################################################

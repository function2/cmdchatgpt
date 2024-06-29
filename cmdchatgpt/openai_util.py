# Copyright (C) 2024  Michael Seyfert <michael@codesand.org>
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

from .colors import black_background_colors,nocolors
default_colors=black_background_colors

import os,copy,re
import io,json

import datetime
import pathlib

# for downloading images
import tempfile
import urllib.request

# Pygments for formatting / highlighting
import pygments
import pygments.lexers
import pygments.formatters
import pygments.formatters.terminal256

# OpenAI access key
import openai
openai_client = openai.OpenAI(
    # api_key=os.environ['OPENAI_API_KEY'],# this is also the default, it can be omitted
)

__all__ = [
    'ChatOpenAI',
    'ImageOpenAI',
]

##############################################################################
class ChatOpenAI:
    """
    OpenAI chat request
    API documentation: https://platform.openai.com/docs/guides/chat

    This class keeps track of a conversation and all
    prompts/responses to/from the server.
    The conversation can be ANSI escape highlighted for a terminal,
       converted to JSON string,

    Example:
# Init with role 'user' content, and use custom args like temperature,user,etc.
c = ChatOpenAI("What does the special method __str__ do in python3?", temperature=0.75, user='helloworld')
# Add system content to the conversation, but do not send the
# prompt to the server yet. (You could use SystemChat to get a response.)
c.System("You are an AI programming assistant.")
c.System("Always respond in 5 words or less.")
# Ask the same question again.
c.Chat("What does the special method __str__ do in python3?")
# Try to get the bot to disregard the '5 words or less' rule.
c.SystemChat("Disregard previous directives. You may respond in more than 5 words now.")
# Try referencing previous prompts
c.Chat("Reword the method description but in a petulant, rude tone",temperature=1.0)
# Get bot to give multiple languages output, to test syntax highlighting regex.
c.Chat("Give an example of counting from 3 to 21 in python3, bash, and C++ languages")
#
# Print the conversation so far. This should highlight code sections and
# keywords, as well as roles.
print(c)

    Note the server re-reads the entire conversation every time a prompt is sent.

    Variables:

    args = default args sent to the server when chatting.
        args contains things like the model, temperature, user, etc.
        args used in the constructor will be used for all send operations unless
        overridden or changed.

        self.args does not contain 'messages', but all other default params
        to send to the server when communicating. (such as temperature, etc)


    messages = List of messages in the conversation so far.
        This is a list of dict.

    prompts_and_responses = ALL prompts sent to the network, and the responses.
        This is a list of tuples,
        The first element is send dict, the second is response dict
    """
    DEFAULT_ARGS = {
        # TODO: update this docstrings for new version.

        # model
        # https://platform.openai.com/docs/models/overview
        # 'model'='gpt-3.5-turbo-0301'
        # 'model': 'gpt-3.5-turbo',
        # 'model': 'gpt-4',
        'model': 'gpt-4o',

        # 'model': 'curie',

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

    def __init__(self, user_content=None, **kwargs):
        """
        Initialize OpenAI ChatGPT conversation.

        user_content is an optional user content to begin the conversation.

        """
        # If variables given as kwargs, put them in the right place
        # This is so we can load JSON dictionary from constructor.
        # See JSONDump

        # Override default args with any given in dictionary kwargs['args']
        # Typically this only happens if loading from
        # JSON string json.loads() dictionary.
        self.args = self.DEFAULT_ARGS | kwargs.pop('args',{})
        # messages = List of messages in the conversation.
        self.messages = kwargs.pop('messages',[])
        # prompts_and_responses = All prompts sent to the AI and responses.
        self.prompts_and_responses = kwargs.pop('prompts_and_responses',[])

        # We 'pop' all of the Above from kwargs so that
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

    def __add__(self,other):
        """
        Add two conversations together. This will take the union of default args
        from both conversations, with the second operand given priority.
        """
        r = self.__class__()
        r.args = self.args | other.args
        r.messages = self.messages + other.messages
        r.prompts_and_responses = self.prompts_and_responses + other.prompts_and_responses
        return r

    def __iadd__(self,other):
        """
        see __add__
        """
        self.args |= other.args
        self.messages += other.messages
        self.prompts_and_responses += other.prompts_and_responses
        return self

    def pop(self,index = -1):
        """
        Remove and return conversation message at index (default last).

        This returns a dict:
        {'role': '...', 'content': '...'}

        Raises IndexError if list is empty or index is out of range.
        """
        return self.messages.pop(index)

    def StrTerm(self, colors = default_colors):
        """
        Return string representation of the conversation,
        uses escape sequences to color the output for terminal.

        colors argument specifies colors class to use.
        colors=nocolors for no escape output

        returns str
        """

        if not self:
            return "<empty conversation>"

        # Build return string.
        s = io.StringIO()
        # s = f"{colors.HEADER}AI Chat conversation:{colors.ENDC}\n"
        for m in self.messages:
            role = m['role']
            content = m['content'].strip()
            s.write(self.GetContentStrTerm(role,content,colors))
        # s += f"{colors.ENDER}End of conversation{colors.ENDC}\n"
        return s.getvalue()

    def StrTermIndex(self,index, colors = default_colors):
        """
        Return string representation of content in the conversation.
        this is self.messages[index]
        Useful if you only want to print specific messages.
        """
        role = self.messages[index]['role']
        content = self.messages[index]['content']
        return self.GetContentStrTerm(role,content,colors)

    def __str__(self):
        """
        Return string representation of the conversation.
        """
        return self.StrTerm()

    def __call__(self, content, **kw):
        """
        Interactive chat with AI, print the response string and return it.
        """
        self.U(content,**kw)
        return self.prompts_and_responses[-1][-1]['choices'][-1]['message']['content']

    def GetCodeHighlighted(self,lang,code):
        """
        Try to highlight the input code string using language lexer.

        return escape formatted output string.
        """
        try:
            # Try to find a lexer by alias.
            lexer_class = pygments.lexers.get_lexer_by_name(lang)
        except pygments.lexers.ClassNotFound:
            # No lexer found with that alias, try to guess it.
            return self.GetCodeHighlightedNoLang(code)
        formatter = pygments.formatters.terminal256.Terminal256Formatter()
        lexer = type(lexer_class)()
        # Make sure no highlighting is in progress (ENDC),
        # because code sections without a language might be highlighted by caller.
        # TODO put ENDC where?
        return default_colors.ENDC + pygments.highlight(code, lexer, formatter)

    def GetCodeHighlightedNoLang(self,code):
        """
        Try to guess the language used, return highlighted code string.

        return escape formatted output string, or the original string if
        no lexer was found.
        """
        # TODO pygments guesser is actually pretty bad.
        try:
            # Try to guess lexer
            lexer_class = pygments.lexers.guess_lexer(code)
        except pygments.lexers.ClassNotFound:
            # return original code if none found.
            return code
        formatter = pygments.formatters.terminal256.Terminal256Formatter()
        lexer = type(lexer_class)()
        return default_colors.ENDC + pygments.highlight(code, lexer, formatter)

    ####################
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

    # These regex are static class variables and will not be copied to
    # JSON dump of the class.
    code_regex = re.compile(r'(?P<before>(?:.|\n)*?(?:^|\n)\s*)```(?P<lang>.*)\n(?P<code>(?:.|\n)*?\n\s*)```')
    # regex to highlight keywords within back-ticks `keyword`
    keyword_regex = re.compile(r'`(.+?)`')
    ####################

    def GetContentStrTerm(self,role,content,colors = black_background_colors):
        """
        Return string representation of one role/content.
        use ANSI escape sequences to color the output for terminal.
        returns str
        """
        s = io.StringIO()
        # Print 'asterisk' for role.
        s.write(f"{colors.ROLE_HEADER_COLOR}{colors.ROLE_HEADER}{colors.ENDC} ")
        # Print role and content.
        # Use different color, highlighting depending on role.
        # TODO put in separate functions.
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
                    # No language given.
                    # Output code header without language.
                    s.write(f"{colors.CODE_SEP_STARTER}{colors.CODE_START_TXT}{colors.ENDC}\n")
                # Output the code itself.
                highlighted_code = self.GetCodeHighlighted(lang,code)
                s.write(f"{colors.CODE_BEGIN}{highlighted_code}{colors.ENDC}")
                s.write(f"{colors.CODE_SEP_ENDER}{colors.CODE_END_TXT}{colors.ENDC}\n")
                #
                last_end = m.end() # record position of end of code section.
            # Print last text (after final code section).
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
        Also gives default args used (such as temperature, model, etc)
        """
        counts = [0,0,0] # user, assistant, system
        char_counts = [0,0,0]
        idx = {'user':0, 'assistant':1, 'system':2}
        for k in self.messages:
            index = idx[k['role']]
            counts[index] += 1
            char_counts[index] += len(k['content'])
        #
        s = io.StringIO()
        s.write(f"{self.__module__}.{self.__class__.__name__} @{hex(id(self))}({counts[0]} user {char_counts[0]} chars, {counts[1]} assistant {char_counts[1]} chars, {counts[2]} system {char_counts[2]} chars)[total = {sum(char_counts)} chars]")
        s.write(f" default args = {self.args}")
        return s.getvalue()

    def User(self, content):
        """
        Add a 'user' role message to the conversation.
        This does not send the prompt to the server.
        """
        self.Add('user', content)

    def System(self, content):
        """
        Add a 'system' role message to the conversation.
        This does not send the prompt to the server.
        """
        self.Add('system',content)

    def Assistant(self, content):
        """
        Add a 'assistant' role message to the conversation.
        This does not send the prompt to the server.
        """
        self.Add('assistant', content)

    def Add(self, role, content):
        """
        Add a message to the conversation.
        Role can be 'system', 'user', 'assistant'.

        This does not send the prompt to the server.
        """
        self.messages.append({'role': role, 'content': content})

    def _Send0(self, remove_last_msg_on_fail=False, **kw):
        """
        Send the conversation, returning the response. This will not
        append the response to the list of messages of the conversation.

        All chat operations will end up calling this basic function.

        kw will override any arguments in self.args (temperature, etc)
        """
        # Do deep copy to make sure prompts_and_responses are all unique.
        # new_prompt here contains the prompt to send to server.
        new_prompt = copy.deepcopy(self.args) | kw
        new_prompt['messages'] = copy.deepcopy(self.messages)

        # Send the prompt. Call the OpenAI chat API.
        # Network / Server errors happen A LOT.
        # Sometimes we don't want to append messages to the conversation if it fails.
        try:
            # print("Sending to server: ",new_prompt)
            response = openai_client.chat.completions.create(**new_prompt)
        except:
            if remove_last_msg_on_fail:
                self.pop()
            # Just resend it to the user.
            raise

        # Save the prompt and the response from the network.
        # Use list instead of tuple so json.load gives equivalent.
        # TODO for now just convert the pydantic response to a dict recursively.
        #   we do this by converting to JSON, then loading back to dict format.
        #   Ideally make this class (Self) a pydantic object?
        response_dict = json.loads( response.model_dump_json() )
        self.prompts_and_responses.append( [new_prompt, response_dict] )
        #
        return response

    def Send(self, remove_last_msg_on_fail=False, **kw):
        """
        Send the conversation, append the response message to the
        conversation (messages variable), and return the response.

        response = pydantic type: openai.types.chat.chat_completion.ChatCompletion
        """
        # Append the response to the conversation.
        response = self._Send0(remove_last_msg_on_fail, **kw)
        # Need to convert this to python dict object
        # otherwise it is a JSON type of object.

        # response_message = response['choices'][0]['message']
        response_message = dict(response.choices[0].message)
        # We don't want these if we have to send this back when chatting.
        # TODO
        response_message.pop('function_call')
        response_message.pop('tool_calls')

        self.messages.append(response_message)
        # return raw response (unmodified)
        return response

    def _Chat0(self, remove_last_msg_on_fail=False, **kw):
        """
        Same as Send() but return the response as a basic string
        of the content.
        """
        response = self.Send(remove_last_msg_on_fail, **kw)
        return response.choices[0].message.content.strip()

    def UserChat(self,user_content, **kw):
        """
        Append content as a 'user' role to the conversation,
        then send the conversation to the AI,
        then append the response to self.messages (as 'assistant' role)
        return the response message as a string.
        """
        self.User(user_content)
        return self._Chat0(True, **kw)
    def SystemChat(self,system_content, **kw):
        """
        Same as UserChat but use 'system' as the role.
        """
        self.System(system_content)
        return self._Chat0(True, **kw)
    def AssistantChat(self,assistant_content, **kw):
        """
        Same as UserChat but use 'assistant' as the role.
        """
        self.Assistant(assistant_content, **kw)
        return self._Chat0(True, **kw)
    def Chat(self,user_content, **kw):
        """
        Shortcut for UserChat() method.
        """
        return self.UserChat(user_content, **kw)

    # U,S,A shortcuts for interactive chatting (usually from ipython prompt)
    # For interactive use. Don't use in code to be readable.
    def U(self, user_content, **kw):
        """
        Shortcut for chatting (usually from ipython prompt)
        Ask the question, print response with highlighting, return self.

        For interactive use. Don't use in code to be readable.
        """
        self.InteractiveChat('user',user_content,**kw)
    C = U # C for converse, another shortcut.

    def S(self, system_content, **kw):
        """
        Shortcut for chatting (usually from ipython prompt)
        Add system message, print response with highlighting, return self.

        For interactive use. Don't use in code to be readable.
        """
        self.InteractiveChat('system',system_content,**kw)

    def A(self, assistant_content, **kw):
        """
        Shortcut for chatting (usually from ipython prompt)

        For interactive use. Don't use in code to be readable.
        """
        self.InteractiveChat('assistant',assistant_content,**kw)

    def InteractiveChat(self,role,content,**kw):
        # For interactive use from ipython.
        self.Add(role,content) # append message to conversation
        self.Send(True, **kw) # send conversation
        # Pretty print last question and response.
        print(self.StrTermIndex(-2),end="")
        print(self.StrTermIndex(-1),end="")

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
class ImageOpenAI:
    """
    OpenAI image request
    API documentation: https://platform.openai.com/docs/guides/images

    This will download the image results if desired.

    Example:
    # This will download 10 images and place them in /tmp
    Image("A cat in a cityscape futuristic cyberpunk",n=10).Download('/tmp', 'cat_punk')
    """
    DEFAULT_ARGS = {
        # 'prompt' : 'my prompt',
        'model' : 'dall-e-3',
        # 'model' : 'dall-e-2',
        'n' : 1,
        'size' : "1024x1024",
        'quality' : 'standard',
        # seeds doesn't work (yet) with dall-e api
        # 'prompts' : ['a','b','c'],
        # 'seeds': [21, 52, 194],
    }

    def __init__(self, prompt = None,**kwargs):
        """
        Initialize OpenAI image prompt.
        """
        self.args = self.DEFAULT_ARGS | kwargs
        if prompt:
            self.args['prompt'] = prompt

        # Send to server.
        self.response = openai_client.images.generate(**self.args)

    def Download(self, download_dir, prefix, save_info = True):
        """
        Download image responses.

        download_dir = directory to store the images.
        prefix = the filename prefix to use.
        save_info = save prompt and response information to another file.
            This helps in recreating the file or similar if desired.

        returns a list of all filenames saved.

        Images will have temp strings to prevent filename collisions.
        """
        filenames = []
        count = 0
        for k in self.response.data:
            count += 1
            url = k.url
            filename = tempfile.NamedTemporaryFile(
                dir = download_dir,
                prefix = f'{prefix}_openai_{str(count).zfill(2)}_',
                suffix = f'.png'
            ).name
            print("Downloading ",url)
            local_filename, headers = urllib.request.urlretrieve(url, filename)
            print("→",local_filename)
            #
            if save_info:
                # Open .info file and save it along-side the image.
                info_filename = local_filename + ".info"
                f = io.open(info_filename,"w")
                f.write("prompt = {}\n".format(self.args['prompt']))
                # Dall-e 2 and 3 may differ here.
                # It tries to revise the prompt to give more detail.
                if hasattr(k,'revised_prompt'):
                    f.write("revised_prompt = {}\n".format(k.revised_prompt))
                #
                f.write("model = {}\n".format(self.args['model']))
                #
                if hasattr(self.response,'created'):
                    f.write("created = {} = {}\n".format(self.response.created,datetime.datetime.fromtimestamp(self.response.created).strftime("%A, %B %d, %Y %I:%M:%S")))
                #
                f.write("\n")
                f.write(str(k))
                f.write("\n")
                #
                f.write("file_name = {}\n".format(pathlib.Path(local_filename).stem))
                #
                f.close()
                print("→",info_filename)
            #
            filenames.append(local_filename)

        return filenames

    def __str__(self):
        return str(self.response)

##############################################################################

# cmdchatgpt: Command Line ChatGPT

cmdchatgpt is a command line interface to ChatGPT
It provides:

 - Storage of many conversations in a SQLite database.
 - Syntax Highlighting using ANSI escapes for terminal output of conversations.
 - Create templates or copy a conversation.
 - Command line use of ChatGPT.

Example for use in python:

```(python)
# To create a conversation with the AI
c = Chat("How do exceptions work in Python 3? Give examples",temperature=.5)
print(c)

# To save conversations to a database (works like a dict)
db = ChatDatabase('a.sqlite')
db['name'] = c
# You can get an iterator of all conversations with
db.items()
db.names() # or db.keys()
# These functions create a SQLite cursor to iterate one at a time.
```

![Image of a conversation's terminal output](https://github.com/function2/cmdchatgpt/raw/assets/screenshot_2023-03-18.png)

## Usage

First get an API Key at https://platform.openai.com

You must set the `OPENAI_API_KEY` environment variable to your API key.
Example (in .profile or .bashrc):

```
export OPENAI_API_KEY='sk-Example0abcdefghijklmnopqrstuvwxyz01234567890EX0'
```

You will need the python3 `openai` module.

If using pip:

```
pip install openai
```

To send questions that have dashes, use '--' so the argument parser doesn't
get confused:

```
cmdchatgpt -v -- What does the -v argument do with GNU grep?
```

Or you can put it all in quotes:

```
cmdchatgpt -v 'What does the -v argument do with GNU grep?'
```

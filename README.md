# cmdchatgpt: ChatGPT from terminal. Syntax highlighting. SQLite storage of conversations.

cmdchatgpt is a python / command line interface to ChatGPT and image generation tools
It provides:

 - Syntax Highlighting for terminal output of conversations.
 - Storage of many conversations in a SQLite database.
 - Create templates or copy a conversation.
 - Command line use of ChatGPT.
 - Image creation and downloading.

Example for use in python:

```python
from cmdchatgpt import *
# Create a conversation
c = Chat("How do exceptions work in Python 3? Give examples", temperature=.5)
print(c) # Pretty print with escapes.

# To save conversations to a database
db = ChatDatabase('a.sqlite')
# ChatDatabase works like a dict
db['name'] = c
# You can get an iterator of all conversations with
db.items()
db.names() # or db.keys()
# These functions create an iterator with cursor to read one at a time.

# To download images
i = Image("A balloon in a flower field",n=10)
i.Download('/tmp', 'balloon')
# This will save 10 images to the tmp directory.
```

![Image of a conversation's terminal output](https://github.com/function2/cmdchatgpt/raw/assets/screenshot_2023-03-18.png)

## Usage

First get an API Key at https://platform.openai.com

You must set the `OPENAI_API_KEY` environment variable to your API key.
Example (in .profile or .bashrc):

```
export OPENAI_API_KEY='sk-Example0abcdefghijklmnopqrstuvwxyz01234567890EX0'
```

You will need the python3 `openai` and `pygments` modules.

If using pip:

```
pip install openai pygments
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

# my scripts for AI tools for terminal usage (ipython or shell).

This repo contains my interface for AI tools. Features:

 - Syntax Highlighting for terminal output of conversations.
 - Storage of many conversations in a SQLite database.
 - Search through past conversations.
 - ipython tab completion of stored conversations.
 - Command line use of ChatGPT and other AI tools.
 - Image creation and downloading from terminal.
   (If the terminal supports urls you can just click them.)

Example for use in python:

```python
from cmdchatgpt import *
# Create a conversation
c = Chat("How do exceptions work in Python 3? Give examples", temperature=.5)
print(c) # Pretty print with escapes.
c('and how does subprocess.Popen work? With an example')

# Vision API
c.ChatImageURL("What type of insect is this?", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Papilio_machaon_Mitterbach_01.jpg/1920px-Papilio_machaon_Mitterbach_01.jpg")
c.ChatImage("What is this?", "./Downloads/img.jpg")

# To save conversations to a database
db = ChatDatabase('a.sqlite')
# ChatDatabase works like a dict
db['name'] = c
# You can get an iterator of all conversations with
db.items()
db.names() # or db.keys()
# These functions create an iterator with cursor to read one at a time.

# To generate and download images
i = Image("A cat in a cityscape futuristic cyberpunk")
i.Download('/tmp', 'cat_punk')
# This will save an image to the /tmp directory.
```

![Image of a conversation terminal output](https://github.com/function2/cmdchatgpt/raw/assets/screenshot_2023-10-27.png)
![AI generated image cat punk](https://github.com/function2/cmdchatgpt/raw/assets/cat_punk_openai_05_kdm6md6r.jpg)

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

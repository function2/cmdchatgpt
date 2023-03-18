# cmdchatgpt: Command Line ChatGPT

cmdchatgpt is a command line interface to ChatGPT
It provides:

 - Syntax Highlighting using ANSI escapes for terminal.
 - Storage of many conversations in a SQLite database.

![Image of a conversation's terminal output](https://github.com/function2/cmdchatgpt/raw/assets/screenshot_2023-03-18.png)

## Usage

First get an API Key at https://platform.openai.com

You must set the `OPENAI_API_KEY` environment variable to your API key.
Example (in .profile or .bashrc):

```
export OPENAI_API_KEY='sk-exampleblahblahblah'
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

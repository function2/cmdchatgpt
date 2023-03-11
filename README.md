# cmdchatgpt
ChatGPT from the command line. Syntax highlighting and save multiple conversations.

You must set the OPENAI_API_KEY environment variable to your API key.
Example (in .profile or .bashrc):
export OPENAI_API_KEY='sk-exampleblahblahblah'

You will need the python3 `openai` module.
If using pip:
pip install openai

To send questions that have dashes, use '--' so the argument parser doesn't
get confused:
cmdchatgpt -v -- What does the -v argument do with GNU grep?
Or you can put it all in quotes:
cmdchatgpt -v 'What does the -v argument do with GNU grep?'

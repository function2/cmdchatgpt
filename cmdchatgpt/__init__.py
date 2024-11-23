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
cmdchatgpt

Store conversations and chat with AI.
"""

__uri__ = "https://github.com/function2/cmdchatgpt"
__version__ = "0.1"

from .database import *
# For now we only have OpenAI chatbot.
from .openai_util import *

__all__ = [
    'Chat', # default Chat bot
    'Image', # default Image generation
    'GPT','gpt',
    'GPT_Solver','gpt_solver',
] + database.__all__ + openai_util.__all__

# For now we only have OpenAI, make it the default.
Chat = ChatOpenAI
Image = ImageOpenAI

def GPT(prompt, **kwargs):
    """
    Given a prompt and args, print ChatBot response.
    Returns constructed Chat object to continue the conversation if desired.

    Example:
    conv = gpt('code to print first 13 prime numbers',temperature=0.73)
    conv.U("Give the code in another language", temperature = 0.05)
    """
    conversation = Chat(prompt,**kwargs)
    print(conversation)
    return conversation
gpt = GPT

def GPT_Solver(prompt, **kwargs):
    """
    Same as GPT but oriented towards logic problems.
    """
    conversation = Chat(prompt,model = 'o1-preview')
    print(conversation)
    return conversation
gpt_solver = GPT_Solver

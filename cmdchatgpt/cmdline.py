"""
cmdchatgpt

Command line interface.
"""

################################################################################
# Freeze command line for now.
# def Go():
#     parser = argparse.ArgumentParser(
#         prog='cmdchatgpt',
#         description='Command line ChatGPT',
#         # epilog='Text at the bottom of help',
#     )
#     # mutually exclusive args
#     # group = parser.add_mutually_exclusive_group()
#     # group.add_argument("-v", "--verbose", action="store_true")
#     # group.add_argument("-q", "--quiet", action="store_true")

#     # This allows multiple -v -vv -vvv etc.
#     parser.add_argument(
#         "-v", "--verbose", help='increase output verbosity (use up to 2 times)',
#         action="count", default=0,
#         dest='verbosity',
#     )
#     # parser.add_argument(
#     #     "-i", "--interactive", help='interactive mode',
#     #     action="store_true",
#     # )
#     parser.add_argument(
#         "-c", "--chat",
#         help='name of the conversation (or a new one is created)',
#         type=str,metavar="conversation",
#     )
#     parser.add_argument(
#         "-r", "--role",type=str,default='u',
#         choices=('u','a','s','user','assistant','system'),
#         help='role (user is default)',
#     )
#     parser.add_argument(
#         "-n", "--no-ansi",help='Disable ansi escape sequences on output',
#         action="store_true",
#     )
#     parser.add_argument(
#         "content",nargs='*',help='content string (if not given read from stdin)',type=str,
#     )
#     args = parser.parse_args()
#     # if args.interactive:
#     #     print("Interactive mode selected.")
#     if args.verbosity >= 2: # -vv display running python file path+name
#         print(f"Running '{__file__}'")
#     #
#     # Get home directory
#     #
#     home_dir = os.environ['HOME']
#     app_dir = os.path.join(home_dir, ".cmdchatgpt")
#     if args.verbosity >= 1:
#         print(f"app_dir = {app_dir}")
#     # if not os.path.exists(app_dir):
#     os.makedirs(app_dir, exist_ok=True)
#     #
#     # Open or create the database.
#     #
#     database_path = os.path.join(app_dir,"a.sqlite")
#     if args.verbosity >= 1:
#         print(f"database_path = {database_path}")
#     db = ChatDatabase(database_path)
#     if not args.chat:
#         args.chat = "default" # TODO for now.
#     chat = db[args.chat]
#     if chat:
#         print("Conversation so far:")
#         print(chat)
#     #
#     # Get role and content
#     #
#     role = args.role
#     if role[0] == 'u':
#         role = 'user'
#     elif role[0] == 's':
#         role = "system"
#     elif role[0] == 'a':
#         role = "assistant"
#     content = ""
#     if args.content:
#         content = " ".join(args.content)
#     else:
#         # No content given,
#         # Read from stdin until EOF.
#         # TODO check if reading from pipe or terminal input.
#         # TODO readline library?
#         print(f"Enter content for conversation '{args.chat}', role {role}:")
#         content = sys.stdin.read().strip()
#     #
#     # if args.verbosity >= 1:
#     #     print(f"role = '{args.role}'")
#     #     print(f"content = '{content}'")
#     #
#     if not content:
#         return
#     if args.verbosity >= 1:
#         print(f"Using model {chat.args['model']}")
#     if role[0] == 'u':
#         chat.User(content)
#     elif role[0] == 's':
#         chat.System(content)
#     elif role[0] == 'a':
#         chat.Assistant(content)
#     print("Sending conversation...")
#     response = chat.Send()
#     db[args.chat] = chat # Store chat with response in the database
#     prompt_tokens = response['usage']['prompt_tokens']
#     completion_tokens = response['usage']['completion_tokens']
#     total_tokens = response['usage']['total_tokens']
#     print(f"Total tokens used: {total_tokens}  (prompt: {prompt_tokens}, completion: {completion_tokens})")
#     if args.verbosity >= 2:
#         print("sent args=")
#         print(pprint.pformat(chat.prompts_and_responses[-1][0]))
#         print("response=")
#         print(pprint.pformat(chat.prompts_and_responses[-1][1]))
#     # Print the result
#     print(chat.StrTermIndex(-2) + chat.StrTermIndex(-1))

# if __name__ == "__main__":
#     Go()

import discord
import textwrap
from enum import Enum
from random import randint

##############GAME VARIABLES################
class Game_State(Enum):
    IDLE = 1
    HOSTING = 2
    GAME_START = 3
    MID_GAME = 4
    VOTING = 5
    GAME_ENDING = 6

class Player():
    def __init__(self, member):
        self.member = member
        self.is_chameleon = False
        self.voted = False
        self.final_vote = False
        self.vote_count = 0


rules_text = """CHAMELEON GAME RULES
1. There will be ONE chameleon assigned among the players
2. The chameleon wil be sent a dm saying "You are the Chameleon!", everyone else will get a coordinate to figure out the secret word!
3. Take turns one by one, and say ONE WORD to describe the secret word. Choose it carefully, as you don't want to reveal the word to the chameleon!
4. After everyone had their turn, vote one person you think is the chameleon after debating.
5. THE REVEAL!! If the person who got the most votes is the chameleon, they get one chance to guess the word. If the chaemeleon gets the word, the chameleon wins!
   If the person was not the chameleon, the chameleon wins!
"""
commands_text = """CHAMELEON BOT COMMANDS
!host: Start hosting a game!
!join: Join a game that's getting hosted!(Only works after !host)
!start: If everyone joined, start the game!
!lame: If you don't like the word board, type lame!
!vote @user: Command used during voting phase
!guess "your guess": Command for the chameleon guessing!
"""

# topics = ['fruits']
wordbank = {'fruits': [['Apple', 'Banana', 'Cherry', 'Date'], 
                       ['Blueberry','Fig','Grape','Honeydew'],
                       ['Kiwi','Lemon','Mango','Nectarine'], 
                       ['Orange', 'Papaya', 'Quince', 'Raspberry']],
            'Ocean Life': [['Dolphin','Jellyfish','Sea Turtle', 'Octopus'],
                           ['Coral','Seahorse','Starfish','Shark'],
                           ['Whale','Manta Ray','Squid','Sea Urchin'],
                           ['Anemone','Clownfish','Seaweed','Crab']]}
topics = list(wordbank.keys())

state = Game_State.IDLE
topic = None
secret = None
players = []
player_count = 0



###############GAME FUNCTIONS#################
def choose_keyword():
    """
    function for generating the secret word
   arguments: none
   returns: (topic, secret word,coord) pair
   """
    topic_word = topics[randint(0,len(topics)-1)]
    row_code = "ABCD"
    row_num = randint(0,3)
    col_num = randint(0,3)
    # topic_word = 'fruits'
    keyword = wordbank[topic_word][col_num][row_num]
    coords = row_code[row_num]+str(col_num+1)
    return (topic_word, keyword, coords)

def new_keyword(keyword):
    """
    function for refreshing the secret word
   arguments: old keyword
   returns: new (topic word, secret word,coord) pair
   """
    old_keyword = keyword
    new_keys = choose_keyword()
    while(old_keyword == new_keys[1]):
        new_keys = choose_keyword()
    return new_keys

def guess_is_correct(message):
    """
    function for checking if the guess is correct
   arguments: plain text of the chat log including the guess
   returns: bool
   """
    if secret in message:
        return True
    else:
        return False


"""function for creating the ASCII art grid for the topic cards
   argument: topic category of the keyword
   returns: printable string of the ASCII art version of the board"""


def ascii_word_grid(topic, max_width=12):
    """
    Creates an ASCII grid with:
      - Auto-wrapped words
      - Auto-sized cell width based on wrapped lines
      - Full outer border
      - Returned as a printable string

    Args:
        topic (str): Title text for the grid
        words (list[str]): 16 words for the 4×4 grid
        max_width (int): Maximum width before wrapping each cell's text

    Returns:
        str: The formatted ASCII grid
    """

    grid = wordbank[topic]
    words = grid[0] + grid[1] + grid[2] + grid[3]

    if len(words) != 16:
        raise ValueError("You must provide exactly 16 words.")
            
    columns = ["A", "B", "C", "D"]
    rows = ["1", "2", "3", "4"]

    # Wrap all words
    wrapped_words = [textwrap.wrap(w, max_width) or [""] for w in words]

    # Determine cell height (max number of lines in any cell)
    cell_height = max(len(w) for w in wrapped_words)

    # Determine cell width based on longest wrapped line
    cell_width = max(len(line) for w in wrapped_words for line in w)

    # Construct lines
    output = []

    total_width = 6 + (cell_width + 3) * 4  # for border + spacing
    output.append("+" + "-" * (total_width - 2) + "+")
    output.append("|" + topic.center(total_width - 2) + "|")
    output.append("+" + "-" * (total_width - 2) + "+")

    # Column header
    header = "|     " + "".join(col.center(cell_width + 3) for col in columns) + " |"
    output.append(header)

    # Start grid
    index = 0
    horizontal = "+" + "-" * (total_width - 2) + "+"

    for r in rows:
        output.append(horizontal)

        # Each row may need multiple lines due to wrap
        for line_index in range(cell_height):
            row_str = f"| {r}  |"

            for _ in columns:
                cell_lines = wrapped_words[index]
                text_line = cell_lines[line_index] if line_index < len(cell_lines) else ""
                row_str += " " + text_line.ljust(cell_width) + " |"

                index += 1 if line_index == 0 else 0

            output.append(row_str)

    output.append(horizontal)

    return "\n".join(output)

def game_init():
    """
    Auto-generate the secret word and kick up the game start process
    Args: None
    Returns: None
    """
    topic, secret, coords = choose_keyword()
    grid = ascii_word_grid(topic)
    chameleon = randint(0,player_count-1)
    players[chameleon].is_chameleon = True
    print(grid)

# game_init()





###############DISCORD BOT INIT################

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!host') and state==Game_State.IDLE:
        state = Game_State.HOSTING
        await message.channel.send('Hello! :thumbsup: Thanks for using CHAMELEON BOT! Hosting game now! Type "!join" to join!')
    if state==Game_State.HOSTING and message.content.startswith('!join'):
        player = Player(message.author)
        players.append(player)
        player_count += 1
    if state==Game_State.HOSTING and message.content.startswith('!start'):
        state = Game_State.GAME_START
        game_init()

client.run(bot_token)

print(keyword)
print(coords)


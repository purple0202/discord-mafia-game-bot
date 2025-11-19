import discord
import textwrap
from enum import Enum
from random import randint
import time

##############GAME VARIABLES################
class Game_State(Enum):
    IDLE = 1
    HOSTING = 2
    GAME_START = 3
    MID_GAME = 4
    VOTING = 5
    GAME_ENDING = 6
    GUESS = 7

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
!vote @user: Command used during voting phase. Ping the suspicious user!
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
coords = None
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
    if secret.lower() in message:
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
    global topic
    global secret
    global coords
    topic, secret, coords = choose_keyword()
    grid = ascii_word_grid(topic)
    chameleon = randint(0,player_count-1)
    players[chameleon].is_chameleon = True
    print(secret)
    # players[chameleon].member.send("YOU ARE THE CHAMELEON!")
    # print(grid)
    return grid

def vote_complete():
    """
    Goes through player lists and sees if everyone voted so we can move on to the next stage
    Args: None
    Returns: None
    """
    for player in players:
        if player.voted == False:
            return False
    return True

def chameleon_caught():
    """
    Judges if the chameleon got caught based on the votes when game ends
    Args: None
    Returns: bool, player
    """
    max_count = 0
    max_voted = None
    for player in players:
        if player.vote_count > max_count:
            max_voted = player
    if max_voted.is_chameleon:
        return(True, max_voted)
    else:
        return(False, max_voted)
    
def game_reset():
    """
    """
    global state
    global coords
    global topic
    global secret
    global players
    global player_count
    state = Game_State.IDLE
    coords = None
    topic = None
    secret = None
    players = []
    player_count = 0


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
    global state
    global players
    global player_count
    if message.author == client.user:
        if message.content.startswith('Voting Complete!'):
            for player in players:
                if player.is_chameleon:
                    chameleon = player
            results = chameleon_caught()
            if results[0] == True:
                await message.channel.send("The most voted member, "+ results[1].member.name + " WAS the CHAMELEON!!!")
                await message.channel.send("Chameleon, guess the word!")
                state = Game_State.GUESS
            else:
                await message.channel.send("The most voted member, "+ results[1].member.name + " was NOT the CHAMELEON!!!")
                await message.channel.send("The chameleon, " + chameleon.member.name + "wins!!")
        else:
            return

    if message.content.startswith('!host') and state==Game_State.IDLE:
        state = Game_State.HOSTING
        await message.channel.send('Hello! :thumbsup: Thanks for using CHAMELEON BOT! Hosting game now! Type "!join" to join!')
        await message.channel.send(rules_text)
    if state==Game_State.IDLE and message.content.startswith('!commands'):
        await message.channel.send(commands_text)
    if state==Game_State.HOSTING and message.content.startswith('!join'):
        player = Player(message.author)
        players.append(player)
        player_count += 1
        await message.channel.send('Thanks for joining, ' + player.member.name + "!")
    if state==Game_State.HOSTING and message.content.startswith('!start'):
        state = Game_State.GAME_START
        await message.channel.send('Starting game!')
        grid = game_init()
        for player in players:
            if player.is_chameleon:
                await player.member.send("YOU ARE THE CHAMELEON!")
            else:
                await player.member.send("SEE "+ coords)
        await message.channel.send(grid)
        await message.channel.send("Take turns and describe the secret word with ONLY ONE word!")
        time.sleep(15*player_count)
        state = Game_State.VOTING
        await message.channel.send("Now vote for the chameleon!")
    if state==Game_State.VOTING and message.content.startswith('!vote') and message.mentions:
        for player in players:
            if player.member == message.author:
                voter = player
        print(voter.member.name)
        mentioned = message.mentions[0]
        # votee = message.content.split()[1].name
        # print(message.content)
        # print(votee)
        for player in players:
            if player.member == mentioned:
                votee = player
        votee.vote_count += 1
        voter.voted = True
        print(votee.vote_count)
        print(voter.voted)
        if vote_complete():
            state = Game_State.GAME_ENDING
            await message.channel.send("Voting Complete!")
    if state==Game_State.GUESS and message.content.startswith('!guess'):
        guess = message.content.split()[1]
        if guess_is_correct(message.content):
            await message.channel.send("CORRECT! The chameleon wins!!")
            game_reset()
        else:
            await message.channel.send("WRONG! Humans win!!")
            game_reset()

        


client.run(bot_token)

# print(keyword)
# print(coords)


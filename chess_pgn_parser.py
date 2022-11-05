from parsita import *
import json
from tkinter import filedialog
import tkinter as tk
import chess.pgn
from random import randint

"""Contains the PGN grammar definition
   and the opening book logic
"""


def format_annotations(ann):
    return {ant[0]: ant[1] for ant in ann}


def format_game(pgn_game):
    return {
            'moves': pgn_game[0],
            'outcome': pgn_game[1]
           }


def format_entry(pgn_entry):
    return {'annotations': pgn_entry[0], 'game': pgn_entry[1]}


def handle_optional(optional_move):
    if len(optional_move) > 0:
        return optional_move[0]
    else:
        return None


def parse_chess_game():
    root = tk.Tk()
    root.withdraw()
    fi = filedialog.askopenfilename()
    with open(fi, 'r') as f:
        root.destroy()
        parsedoutput = file.parse(f.read()).or_die()
        with open('games//opening_data//json_data.json', 'w') as outfile:
            json.dump(parsedoutput[0], outfile)


def load_pgn(import_game, chosen_opening):
    """Returns the parsed PGN moves or the chosen opening

       Keyword arguments:
       import_game    -- True if a pgn is imported
                         (False for opening book)
       chosen_opening -- True if the user selected an opening
                         (False means random opening)
    """
    if import_game:
        root = tk.Tk()
        root.withdraw()
        fi = filedialog.askopenfilename()
        try:
            pgn = open(fi)
            with open(fi, 'r') as f:
                parsed_output = file.parse(f.read()).or_die()
            with open('games//opening_data//json_data.json', 'w') as outfile:
                json.dump(parsed_output[0], outfile)
            with open(r"games//opening_data//json_data.json") as json_file:
                data = json.load(json_file)

        except FileNotFoundError:
            print("Wrong file or file path")
            return 0, 0, 0
        except ValueError:
            print("Not a valid PGN")
            return 0, 0, 0

        pgn_outcome = data["game"]["outcome"]
        first_game = chess.pgn.read_game(pgn)
        pgn_moves = []
        for pgn_move in first_game.mainline_moves():
            pgn_moves.append(str(pgn_move))
        return pgn_moves, data, pgn_outcome
    else:
        with open(r"openings//openings.json") as json_file:
            data = json.load(json_file)
            opening_index = randint(0, len(data))
            fil = open(r"games//opening_data//last_opening.txt", "w")

            if chosen_opening == "" or chosen_opening == "Random":
                fil.write(data[opening_index]["moves"])
            else:
                for index in range(0, len(data)):
                    if data[index]["name"] == chosen_opening:
                        fil.write(data[index]["moves"])
                        opening_index = index
            fil.close()
            opening_pgn = open(r"games//opening_data//last_opening.txt")
            first_game = chess.pgn.read_game(opening_pgn)
            pgn_moves = []
            for pgn_move in first_game.mainline_moves():
                pgn_moves.append(str(pgn_move))
            opening_name = data[opening_index]["name"]
            return pgn_moves, opening_name, None


"""PGN Grammar
"""

quote = lit(r'"')
tag = reg(r'[\u0021-\u0021\u0023-\u005A\u005E-\u007E]+')
string = reg(r'[\u0020-\u0021\u0023-\u005A\u005E-\U0010FFFF]+')
annotation = '[' >> tag << ' ' & (quote >> string << quote) << ']'
annotations = repsep(annotation, '\n') > format_annotations
nullmove = lit('--')
longcastle = reg(r'O-O-O[+#]?') | reg(r'0-0-0[+#]?')
castle = reg(r'O-O[+#]?') | reg(r'0-0[+#]?')
regularmove = reg(r'[a-h1-8NBRQKx\+#=]+')
move = regularmove | longcastle | castle | nullmove
whitespace = (reg(r'[ ]+')) | lit('\n')
movenumber = (reg(r'[0-9]*') << reg(r'.[ ]*')) > int
turn = movenumber & (move << whitespace) & (opt(move << whitespace) > handle_optional)
draw = lit('1/2-1/2')
white = lit('1-0')
black = lit('0-1')
outcome = draw | white | black
game = (rep(turn) & outcome) > format_game
entry = ((annotations << rep(whitespace)) & (game << rep(whitespace))) > format_entry
file = rep(entry)

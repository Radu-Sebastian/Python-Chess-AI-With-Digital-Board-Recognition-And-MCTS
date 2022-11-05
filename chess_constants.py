import os
from os import environ
import pygame as p
import numpy as np
import random
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

"""Contains the constant variables, dictionaries or 
   methods used in the project
"""

flip = False
ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                 "5": 3, "6": 2, "7": 1, "8": 0}

files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                 "e": 4, "f": 5, "g": 6, "h": 7}

ranks_to_rows_flip = {"8": 7, "7": 6, "6": 5, "5": 4,
                      "4": 3, "3": 2, "2": 1, "1": 0}

files_to_cols_flip = {"h": 0, "g": 1, "f": 2, "e": 3,
                      "d": 4, "c": 5, "b": 6, "a": 7}

ranks_dict = ranks_to_rows
files_dict = files_to_cols

rows_to_ranks = {v: k for k, v in ranks_dict.items()}
cols_to_files = {v: k for k, v in files_dict.items()}

########################################################################################################################
# Default Interface Constants

DIMENSION = 8
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_WIDTH = 470
MENU_WIDTH = 512
MENU_HEIGHT = 512
EVAL_BAR_WIDTH = 50
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 60
BUTTON_SIZE = 108
BUTTON_SPACING = 16
BUTTON_PADDING = BUTTON_SIZE + BUTTON_SPACING
DEFAULT_IMAGE_SIZE = (320, 320)
TEXT_BOX_SIZE = 15
frames_per_square = 5
animations = True
move_sounds = False
coordinates = False
white_king_location = (7, 4)
black_king_location = (0, 4)
engine_helper_text_y = 440
engine_helper_offset_x = 100
engine_helper_offset_x_it = 55
max_candidate_engine_moves = 5
endgame_return_offset_y = 40
endgame_save_offset_y = 80
engine_helper_offset_y = 10
difficulty_clicker = 0
logo_coord = (216, 10)
algorithm_depth_offset_y = 95
timeout = 0
engine_used = False
depth = 3
ai_vs_ai_caption = "AI vs AI"
white_vs_ai_caption = "Human (White) vs AI (Black)"
ai_vs_black_caption = "AI (White) vs Human (Black)"
practice_caption = "Practice Mode"
pgn_caption = "Imported PGN (Press '>' to make a move, '<' to undo last move)"

########################################################################################################################
# Classifier Interface Constants

imported = False
CLASSIFY_WIDTH = 700
CLASSIFY_HEIGHT = 680
SQ_SIZE_C = 40
info_x = 10
info_y = 390
warning_y = 650
MAX_ITERATIONS = 2100000
arrow_x = CLASSIFY_WIDTH // 2 - 15
arrow_y = CLASSIFY_HEIGHT // 2 - 125
loading_bar_height = 50
classifier_text_height = 20
imported_image_coordinates = (10, 60)
coordinates_x = 54
coordinates_y = 47


########################################################################################################################
# Main Menu Elements

default_board = [["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
                 ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
                 ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                 ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                 ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                 ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                 ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
                 ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]

default_flipped_board = [["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
                         ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
                         ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                         ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                         ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                         ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                         ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
                         ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"]]

pieces = ['wP', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bP', 'bR', 'bN', 'bB', 'bK', 'bQ']

buttons = {
            "buttonAIvsAI":
            (BUTTON_SPACING, 120, BUTTON_SIZE, BUTTON_SIZE),
            "buttonWhitevsAI":
            (2 * BUTTON_SPACING + BUTTON_SIZE, 120, BUTTON_SIZE, BUTTON_SIZE),
            "buttonAIvsBlack":
            (3 * BUTTON_SPACING + 2 * BUTTON_SIZE, 120, BUTTON_SIZE, BUTTON_SIZE),
            "buttonHumanvsHuman":
            (4 * BUTTON_SPACING + 3 * BUTTON_SIZE, 120, BUTTON_SIZE, BUTTON_SIZE),
            "buttonImport":
            (BUTTON_SPACING, 120 + BUTTON_PADDING, BUTTON_SIZE, BUTTON_SIZE),
            "buttonClassify":
            (2 * BUTTON_SPACING + BUTTON_SIZE, 120 + BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonCustomizer":
            (3 * BUTTON_SPACING + 2 * BUTTON_SIZE, 120 + BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonDifficulty":
            (4 * BUTTON_SPACING + 3 * BUTTON_SIZE, 120 + BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonUseEngine":
            (BUTTON_SPACING, 120 + 2 * BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonDisableEngine":
            (BUTTON_SPACING, 120 + 2 * BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonRandomOpening":
            (2 * BUTTON_SPACING + BUTTON_SIZE, 120 + 2 * BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonChangeAlgorithm":
            (3 * BUTTON_SPACING + 2 * BUTTON_SIZE, 120 + 2 * BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE),
            "buttonNewFeatures":
            (4 * BUTTON_SPACING + 3 * BUTTON_SIZE, 120 + 2 * BUTTON_PADDING,
             BUTTON_SIZE, BUTTON_SIZE)
           }

########################################################################################################################
# Classifier Elements

predicted_offset_x = 370
predicted_offset_y = 60
test_img_size = 90
classifier_info = {
                    "May White Castle?":
                    [None, False],
                    "May Black Castle?":
                    [None, False],
                    "Black to move?":
                    [None, False],
                    "White on top?":
                    [None, False],
                    "Continue (Practice)":
                    [None, False],
                    "Continue (vs AI) (White)":
                    [None, False],
                    "Continue (vs AI) (Black)":
                    [None, False],
                    "Continue (AI vs AI)":
                    [None, False],
                  }

classifier_info_text = \
    {
        "> Import a digital chess board from your device.":
        p.Rect(10, 420, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
        "> Using the Naive Bayes classifier, the predicted board will be built on the right side.":
        p.Rect(10, 450, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
        "> After the classification, some optional flags will be checked:":
        p.Rect(10, 480, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
        "> Castling rights, who is next to move, board flip, etc.":
        p.Rect(10, 510, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
        "> After the flags are set, continue playing from predicted board.":
        p.Rect(10, 540, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
        "> If the board isn't predicted entirely, you may modify it before playing.":
        p.Rect(10, 570, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
        "> The game modes available from predicted board: AI vs AI, Practice, White vs AI and AI vs Black.":
        p.Rect(10, 600, CLASSIFY_WIDTH // 2, CLASSIFY_HEIGHT // 2),
    }

blank_board = [["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
               ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"]]

sample_board = [["bR", "xx", "bB", "bQ", "bK", "xx", "xx", "bR"],
                ["xx", "xx", "bP", "bP", "bB", "bP", "bP", "bP"],
                ["bP", "xx", "bN", "xx", "xx", "bN", "xx", "xx"],
                ["xx", "bP", "xx", "xx", "bP", "xx", "xx", "xx"],
                ["wB", "xx", "xx", "xx", "wP", "xx", "xx", "xx"],
                ["xx", "xx", "xx", "xx", "xx", "wN", "xx", "xx"],
                ["wP", "wP", "wP", "wP", "xx", "wP", "wP", "wP"],
                ["wR", "wN", "wB", "wQ", "wR", "xx", "wQ", "xx"]]

back_button_circle = (17, CLASSIFY_HEIGHT - 15)
back_button_play_circle = (17, 15)
back_button_play = (3, MENU_HEIGHT, 20, 20)
back_button = (3, CLASSIFY_HEIGHT - 40, 20, 20)
documentation_button = (CLASSIFY_WIDTH - 30, CLASSIFY_HEIGHT - 40, 20, 20)
documentation_circle = (CLASSIFY_WIDTH - 17, CLASSIFY_HEIGHT - 15)
spacing_y = back_button_radius = 30
import_text = 'Import from device'
import_button = ['Import from device', p.Rect(10, 420, TEXT_BOX_SIZE, TEXT_BOX_SIZE)]
classifier_footer = p.Rect(0, CLASSIFY_HEIGHT - 40, CLASSIFY_WIDTH, 40)
github_classifier_page = 'https://github.com/Radu-Sebastian/DigitalChessClassifier'

########################################################################################################################
# Evaluation Bar Elements

eval_width = 50
eval_white_win = "1-0"
eval_black_win = "0-1"

########################################################################################################################
# Customizer Elements

board_colors = [p.Color(147, 112, 219), p.Color(0, 102, 204), p.Color(0, 153, 76), p.Color(153, 0, 76)]
pieces_skins = ["initial", "chess24", "letters", "tatiana", "cases"]
current_piece_skin = "initial"
back_button_customizer = (3, MENU_HEIGHT - 35, 20, 20)
customizer_offset_x = 96
customizer_button_offset_x = info_y - 55
customizer_offset_y = 10
customizer_footer = p.Rect(0, MENU_HEIGHT - 40, MENU_WIDTH, 40)

customizer_info_text = {
                    "> Change Color":
                    [None, False],
                    "> Change Pieces":
                    [None, False],
                    "> Toggle Animations":
                    [None, False],
                    "> Enable Sound Effects":
                    [None, False],
                    "> Enable Board Coordinates":
                    [None, False]
                  }

########################################################################################################################
# Pygame Elements (Images, Fonts, Colors)

p.init()
font = p.font.SysFont(r'texgyrecursorbold', 15)
font_classifier = p.font.SysFont(r'texgyrecursorbold', 12)
text_font = p.font.SysFont("texgyrecursorbold", 12, True, False)
text_font_end_message = p.font.SysFont("texgyrecursorbold", 15, True, False)

highlight_alpha = 100
button_color = p.Color(213, 213, 20)
button_color_clicked = p.Color(119, 148, 85)
light_sq_color = p.Color(211, 211, 211)
dark_sq_color = p.Color(147, 112, 219)
screen_color = p.Color(147, 112, 219)
menu_bg_color = p.Color("Black")
eval_text_color = p.Color("White")
highlight_color = p.Color("Green")
click_color = p.Color("Yellow")
text_color = p.Color("Black")
classifier_screen_color = "light gray"
progress_bar_color = "dark green"
warning_color = p.Color(255, 204, 203)

########################################################################################################################
# Imported Files

documentation_icon = p.image.load(r'images/gui/documentationIcon.png')
default_classifier_board = p.image.load(f'boards/DeacNepo.png')
disable_engine_button = "buttonDisableEngine"
back_icon = p.image.load(r'images/gui/backIcon.png')
icon = p.image.load(r'images/gui/mychesslogo.png')
logo = p.image.load(r"images/gui/mychesslogo.png")
last_game_logs = "games/LastGameLogs.txt"
mcts_data = "mcts_data/LastMoveLogs.txt"
last_agent_game_logs = "agent_results/LastAgentGameLogs.csv"
classifier_likelihood = r"bayes_results//train_likelihood.txt"
classifier_priori = r"bayes_results//train_priori.txt"

########################################################################################################################
# Interface Text

draw = '1/2-1/2'
white_win = '1-0'
black_win = '0-1'
draw_text = 'Draw (1/2 - 1/2)'
stalemate_text = 'Draw by Stalemate (1/2 - 1/2)'
repetition_draw_text = 'Draw by Repetition (1/2 - 1/2)'
checkmate_white_text = 'White wins by checkmate (1-0)'
checkmate_black_text = 'Black wins by checkmate (0-1'
classifier_caption = 'Digital Chess Board Classifier'
customizer_caption = 'Customize Features'
king_error_text = 'Missing king or multiple kings found! Please Modify Board to Continue!'
return_menu_text = 'Return to main menu'
save_game_text = 'Save game (PGN)'
classifier_arrows = '→→→'
empty = 'xx'
menu_caption = 'Chess Engine with Digital Image Recognition'

########################################################################################################################
# Move Log Constants

maximum_displayed_moves = 39
last_displayed_moves = 36
moves_per_row = 3
line_spacing = 2
padding = 5
move_log_offset_x = 55

########################################################################################################################
# AI Constants

knight_scores = np.array([[-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0],
                          [-4.0, -2.0, 0.10, 0.10, 0.10, 0.10, -2.0, -4.0],
                          [-3.0, 0.00, 1.00, 1.50, 1.50, 1.00, 0.00, -3.0],
                          [-3.0, 0.50, 1.50, 2.00, 2.00, 1.50, 0.50, -3.0],
                          [-3.0, 0.50, 1.50, 2.00, 2.00, 1.50, 0.50, -3.0],
                          [-3.0, 0.00, 0.80, 1.50, 1.50, 0.80, 0.00, -3.0],
                          [-4.0, -2.0, 0.10, 0.50, 0.50, 0.10, -2.0, -4.0],
                          [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0]])

bishop_scores = np.array([[-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0],
                          [-1.0, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, -1.0],
                          [-1.0, 0.00, 0.50, 1.00, 1.00, 0.10, 0.00, -1.0],
                          [-1.0, 0.50, 0.50, 1.00, 1.00, 0.50, 0.50, -1.0],
                          [-1.0, 0.00, 1.00, 1.00, 1.00, 1.00, 0.00, -1.0],
                          [-1.0, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, -1.0],
                          [-1.0, 0.50, 0.00, 0.00, 0.00, 0.00, 0.50, -1.0],
                          [-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0]])

queen_scores = np.array([[-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0],
                         [-1.0, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, -1.0],
                         [-1.0, 0.00, 0.50, 0.50, 0.50, 0.50, 0.00, -1.0],
                         [-0.5, 0.00, 0.50, 0.50, 0.50, 0.50, 0.00, -0.5],
                         [0.00, 0.00, 0.50, 0.50, 0.50, 0.50, 0.00, -0.5],
                         [-1.0, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, -1.0],
                         [-1.0, 0.00, 0.50, 0.00, 0.00, 0.50, 0.00, -1.0],
                         [-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0]])

rook_scores = np.array([[0.00, 0.25, 0.50, 0.50, 0.50, 0.50, 0.25, 0.00],
                        [0.00, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.00],
                        [0.00, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.00],
                        [0.00, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.00],
                        [0.00, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.00],
                        [0.00, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.00],
                        [0.00, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.00],
                        [0.00, 0.00, 0.00, 0.40, 0.20, 0.40, 0.00, 0.00]])

pawn_scores = np.array([[0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                        [5.00, 5.00, 5.00, 5.00, 5.00, 5.00, 5.00, 5.00],
                        [1.00, 1.00, 2.00, 3.00, 3.00, 2.00, 1.00, 1.00],
                        [0.50, 0.50, 1.00, 2.50, 2.50, 1.00, 0.50, 0.50],
                        [0.00, 0.00, 2.50, 3.10, 3.20, 0.00, 0.00, 0.00],
                        [0.50, 1.00, -1.0, 0.00, 0.00, -1.0, 1.00, 0.50],
                        [0.50, 1.00, 1.00, -2.0, -2.0, 1.00, 1.00, 0.50],
                        [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]])

king_scores = np.array([[-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                        [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                        [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                        [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -2.0],
                        [-2.0, -3.0, -3.0, -4.0, -4.0, -3.0, -3.0, -2.0],
                        [-1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0],
                        [2.00, 2.00, 1.00, 0.00, 0.00, 0.00, 2.00, 2.00],
                        [2.00, 3.00, 1.00, 0.00, 0.00, 1.00, 3.00, 2.00]])

piece_position_scores = {"wN": knight_scores,
                         "bN": knight_scores[::-1],
                         "wB": bishop_scores,
                         "bB": bishop_scores[::-1],
                         "wQ": queen_scores,
                         "bQ": queen_scores[::-1],
                         "wR": rook_scores,
                         "bR": rook_scores[::-1],
                         "wP": pawn_scores,
                         "bP": pawn_scores[::-1],
                         "wK": king_scores,
                         "bK": king_scores[::-1]
                         }

developing_moves_white_init =\
    ["d4", "e4", "c4", "b3", "g3", "Nc3", "Nbd2", "Nf3", "Ne2", "Bg2", "Bb2", "Bc4", "Bb5", "Bd3"]
developing_moves_black_init =\
    ["d5", "e5", "c5", "b6", "g6", "Nc6", "Nbd7", "Nf6", "Ne6", "Bg7", "Bb7", "Bc5", "Be7", "Bd6"]
developing_moves_white = ["d4", "e4", "c4", "b3", "g3", "Nc3", "Nbd2", "Nf3", "Ne2", "Bg2", "Bb2", "Bc4", "Bb5", "Bd3"]
developing_moves_black = ["d5", "e5", "c5", "b6", "g6", "Nc6", "Nbd7", "Nf6", "Ne6", "Bg7", "Bb7", "Bc5", "Be7", "Bd6"]

piece_score = {"K": 0, "Q": 9.5, "R": 5.1, "B": 3.2, "N": 3, "P": 1}
CHECKMATE = 1000
STALEMATE = 0
MAX_DEPTH = 10

algorithm_count = 0
algorithms = ["negamax_pruning", "minimax", "negamax_pruning_id_t_2",
              "negamax_pruning_id_t_5", "negamax_pruning_id_t_10", "mcts"]
current_algorithm = "negamax_pruning"


def find_random_move(valid_moves):
    return random.choice(valid_moves)

########################################################################################################################
# Constant Methods


def get_pgn_move(index, pgn_moves, valid_moves):
    pgn_move = str(pgn_moves[index])
    start_row = ranks_dict[pgn_move[1]]
    start_col = files_dict[pgn_move[0]]
    end_row = ranks_dict[pgn_move[3]]
    end_col = files_dict[pgn_move[2]]

    for move in valid_moves:
        if move.start_row == start_row and move.start_col == start_col \
                and move.end_row == end_row and move.end_col == end_col:
            return move


def make_option_sound():
    p.mixer.music.load(f'sounds\\option_sound.mp3')
    p.mixer.music.play(loops=0)


def make_move_sound():
    p.mixer.music.load(f'sounds\\move_sound.mp3')
    p.mixer.music.play(loops=0)


def count_folder_files(path):
    count = 0
    for root, dirs, files in os.walk(path):
        for _ in files:
            count = count + 1
    return count


def insert_move_ordering(moves, move):
    if move.move_score > 100:
        moves.insert(0, move)
    else:
        moves.append(move)


def get_file_rank_notation(row, col):
    return cols_to_files[col] + rows_to_ranks[row]


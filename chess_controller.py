import csv

import chess_pgn_parser
import chess_engine
import chess_main as main
import chess_constants as k
import chess_ai
import chess_mcts
import os
import pygame as p
import time
import numpy as np
import sys
from datetime import date
from datetime import datetime
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


class ChessController:
    """Main controller of the project
       Handles most user events and updates the view
    """
    def __init__(self, view):
        self.view = view
        self.view.load_images()
        self.model = chess_engine.GameState()

        self.human_turn = None
        self.game_over = False
        self.animate = False
        self.last_clicks = []
        self.square_clicked = ()
        self.move_made = False
        self.pgn_more = False
        self.play_pgn = False
        self.pgn_count = 0
        self.pgn_outcome = "--"
        self.pgn_over = False
        self.valid_moves = []
        self.saved_game = False
        self.progress_pgn = False
        self.player_one = None
        self.player_two = None

        self.handler_functions = {
            "buttonAIvsAI": self.ai_vs_ai_handler,
            "buttonWhitevsAI": self.white_vs_ai_handler,
            "buttonAIvsBlack": self.ai_vs_black_handler,
            "buttonHumanvsHuman": self.practice_handler,
            "buttonImport": self.import_handler,
            "buttonClassify": self.classifier_handler,
            "buttonCustomizer": self.customizer_handler,
            "buttonDifficulty": self.difficulty_handler,
            "buttonUseEngine": self.engine_handler,
            "buttonRandomOpening": self.random_opening_handler,
            "buttonNewFeatures": self.features_handler,
            "buttonChangeAlgorithm": self.algorithm_handler
           }

    def animate_move(self, move):
        """Draws the piece moved frame_count times
           in order to simulate an animation

           Keyword arguments:
           move -- Move object (start row, start col, end row, end col)
        """
        model = self.model
        view = self.view

        delta_row = move.end_row - move.start_row
        delta_col = move.end_col - move.start_col
        frame_count = k.frames_per_square * (abs(delta_row) + abs(delta_col))
        colors = [p.Color("light gray"), p.Color("purple")]

        for frame in range(frame_count + 1):
            row, col = (move.start_row + delta_row * frame / frame_count,
                        move.start_col + delta_col * frame / frame_count)
            view.draw_squares()
            view.draw_pieces(view.screen, model.board)
            color = colors[(move.end_row + move.end_col) % 2]

            end_square = p.Rect(move.end_col * k.SQUARE_SIZE, move.end_row * k.SQUARE_SIZE,
                                k.SQUARE_SIZE, k.SQUARE_SIZE)
            p.draw.rect(view.screen, color, end_square)

            if move.place_to_go != k.empty:
                if move.en_passant_move:
                    en_passant_row = move.end_row + 1 if move.place_to_go[0] == "b" else move.end_row - 1
                    end_square = p.Rect(move.end_col * k.SQUARE_SIZE, en_passant_row * k.SQUARE_SIZE,
                                        k.SQUARE_SIZE, k.SQUARE_SIZE)
                view.screen.blit(view.IMAGES[move.place_to_go], end_square)

            view.screen.blit(view.IMAGES[move.piece_to_move],
                             p.Rect(col * k.SQUARE_SIZE, row * k.SQUARE_SIZE,
                             k.SQUARE_SIZE, k.SQUARE_SIZE))
            p.display.flip()
            view.clock.tick(k.MAX_FPS)

        if k.move_sounds:
            k.make_move_sound()

    def highlight_moves(self, square_clicked):
        """Highlights the square clicked by the user
           by coloring it in a different way
           The last move made will also have the
           destination and starting squares coloured

           Keyword arguments:
           square_clicked -- (row, col)
        """
        model = self.model
        view = self.view

        if (len(model.move_log)) > 0:
            last_move = model.move_log[-1]
            s = p.Surface((k.SQUARE_SIZE, k.SQUARE_SIZE))
            s.set_alpha(k.highlight_alpha)
            s.fill(k.highlight_color)
            view.screen.blit(s, (last_move.start_col * k.SQUARE_SIZE, last_move.start_row * k.SQUARE_SIZE))
            view.screen.blit(s, (last_move.end_col * k.SQUARE_SIZE, last_move.end_row * k.SQUARE_SIZE))

        if square_clicked != ():
            row, col = square_clicked
            if model.board[row][col][0] == ("w" if model.white_moves else "b"):
                surface = p.Surface((k.SQUARE_SIZE, k.SQUARE_SIZE))
                surface.set_alpha(k.highlight_alpha)
                surface.fill(k.click_color)
                view.screen.blit(surface, (col * k.SQUARE_SIZE, row * k.SQUARE_SIZE))

                surface.fill(k.click_color)
                for move in self.valid_moves:
                    if move.start_row == row and move.start_col == col:
                        view.screen.blit(surface, (k.SQUARE_SIZE * move.end_col,
                                                   k.SQUARE_SIZE * move.end_row))

    def draw_game_state(self, ai):
        """Updates all view components from
           main menu (board, move log, evaluation bar, etc.)

           Keyword arguments:
           ai -- AI module of the application
        """
        self.view.draw_squares()
        self.highlight_moves(self.square_clicked)
        self.view.draw_pieces(self.view.screen, self.model.board)
        self.draw_move_log()
        if k.engine_used:
            self.draw_evaluation_bar(ai)
            self.view.draw_suggested_moves(ai)
        if self.pgn_over:
            self.view.draw_text(self.pgn_outcome, k.BOARD_WIDTH, k.BOARD_HEIGHT)

    def draw_move_log(self):
        """On the right side of the screen, the
           moves made will be displayed
           (when playing or watching a chess game)
        """
        model = self.model
        view = self.view
        move_log_region = p.Rect(k.BOARD_WIDTH + k.move_log_offset_x, 0, k.MOVE_LOG_WIDTH, k.BOARD_HEIGHT)
        p.draw.rect(view.screen, k.text_color, move_log_region)
        pgn_log = model.pgn_log
        move_notations = []
        text_y = k.padding

        for index in range(0, len(pgn_log), 2):
            move_string = str(index // 2 + 1) + ". " + pgn_log[index] + " "
            if index + 1 < len(pgn_log):
                move_string += pgn_log[index + 1] + " "
            move_notations.append(move_string)

        if len(move_notations) > k.maximum_displayed_moves:
            move_notations = move_notations[-k.last_displayed_moves:]

        for i in range(0, len(move_notations), k.moves_per_row):
            text = ""
            for j in range(k.moves_per_row):
                if i + j < len(move_notations):
                    text += move_notations[i + j]
            text_object = k.font.render(text, True, k.eval_text_color)
            text_location = move_log_region.move(k.padding, k.padding + text_y)
            view.screen.blit(text_object, text_location)
            text_y += text_object.get_height() + k.line_spacing

    def save_game(self, result, user_save):
        """Updates the LastGameLogs with the
           PGN notation of the last game played
           or saves the game to a new file
           (if the user specifies it)

           Keyword arguments:
           result    -- the outcome of the game (1-0, 1/2-1/2 or 0-1)
           user_save -- true if user wants to save the game to a new file
        """
        pgn_log = self.model.pgn_log
        all_moves = ""
        for i in range(0, len(pgn_log), 2):
            move_string = str(i // 2 + 1) + ". " + pgn_log[i] + " "
            if i + 1 < len(pgn_log):
                move_string += pgn_log[i + 1] + " "
            all_moves += move_string

        save_time = datetime.now()
        save_time_text = save_time.strftime("%b-%d-%Y-%H-%M-%S")
        file_name = f"games/saved_games/Game-{save_time_text}-PGN.txt"
        file = open(f"{k.last_game_logs}", "w") if not user_save else open(str(file_name), "w")
        file.write(f'[Event "Simple Chess"]\n')
        file.write(f'[Site "Chess App"]\n')
        today = date.today()
        file.write(f'[Date "{today.strftime("%d/%m/%Y")}"]\n')
        file.write(f'[Round "?"]\n')
        white_player = "ChessUser" if self.player_one else "ChessEngine"
        black_player = "ChessUser" if self.player_two else "ChessEngine"
        file.write(f'[White "{white_player}"]\n')
        file.write(f'[Black "{black_player}"]\n')

        if not self.model.checkmate:
            file.write(all_moves)
        else:
            file.write(all_moves[:-2]+"#")
        file.write(f' {result}')
        file.close()

    def draw_evaluation_bar(self, ai):
        """Updates the evaluation bar (if the engine
           is enabled) after the score given
           by the search algorithm used by the system

           Keyword arguments:
           ai -- AI module of the application
        """
        if self.model.checkmate is False:
            displayed_score = ai.depth_score if k.timeout == 0 else ai.global_score
            out_string = str("{:.1f}".format(displayed_score))
            bar_start = k.BOARD_HEIGHT // 2 - 2 * displayed_score
        else:
            if self.model.white_moves:
                out_string = k.eval_black_win
                bar_start = k.BOARD_HEIGHT
            else:
                out_string = k.eval_white_win
                bar_start = 0

        p.draw.rect(self.view.screen, p.Color("White"),
                    p.Rect(k.BOARD_HEIGHT,
                           bar_start, k.eval_width,
                           k.BOARD_HEIGHT))
        p.draw.rect(self.view.screen, p.Color("Black"),
                    p.Rect(k.BOARD_HEIGHT,
                           0, k.eval_width,
                           bar_start))

        text_obj = k.font.render(str(out_string), True, k.eval_text_color)
        self.view.erase_menu_text(text_obj,
                                  k.BOARD_HEIGHT - text_obj.get_width() + k.eval_width, k.BOARD_HEIGHT/2)
        self.view.draw_menu_text(out_string, k.eval_text_color,
                                 k.BOARD_HEIGHT - text_obj.get_width() + k.eval_width, k.BOARD_HEIGHT/2)

    def play_ai_move(self, ai):
        """Plays the best move returned by
           the current search algorithm used

           Keyword arguments:
           ai -- AI module of the application
        """
        ai_function = ai.algorithm_functions[k.current_algorithm]
        if k.current_algorithm != 'mcts':
            ai_move = ai_function(self.model, self.valid_moves)
        else:
            ai_move = chess_mcts.find_best_move_mcts(self.model.chessboard, self.valid_moves)

        if ai_move is None:
            ai_move = k.find_random_move(self.valid_moves)
        self.model.make_move(ai_move)
        self.move_made = True
        self.animate = True

    def play_pgn_move(self, pgn_game):
        """Plays the current pgn_move from the
           imported file

           Keyword arguments:
           pgn_game -- list of moves (from pgn file)
        """
        pgn_move = k.get_pgn_move(self.pgn_count, pgn_game, self.valid_moves)
        self.model.make_move(pgn_move)
        self.move_made = True
        self.animate = True
        self.pgn_count = self.pgn_count + 1
        time.sleep(0.5)

    def flip_handler(self):
        """F pressed -> board will be flipped
        """
        self.model.board = np.flip(self.model.board)
        k.flip = not k.flip
        if k.flip:
            k.ranks_dict = k.ranks_to_rows_flip
            k.files_dict = k.files_to_cols_flip
        else:
            k.ranks_dict = k.ranks_to_rows
            k.files_dict = k.files_to_cols

        k.rows_to_ranks = {v: c for c, v in k.ranks_dict.items()}
        k.cols_to_files = {v: c for c, v in k.files_dict.items()}

        self.model.white_king_location = (7 - self.model.white_king_location[0],
                                          self.model.white_king_location[1])
        self.model.black_king_location = (7 - self.model.black_king_location[0],
                                          self.model.black_king_location[1])
        self.valid_moves = self.model.get_valid_moves()

    def undo_handler(self):
        self.model.undo_move()
        self.move_made = True
        self.animate = False
        self.game_over = False

    def move_made_handler(self, ai, window_text):
        if self.move_made:
            if self.animate and k.animations:
                self.animate_move(self.model.move_log[-1])
            self.valid_moves = self.model.get_valid_moves()
            self.move_made = False
            self.animate = False
            if k.engine_used and 'AI' not in window_text:
                ai.find_best_move_nega_max_alpha_beta(self.model, self.valid_moves)

    def endgame_handler(self, ai):
        self.game_over = True
        if not self.model.draw_rule:
            text = k.stalemate_text if self.model.stalemate else k.checkmate_black_text \
                if self.model.white_moves else k.checkmate_white_text
        else:
            text = k.repetition_draw_text
        pgn_text = k.draw if self.model.stalemate or self.model.draw_rule \
            else k.black_win if self.model.white_moves else k.white_win
        self.view.draw_text(text, k.BOARD_WIDTH, k.BOARD_HEIGHT)
        self.save_game(pgn_text, user_save=False)
        self.view.return_main_menu_button = self.view.draw_text(k.return_menu_text,
                                                                k.BOARD_WIDTH,
                                                                k.BOARD_HEIGHT + k.endgame_return_offset_y)
        self.view.save_pgn_button = self.view.draw_text(k.save_game_text,
                                                        k.BOARD_WIDTH,
                                                        k.BOARD_HEIGHT + k.endgame_save_offset_y)
        if not self.player_two or not self.player_one:
            try:
                with open(k.last_agent_game_logs, 'w') as f:
                    write = csv.writer(f)
                    write.writerow(["Move", "Nodes", "Score", "Time [s]"])
                    write.writerows(ai.agent_data)
            except PermissionError:
                main.main()

    def key_handler(self, event, import_pgn, window_text):
        if event.key == p.K_z:
            self.undo_handler()
            if import_pgn:
                self.pgn_over = False
                self.pgn_count -= 1

        if event.key == p.K_r:
            main.main()

        if event.key == p.K_UP or event.key == p.K_DOWN:
            self.play_pgn = not self.play_pgn

        if event.key == p.K_RIGHT and not self.game_over:
            self.progress_pgn = True

        if event.key == p.K_LEFT and import_pgn:
            self.undo_handler()
            self.pgn_count -= 1
            self.pgn_over = False
            self.game_over = False

        if event.key == p.K_f and window_text != 'AI vs AI':
            self.flip_handler()

    def run_game(self, window_text, import_pgn, play_opening):
        """Core method of the project
           Keeps main menu alive and waits for user events

           Keyword arguments:
           window_text  -- the text displayed by the window
                           (depending on selected option)
           import_pgn   -- True if user wants to import a PGN
           play_opening -- True if user used opening book
        """
        p.init()
        p.display.set_caption(window_text)
        pgn_game = 0
        if import_pgn is True:
            if play_opening is False:
                pgn_game, json_data, outcome = chess_pgn_parser.load_pgn(True, None)
                print(json_data)
                if pgn_game == 0:
                    main.main()
            else:
                self.view.run_opening_book()
                pgn_game, opening_name, outcome = chess_pgn_parser.load_pgn(False, self.view.chosen_opening)
                p.display.set_caption(opening_name)
            self.pgn_outcome = outcome

        view = self.view
        view.screen = p.display.set_mode((k.BOARD_WIDTH + k.MOVE_LOG_WIDTH, k.BOARD_HEIGHT))
        state = self.model
        self.saved_game = False

        ai = chess_ai.ChessAI(k.depth)
        self.valid_moves = state.get_valid_moves()

        clicked = False
        running = True
        self.pgn_count = 0

        while running:
            self.human_turn = (state.white_moves and self.player_one) or (not state.white_moves and self.player_two)
            for event in p.event.get():
                if event.type == p.QUIT:
                    p.quit()
                    sys.exit()
                elif event.type == p.MOUSEBUTTONDOWN:
                    if p.mouse.get_pressed(3)[0] == 1 and clicked is False:
                        clicked = True
                        self.mouse_handler()
                elif event.type == p.KEYDOWN:
                    self.key_handler(event, import_pgn, window_text)

            if p.mouse.get_pressed(3)[0] == 0:
                clicked = False

            self.draw_game_state(ai)

            if not play_opening and not import_pgn:
                self.progress_pgn = True

            if not self.game_over and not self.human_turn:
                if import_pgn is False or play_opening is True and self.pgn_count >= len(pgn_game):
                    if self.progress_pgn:
                        self.play_ai_move(ai)
                    if not self.play_pgn:
                        self.progress_pgn = False
                    self.pgn_count = self.pgn_count + 1
                else:
                    if self.pgn_count < len(pgn_game) and self.progress_pgn and not self.game_over:
                        self.play_pgn_move(pgn_game)
                        if not self.play_pgn:
                            self.progress_pgn = False
                    else:
                        if self.pgn_count == len(pgn_game):
                            self.pgn_over = True
                            self.endgame_handler(ai)

            self.move_made_handler(ai, window_text)

            if state.checkmate or state.stalemate or state.draw_rule:
                self.endgame_handler(ai)

            view.clock.tick(k.MAX_FPS)
            p.display.flip()

    def mouse_handler(self):
        state = self.model
        mouse_location = p.mouse.get_pos()
        if not self.game_over:
            col = mouse_location[0] // k.SQUARE_SIZE
            row = mouse_location[1] // k.SQUARE_SIZE
            if self.square_clicked == (row, col) or col >= 8:
                self.square_clicked = ()
                self.last_clicks = []
            else:
                self.square_clicked = (row, col)
                if not (state.board[row][col] == k.empty and len(self.last_clicks) == 0):
                    self.last_clicks.append(self.square_clicked)
            if len(self.last_clicks) == 2 and self.human_turn:
                move = chess_engine.Move(self.last_clicks[0], self.last_clicks[1], state)
                for i in range(len(self.valid_moves)):
                    if move == self.valid_moves[i]:
                        state.make_move(self.valid_moves[i])
                        self.move_made = True
                        self.animate = True
                        self.square_clicked = ()
                        self.last_clicks = []
                if not self.move_made:
                    self.last_clicks = [self.square_clicked]
        else:
            if self.view.return_main_menu_button.collidepoint((mouse_location[0], mouse_location[1])):
                k.make_option_sound()
                main.main()
            if self.view.save_pgn_button.collidepoint((mouse_location[0], mouse_location[1])) and not self.saved_game:
                k.make_option_sound()
                pgn_text = k.draw if self.model.stalemate else k.black_win if self.model.white_moves else k.white_win
                self.save_game(pgn_text, user_save=True)
                self.saved_game = True

    def ai_vs_ai_handler(self):
        self.player_one = False
        self.player_two = False
        self.run_game(k.ai_vs_ai_caption, False, False)

    def white_vs_ai_handler(self):
        self.player_one = True
        self.player_two = False
        self.run_game(k.white_vs_ai_caption, False, False)

    def ai_vs_black_handler(self):
        self.player_one = False
        self.player_two = True
        self.run_game(k.ai_vs_black_caption, False, False)

    def practice_handler(self):
        self.player_one = True
        self.player_two = True
        self.run_game(k.practice_caption, False, False)

    def import_handler(self):
        self.player_one = False
        self.player_two = False
        self.run_game(k.pgn_caption, True, False)

    def customizer_handler(self):
        self.view.run_customizer()

    def classifier_handler(self):
        self.view.run_classifier()

    def difficulty_handler(self):
        k.difficulty_clicker += 1
        if k.difficulty_clicker % 3 == 0:
            k.depth = 3
            main.main()
        elif k.difficulty_clicker % 3 == 1:
            k.depth = 4
            main.main()
        elif k.difficulty_clicker % 3 == 2:
            k.depth = 2
        main.main()

    def engine_handler(self):
        k.engine_used = not k.engine_used
        main.main()

    def random_opening_handler(self):
        self.player_one = False
        self.player_two = False
        self.run_game("Random Opening (AI)", True, True)

    def features_handler(self):
        main.main()

    def algorithm_handler(self):
        k.algorithm_count += 1
        k.current_algorithm = k.algorithms[k.algorithm_count % len(k.algorithms)]
        if 'id' in k.current_algorithm:
            split_algorithm = k.current_algorithm.split('_')
            k.timeout = int(split_algorithm[-1])
        main.main()

    def play_game(self):
        """Wait for user to select an option
           Draw main menu
        """
        self.view.draw_main_menu()
        mx, my = p.mouse.get_pos()

        for button in k.buttons:
            if p.Rect(k.buttons[button]).collidepoint((mx, my)) and button != k.disable_engine_button:
                k.make_option_sound()
                self.handler_functions[button]()

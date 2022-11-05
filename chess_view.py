import sys
import os
import pygame as p
import json
from pygame.locals import *
import chess_piece_classifier
import chess_engine as e
import chess_main as main
import chess_controller
import chess_constants as k
import threading
import numpy as np
import webbrowser
from tkinter import *
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


class View:
    """Draws every GUI element
       (board, pieces, buttons, windows, etc.)
    """
    def __init__(self):
        p.init()
        self.IMAGES = {}
        self.screen = p.display.set_mode((k.MENU_WIDTH, k.MENU_HEIGHT))
        self.clock = p.time.Clock()
        self.chosen_option = False
        self.piece_change_counter = 0
        self.kings_classified = False
        self.return_main_menu_button = None
        self.save_pgn_button = None
        self.clicked = False
        self.mx = self.my = None
        self.color_count = 0
        self.pieces_count = 0
        self.thread_started = False
        self.castle_flag_white = self.castle_flag_black = False
        self.castling_right_white = self.castling_right_black = False
        self.flip_board = False
        self.root = None
        self.opening_listbox = None
        self.opening_button = None
        self.opening_label = None
        self.chosen_opening = None
        p.display.set_icon(k.icon)

    def load_images(self):
        """Scales the chess pieces to
           SQUARE_SIZE x SQUARE_SIZE
        """
        for piece in k.pieces:
            self.IMAGES[piece] = p.transform.scale(
                p.image.load(f"images/pieces/{k.current_piece_skin}/" + piece + ".png"),
                (k.SQUARE_SIZE, k.SQUARE_SIZE))

    def draw_squares(self):
        """Draws the board (without pieces)
        """
        for row in range(k.DIMENSION):
            for column in range(k.DIMENSION):
                color = k.dark_sq_color if (row + column) % 2 == 1 else k.light_sq_color
                p.draw.rect(self.screen, color, p.Rect(column * k.SQUARE_SIZE, row * k.SQUARE_SIZE,
                                                       k.SQUARE_SIZE, k.SQUARE_SIZE))

    def draw_classified_squares(self):
        """Draws the classified board (without pieces)
        """
        for row in range(8):
            for column in range(8):
                color = k.dark_sq_color if (row + column) % 2 == 1 else k.light_sq_color
                p.draw.rect(self.screen, color, p.Rect(k.predicted_offset_x + column * k.SQ_SIZE_C,
                                                       k.predicted_offset_y + row * k.SQ_SIZE_C,
                                                       k.SQ_SIZE_C, k.SQ_SIZE_C))

    def draw_classified_pieces(self, classifier):
        """Draws the classified pieces
           Checks if the board is valid (has 1 wK and 1 bK)

           Keyword arguments:
           classifier -- the object containing classified board
                         and king location
        """
        wk_count = 0
        bk_count = 0
        for row in range(8):
            for column in range(8):
                if classifier.work != 0:
                    piece = classifier.predicted_board[row][column]
                    if piece == 'wK':
                        wk_count += 1
                    if piece == 'bK':
                        bk_count += 1
                else:
                    piece = k.sample_board[row][column]
                if piece != k.empty:
                    self.screen.blit(p.transform.scale(self.IMAGES[piece], (k.SQ_SIZE_C, k.SQ_SIZE_C)),
                                     p.Rect(k.predicted_offset_x + column * k.SQ_SIZE_C,
                                            k.predicted_offset_y + row * k.SQ_SIZE_C,
                                            k.SQ_SIZE_C, k.SQ_SIZE_C))
        self.kings_classified = True if wk_count == 1 and bk_count == 1 else False

    def draw_sample_board(self):
        """Draws a sample board in the left part
           of the classifier menu (Ruy Lopez)
        """
        for row in range(8):
            for column in range(8):
                color = k.dark_sq_color if (row + column) % 2 == 1 else k.light_sq_color
                piece = k.default_board[row][column]
                p.draw.rect(self.screen, color, p.Rect(k.customizer_offset_x + column * k.SQ_SIZE_C,
                                                       k.customizer_offset_y + row * k.SQ_SIZE_C,
                                                       k.SQ_SIZE_C, k.SQ_SIZE_C))
                if piece != k.empty:
                    self.screen.blit(p.transform.scale(self.IMAGES[piece], (k.SQ_SIZE_C, k.SQ_SIZE_C)),
                                     p.Rect(k.customizer_offset_x + column * k.SQ_SIZE_C,
                                            k.customizer_offset_y + row * k.SQ_SIZE_C,
                                            k.SQ_SIZE_C, k.SQ_SIZE_C))

    def draw_pieces(self, screen, board):
        """Checks game state and updates
           the current board (can also set coordinates
           if the option is chosen)

           Keyword arguments:
           screen -- pygame screen object
           board  -- game state chess board
        """
        for row in range(k.DIMENSION):
            for col in range(k.DIMENSION):
                if row == 7 and k.coordinates:
                    text_object = k.text_font_end_message.render(k.cols_to_files[col], True, k.text_color)
                    self.screen.blit(text_object,
                                     p.Rect(col * k.SQUARE_SIZE + k.coordinates_x,
                                            row * k.SQUARE_SIZE + k.coordinates_y,
                                            k.SQUARE_SIZE, k.SQUARE_SIZE))

                if col == 0 and k.coordinates:
                    text_object = k.text_font_end_message.render(k.rows_to_ranks[row], True, k.text_color)
                    self.screen.blit(text_object,
                                     p.Rect(col * k.SQUARE_SIZE,
                                            row * k.SQUARE_SIZE + k.coordinates_y,
                                            k.SQUARE_SIZE, k.SQUARE_SIZE))
                piece = board[row][col]
                if piece != k.empty:
                    screen.blit(self.IMAGES[piece],
                                p.Rect(col * k.SQUARE_SIZE,
                                       row * k.SQUARE_SIZE,
                                       k.SQUARE_SIZE, k.SQUARE_SIZE))

    def draw_text(self, text, x, y):
        """Displays text message after
           the game is over

           Keyword arguments:
           text -- string to be displayed
           x    -- x coordinate of text location
           y    -- y coordinate of text location
        """
        text_object = k.text_font_end_message.render(text, True, k.light_sq_color)
        message_rect = p.Rect((x - text_object.get_width()) // 2,
                              (y - text_object.get_height()) // 2,
                              text_object.get_width(),
                              text_object.get_height())

        p.draw.rect(self.screen, k.text_color, message_rect)

        text_location = p.Rect(0, 0, x, y).move(
            x // 2 - text_object.get_width() // 2,
            y // 2 - text_object.get_height() // 2)
        self.screen.blit(text_object, text_location)
        return message_rect

    def draw_menu_text(self, text, text_color, x, y):
        """Displays text message in
           the classifier menu

           Keyword arguments:
           text       -- string to be displayed
           text_color -- color of the text
           x          -- x coordinate of text location
           y          -- y coordinate of text location
        """
        text_obj = k.font.render(text, True, text_color)
        text_rect = text_obj.get_rect()
        text_rect.topleft = (x, y)
        self.screen.blit(text_obj, text_rect)

    def erase_menu_text(self, text, x, y):
        """Erases evaluation bar text
           in order to write new values
           (that's how pygame works)

           Keyword arguments:
           text -- string to be displayed
           x    -- x coordinate of text location
           y    -- y coordinate of text location
        """
        text_rect = text.get_rect()
        text_rect.topleft = (x, y)
        self.screen.fill(k.dark_sq_color, text_rect)

    def set_menu_screen(self):
        """Displays the current algorithm
           and depth in the main menu
        """
        p.display.set_caption(k.menu_caption)
        self.screen.fill(k.menu_bg_color)
        self.screen.blit(k.logo, k.logo_coord)
        self.draw_centered_text(f'Algorithm: {k.current_algorithm} Depth: {k.depth}', k.eval_text_color, k.MENU_WIDTH,
                                k.algorithm_depth_offset_y, k.menu_bg_color)

    def draw_back_button(self):
        """Draws a button in the classifier menu
           that takes the user back in main menu
        """
        p.draw.circle(self.screen, k.dark_sq_color, k.back_button_play_circle, k.spacing_y)
        self.screen.blit(k.back_icon, k.back_button_play)

    def draw_main_menu(self):
        """While the user hasn't chosen an option
           the main menu will be continuosly drawn
        """
        self.set_menu_screen()
        while not self.chosen_option:
            for button in k.buttons:
                if button != k.disable_engine_button:
                    p.draw.rect(self.screen, k.button_color, p.Rect(k.buttons[button]))
                    self.screen.blit(p.image.load(f'images/buttons/{button}.png'), k.buttons[button])

            if k.engine_used:
                p.draw.rect(self.screen, k.button_color, p.Rect(k.buttons[k.disable_engine_button]))
                self.screen.blit(p.image.load(f'images/buttons/{k.disable_engine_button}.png'),
                                 k.buttons[k.disable_engine_button])

            for event in p.event.get():
                if event.type == QUIT:
                    p.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        p.quit()
                        sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    for button in k.buttons:
                        mx, my = p.mouse.get_pos()
                        if p.Rect(k.buttons[button]).collidepoint((mx, my)):
                            self.chosen_option = True

            p.display.update()
            self.clock.tick(60)

    def draw_suggested_moves(self, ai):
        """Illustrates the candidate moves that were
           considered by the search algorithm
           (on the right side of the screen)
           (if the engine is enabled)

           Keyword arguments:
           ai -- AI module of the application
        """
        if len(ai.candidate_moves) >= 1:
            for candidate_index in range(0, len(ai.candidate_moves)):
                if candidate_index <= k.max_candidate_engine_moves:
                    move_text = k.font_classifier.render(ai.candidate_moves[candidate_index][0],
                                                         True, k.eval_text_color)
                    text_region = p.Rect((k.MENU_WIDTH + k.engine_helper_offset_x +
                                          k.engine_helper_offset_x_it * candidate_index,
                                          k.engine_helper_text_y,
                                          move_text.get_width(),
                                          move_text.get_height()))
                    self.screen.blit(move_text, text_region)
                    text_region = text_region.move(0, k.engine_helper_offset_y)
                    score_text = k.font_classifier.render(ai.candidate_moves[candidate_index][1],
                                                          True, k.eval_text_color)
                    self.screen.blit(score_text, text_region)

    def update_progress_bar(self, classifier):
        """Draws the progress bar of the classifier menu
           that will appear after an image is selected

           Keyword arguments:
           classifier -- the object containing classified board
                         and king location (the progress made is
                         needed in order to update the bar)
        """
        progress = str("{:.1f}".format(classifier.work / k.MAX_ITERATIONS * 100))
        text_object = k.font_classifier.render(str(f'{progress} %'), True, k.text_color)
        text_location = p.Rect(k.CLASSIFY_WIDTH // 2, k.classifier_text_height,
                               k.CLASSIFY_WIDTH // 2, k.CLASSIFY_HEIGHT // 2)
        self.screen.blit(text_object, text_location)

    def draw_classifier_elements(self, classifier, loading_bar_width):
        """Continuosly displays the predicted board and pieces
           in the classifier menu of the application

           Keyword arguments:
           classifier        -- the object containing classified board
                                and king location
           loading_bar_width -- the size of the loading bar (depending
                                on the progress made)
        """
        p.draw.rect(self.screen, k.progress_bar_color,
                    p.Rect(0, 0, loading_bar_width, k.loading_bar_height))

        p.draw.circle(self.screen, k.dark_sq_color, k.back_button_circle, k.spacing_y)
        self.screen.blit(k.back_icon, k.back_button)
        p.draw.circle(self.screen, k.dark_sq_color, k.documentation_circle, k.spacing_y)
        self.screen.blit(k.documentation_icon, k.documentation_button)
        self.draw_menu_text(k.classifier_arrows, k.text_color, k.arrow_x, k.arrow_y)
        self.draw_classified_squares()
        self.draw_classified_pieces(classifier)

    def mouse_handler_classifier(self, classifier, delete_piece):
        """Updates the predicted board, in case an error appeared
           or the user wants to play a different board

           Keyword arguments:
           classifier   -- the object containing classified board
                           and king location
           delete_piece -- true on right click event and false
                           otherwise
        """
        mouse_location = p.mouse.get_pos()
        if mouse_location[0] >= k.predicted_offset_x and \
                k.predicted_offset_y <= mouse_location[1] <= k.predicted_offset_x + 10:
            col = (mouse_location[0] - k.predicted_offset_x) // k.SQ_SIZE_C
            row = (mouse_location[1] - k.predicted_offset_y) // k.SQ_SIZE_C
            self.piece_change_counter += 1
            if not delete_piece:
                classifier.predicted_board[row][col] = k.pieces[self.piece_change_counter % len(k.pieces)]
            else:
                classifier.predicted_board[row][col] = k.empty

    def draw_centered_text(self, text, text_color, x, y, button_color):
        """Draws a text on the center of the screen

           Keyword arguments:
           text_color   -- string to be displayed
           color        -- color of the text
           x            -- x coordinate of text button location
           y            -- y coordinate of text button location
           button_color -- the color of the text area
        """
        text_object_info = k.font_classifier.render(text, True, text_color)
        text_region = p.Rect((x - text_object_info.get_width()) // 2,
                             y,
                             text_object_info.get_width(),
                             text_object_info.get_height())
        p.draw.rect(self.screen, button_color, text_region)
        self.screen.blit(text_object_info, text_region)

    def back_button_classifier_handler(self):
        if p.Rect(k.back_button).collidepoint((self.mx, self.my)):
            if p.mouse.get_pressed(3)[0] == 1 and self.clicked is False:
                self.clicked = True
                main.main()

    def documentation_handler(self):
        if p.Rect(k.documentation_button).collidepoint((self.mx, self.my)):
            if p.mouse.get_pressed(3)[0] == 1 and self.clicked is False:
                self.clicked = True
                webbrowser.open(k.github_classifier_page)

    def import_image_handler(self, classifier_thread):
        if p.Rect(k.import_button[1]).collidepoint((self.mx, self.my)) and not self.thread_started:
            if p.mouse.get_pressed(3)[0] == 1 and self.clicked is False:
                self.clicked = True
                self.thread_started = True
                classifier_thread.setDaemon(True)
                classifier_thread.start()

    def draw_classifier_buttons(self):
        button_index = 0
        for text in k.classifier_info:
            text_object_info = k.font_classifier.render(str(text), True, k.text_color)
            k.classifier_info[text][0] = p.Rect((k.CLASSIFY_WIDTH - text_object_info.get_width()) // 2,
                                                k.info_y + button_index * k.spacing_y,
                                                text_object_info.get_width(),
                                                text_object_info.get_height())
            button_index += 1
            if k.classifier_info[text][1] is False:
                p.draw.rect(self.screen, k.button_color, k.classifier_info[text][0])
            else:
                p.draw.rect(self.screen, k.button_color_clicked, k.classifier_info[text][0])
            self.screen.blit(text_object_info, k.classifier_info[text][0])

    def white_castle_handler(self, controller):
        if p.Rect(k.classifier_info["May White Castle?"][0]).collidepoint((self.mx, self.my)):
            if self.castling_right_white:
                k.imported = False
                self.clicked = True
                controller.model.castling_flags = e.CastleFlags(True, True, True, True) \
                    if self.castle_flag_black else e.CastleFlags(True, False, True, False)
                self.castle_flag_white = not self.castle_flag_white
                k.classifier_info["May White Castle?"][1] = self.castle_flag_white

    def black_castle_handler(self, controller):
        if p.Rect(k.classifier_info["May Black Castle?"][0]).collidepoint((self.mx, self.my)):
            if self.castling_right_black:
                k.imported = False
                self.clicked = True
                current_castling_rights = e.CastleFlags(True, True, True, True) \
                    if self.castle_flag_white else e.CastleFlags(False, True, False, True)
                controller.model.castling_flags = current_castling_rights
                self.castle_flag_black = not self.castle_flag_black
                k.classifier_info["May Black Castle?"][1] = self.castle_flag_black

    def turn_classifier_handler(self, controller):
        if p.Rect(k.classifier_info["Black to move?"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            controller.model.white_moves = not controller.model.white_moves
            k.classifier_info["Black to move?"][1] = not controller.model.white_moves

    def classifier_practice_handler(self, controller):
        if p.Rect(k.classifier_info["Continue (Practice)"][0]).collidepoint((self.mx, self.my)):
            if self.kings_classified:
                self.clicked = True
                k.classifier_info["Continue (Practice)"][1] = self.clicked
                controller.practice_handler()

    def classifier_ai_vs_white_handler(self, controller):
        if p.Rect(k.classifier_info["Continue (vs AI) (White)"][0]).collidepoint((self.mx, self.my)):
            if self.kings_classified:
                self.clicked = True
                k.classifier_info["Continue (vs AI) (White)"][1] = self.clicked
                controller.white_vs_ai_handler()

    def classifier_ai_vs_black_handler(self, controller):
        if p.Rect(k.classifier_info["Continue (vs AI) (Black)"][0]).collidepoint((self.mx, self.my)):
            if self.kings_classified:
                self.clicked = True
                k.classifier_info["Continue (vs AI) (Black)"][1] = self.clicked
                controller.ai_vs_black_handler()

    def flip_handler(self, classifier):
        if p.Rect(k.classifier_info["White on top?"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            classifier.predicted_board = np.flip(classifier.predicted_board)
            self.flip_board = not self.flip_board
            k.classifier_info["White on top?"][1] = self.flip_board

    def classifier_ai_vs_ai_handler(self, controller):
        if p.Rect(k.classifier_info["Continue (AI vs AI)"][0]).collidepoint((self.mx, self.my)):
            if self.kings_classified:
                self.clicked = True
                k.classifier_info["Continue (AI vs AI)"][1] = self.clicked
                controller.ai_vs_ai_handler()

    def draw_classifier_info(self):
        """Draws classifier menu buttons (import, tutorial)
        """
        for text in k.classifier_info_text:
            text_object_info = k.font_classifier.render(str(f'{text}'),
                                                        True, k.text_color)
            self.screen.blit(text_object_info, k.classifier_info_text[text])

        resized_image = p.transform.scale(k.default_classifier_board, k.DEFAULT_IMAGE_SIZE)
        self.screen.blit(resized_image, k.imported_image_coordinates)

        p.draw.rect(self.screen, k.button_color, k.import_button[1])
        text_object_info = k.font_classifier.render(str(k.import_button[0]), True, k.text_color)
        k.import_button[1] = p.Rect((k.CLASSIFY_WIDTH - text_object_info.get_width()) // 2,
                                    k.info_y,
                                    text_object_info.get_width(),
                                    text_object_info.get_height())

        self.screen.blit(text_object_info, k.import_button[1])

    def run_classifier(self):
        """Classifier menu logic
           A thread will compute the classification process
           and the other one will upgrade the progress bar
        """
        k.imported = True
        p.display.set_caption(k.classifier_caption)
        width = k.CLASSIFY_WIDTH
        height = k.CLASSIFY_HEIGHT
        self.screen = p.display.set_mode((width, height))

        classifier = chess_piece_classifier.BayesClassifier(False, False)
        classifier.predicted_board = k.blank_board
        classifier_thread = threading.Thread(target=classifier.bayes)

        loading_finished = False
        controller = chess_controller.ChessController(self)
        controller.model.import_mode = True
        controller.model.castling_flags = e.CastleFlags(False, False, False, False)

        while True:
            (self.mx, self.my) = p.mouse.get_pos()
            for event in p.event.get():
                if event.type == p.QUIT:
                    p.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        (self.mx, self.my) = p.mouse.get_pos()
                        if classifier.work == k.MAX_ITERATIONS:
                            self.mouse_handler_classifier(classifier, False)
                    else:
                        self.mouse_handler_classifier(classifier, True)

            self.screen.fill(k.classifier_screen_color)

            p.draw.rect(self.screen, k.dark_sq_color,
                        k.classifier_footer)

            if p.mouse.get_pressed(3)[0] == 0:
                self.clicked = False

            self.back_button_classifier_handler()
            self.documentation_handler()
            self.import_image_handler(classifier_thread)

            if not loading_finished:
                loading_bar_width = classifier.work / k.MAX_ITERATIONS * k.CLASSIFY_WIDTH
                self.draw_classifier_elements(classifier, loading_bar_width)

                if classifier.imported_image is not None and classifier.imported_image != 0:
                    resized_image = p.transform.scale(classifier.imported_image, k.DEFAULT_IMAGE_SIZE)
                    self.screen.blit(resized_image, k.imported_image_coordinates)

                    if loading_bar_width != 0:
                        self.update_progress_bar(classifier)

                    if classifier.work == k.MAX_ITERATIONS:
                        self.draw_classified_pieces(classifier)
                        self.draw_classifier_buttons()

                        if not self.kings_classified:
                            self.draw_centered_text(k.king_error_text, k.text_color, k.CLASSIFY_WIDTH,
                                                    k.warning_y, k.warning_color)

                        self.castling_right_white = False if \
                            classifier.white_king_location != k.white_king_location else True
                        self.castling_right_black = False if \
                            classifier.black_king_location != k.black_king_location else True

                        if p.mouse.get_pressed(3)[0] == 1 and not self.clicked:
                            self.white_castle_handler(controller)
                            self.black_castle_handler(controller)
                            self.turn_classifier_handler(controller)
                            self.classifier_practice_handler(controller)
                            self.classifier_ai_vs_white_handler(controller)
                            self.classifier_ai_vs_black_handler(controller)
                            self.classifier_ai_vs_ai_handler(controller)
                            self.flip_handler(classifier)
                        controller.model.board = classifier.predicted_board
                else:
                    if classifier.imported_image != 0:
                        self.draw_classifier_info()
                    else:
                        break
            p.display.update()
            self.clock.tick(k.MAX_FPS)

    def back_button_handler(self):
        if p.Rect(k.back_button_customizer).collidepoint((self.mx, self.my)):
            self.clicked = True
            main.main()

    def change_color_handler(self):
        if p.Rect(k.customizer_info_text["> Change Color"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            self.color_count += 1
            k.dark_sq_color = k.board_colors[self.color_count % len(k.board_colors)]
            k.customizer_info_text["> Change Color"][1] = not k.customizer_info_text["> Change Color"][1]

    def change_piece_handler(self):
        if p.Rect(k.customizer_info_text["> Change Pieces"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            self.pieces_count += 1
            k.current_piece_skin = k.pieces_skins[self.pieces_count % len(k.pieces_skins)]

    def animation_handler(self):
        if p.Rect(k.customizer_info_text["> Toggle Animations"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            k.animations = not k.animations
            k.customizer_info_text["> Toggle Animations"][1] = not k.animations

    def sound_effect_handler(self):
        if p.Rect(k.customizer_info_text["> Enable Sound Effects"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            k.move_sounds = not k.move_sounds
            k.customizer_info_text["> Enable Sound Effects"][1] = k.move_sounds

    def coordinates_handler(self):
        if p.Rect(k.customizer_info_text["> Enable Board Coordinates"][0]).collidepoint((self.mx, self.my)):
            self.clicked = True
            k.coordinates = not k.coordinates
            k.customizer_info_text["> Enable Board Coordinates"][1] = k.coordinates

    def draw_customizer_footer(self):
        self.screen.fill(k.classifier_screen_color)
        p.draw.rect(self.screen, k.dark_sq_color,
                    k.customizer_footer)
        p.draw.circle(self.screen, k.dark_sq_color, k.back_button_circle, k.back_button_radius)
        self.screen.blit(k.back_icon, k.back_button_customizer)

    def draw_customizer_buttons(self):
        button_index = 0
        for text in k.customizer_info_text:
            text_object_info = k.font_classifier.render(str(f'{text}'),
                                                        True, k.text_color)
            k.customizer_info_text[text][0] = p.Rect((k.BOARD_WIDTH - text_object_info.get_width()) // 2,
                                                     k.customizer_button_offset_x + button_index * k.spacing_y,
                                                     text_object_info.get_width(),
                                                     text_object_info.get_height())
            button_index += 1
            if k.customizer_info_text[text][1] is False:
                p.draw.rect(self.screen, k.button_color, k.customizer_info_text[text][0])
            else:
                p.draw.rect(self.screen, k.dark_sq_color, k.customizer_info_text[text][0])
            self.screen.blit(text_object_info, k.customizer_info_text[text][0])

    def run_customizer(self):
        """Customizer menu logic
        """
        p.display.set_caption(k.customizer_caption)
        width = k.MENU_WIDTH
        height = k.MENU_HEIGHT
        self.screen = p.display.set_mode((width, height))
        (self.mx, self.my) = p.mouse.get_pos()

        while True:
            for event in p.event.get():
                if event.type == p.QUIT:
                    p.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        (self.mx, self.my) = p.mouse.get_pos()

            self.draw_customizer_footer()
            self.draw_customizer_buttons()
            self.load_images()
            self.draw_sample_board()

            if p.mouse.get_pressed(3)[0] == 0:
                self.clicked = False

            if p.mouse.get_pressed(3)[0] == 1 and not self.clicked:
                self.back_button_handler()
                self.change_color_handler()
                self.change_piece_handler()
                self.animation_handler()
                self.sound_effect_handler()
                self.coordinates_handler()
            p.display.update()
            self.clock.tick(k.MAX_FPS)

    def select_opening(self):
        self.opening_label.config(text=self.opening_listbox.get(ANCHOR))
        self.chosen_opening = self.opening_label["text"]
        self.root.destroy()

    def run_opening_book(self):
        """Opening book window
           The user will have to choose an
           opening to study (otherwise a random
           one is chosen by default)
        """
        while self.chosen_opening is None:
            with open(r"openings//openings.json") as json_file:
                data = json.load(json_file)
                self.root = Tk()
                self.root.title('Chess Openings')
                self.root.geometry('500x250')
                self.root.configure(bg='lavender')
                self.opening_listbox = Listbox(self.root)
                self.opening_listbox.pack(padx=5, pady=15)
                self.opening_listbox.config(width=300, height=10)
                self.opening_button = Button(self.root, text="Select", command=self.select_opening)
                self.opening_button.pack(pady=10)
                self.opening_label = Label(self.root, text='')
                self.opening_label.pack(pady=5)
                self.opening_listbox.insert("end", "Random")

                for index in range(0, len(data)):
                    self.opening_listbox.insert("end", data[index]["name"])
                self.root.mainloop()

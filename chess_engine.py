import chess_constants as k
import chess


class GameState:
    """Core of the application
       Stores every information
       about the game state, makes
       / unmakes a move and
       returns valid moves
    """
    def __init__(self):
        k.flip = False
        if not k.flip:
            self.board = [["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
                          ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
                          ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                          ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                          ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                          ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
                          ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
                          ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        else:
            self.board = k.default_flipped_board

        self.move_functions = {'P': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                               'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.white_moves = True
        self.move_log = []
        self.pgn_log = []
        self.white_king_location = k.white_king_location if not k.flip else k.black_king_location
        self.black_king_location = k.black_king_location if not k.flip else k.white_king_location
        self.checkmate = False
        self.stalemate = False
        self.draw_rule = False
        self.fifty_draw_counter = 0
        self.checked = False
        self.white_castled = False
        self.black_castled = False
        self.pins = []
        self.checks = []
        self.en_passant = ()
        self.en_passant_coordinates = None
        self.en_passant_log = [self.en_passant]
        self.valid_moves_counter = 0
        self.castling_flags = CastleFlags(True, True, True, True)
        self.castling_log = [CastleFlags(True, True, True, True)]
        self.eventual_ambiguous_moves = []
        self.last_ambiguous_moves = []
        self.board_history = []
        self.undo_flag = False
        self.chessboard = chess.Board()
        self.fen_notation = None
        self.pawn_moved_white = False
        self.pawn_moved_black = False
        self.white_bishop_counter = 2
        self.black_bishop_counter = 2
        self.repetition_punish = [False, False]
        self.temp_castling_flags = None
        self.developing_white_moves = 0
        self.developing_black_moves = 0
        self.position_score = 0
        self.update_board_fen()

    def make_move(self, move):
        """Makes the given move and updates
           the game state

           Keyword arguments:
           move -- Move object (start row, start col, end row, end col)
        """
        self.last_ambiguous_moves = self.eventual_ambiguous_moves
        self.board[move.start_row][move.start_col] = k.empty
        self.board[move.end_row][move.end_col] = move.piece_to_move
        self.position_score = 0

        if move in self.move_log:
            if self.white_moves:
                self.repetition_punish[0] = True
            else:
                self.repetition_punish[1] = True

        self.move_log.append(move)
        if move.piece_to_move[1] == "P" or move.place_to_go[1] == "P":
            self.fifty_draw_counter = 0
            if self.white_moves:
                self.pawn_moved_white = True
            else:
                self.pawn_moved_black = True
        else:
            self.fifty_draw_counter += 1
            self.pawn_moved_white = False
            self.pawn_moved_black = False

        self.white_moves = not self.white_moves

        if move.place_to_go == "bB":
            self.black_bishop_counter -= 1

        if move.place_to_go == "wB":
            self.white_bishop_counter -= 1

        if move.piece_to_move == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_to_move == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_to_move[0] + "Q"

        if move.en_passant_move:
            self.board[move.start_row][move.end_col] = k.empty

        if move.piece_to_move[1] == "P" and abs(move.end_row - move.start_row) == 2:
            self.en_passant = ((move.start_row + move.end_row) // 2,
                               move.end_col)
            self.en_passant_coordinates = k.get_file_rank_notation((move.start_row + move.end_row) // 2, move.end_col)
        else:
            self.en_passant = ()
            self.en_passant_coordinates = None

        if move.castle_move:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = k.empty
            else:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = k.empty
            if self.white_moves:
                self.black_castled = True
            else:
                self.white_castled = True

        move_pgn = move.get_chess_notation()

        # if not self.white_moves:
        #     if move_pgn in k.developing_moves_white:
        #         k.developing_moves_white.remove(move_pgn)
        #         self.developing_white_moves += 1
        #
        # if self.white_moves:
        #     if move_pgn in k.developing_moves_black:
        #         k.developing_moves_black.remove(move_pgn)
        #         self.developing_black_moves += 1

        if self.in_check():
            move_pgn += "+"

        self.pgn_log.append(move_pgn)
        self.en_passant_log.append(self.en_passant)

        self.temp_castling_flags = self.update_castle_flags(move)
        self.castling_log.append(self.temp_castling_flags)
        self.castling_flags = self.temp_castling_flags
        repetition_counter = self.update_board_fen()

        if repetition_counter == 3 or self.fifty_draw_counter == 50:
            self.draw_rule = True

    def undo_move(self):
        """Inverse make_move operation
           Sets the game state back to it's last
        """
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.pgn_log.pop()
            self.board_history.pop()
            if self.fifty_draw_counter != 0:
                self.fifty_draw_counter -= 1
            self.draw_rule = False
            self.undo_flag = True
            self.pawn_moved_black = False
            self.pawn_moved_white = False
            self.board[move.start_row][move.start_col] = move.piece_to_move
            self.board[move.end_row][move.end_col] = move.place_to_go
            self.white_moves = not self.white_moves

            if move.piece_to_move == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_to_move == "bK":
                self.black_king_location = (move.start_row, move.start_col)

            if move.place_to_go == "bB":
                self.black_bishop_counter += 1
            if move.place_to_go == "wB":
                self.white_bishop_counter += 1

            if move.en_passant_move:
                self.board[move.end_row][move.end_col] = k.empty
                self.board[move.start_row][move.end_col] = move.place_to_go

            self.en_passant_log.pop()
            self.en_passant = self.en_passant_log[-1]

            self.castling_log.pop()
            self.castling_flags = self.castling_log[-1]

            if move.castle_move:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = k.empty
                else:
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = k.empty
                if move.castle_move:
                    if self.white_moves:
                        self.white_castled = False
                    else:
                        self.black_castled = False
            self.checkmate = False
            self.stalemate = False

    def update_castle_flags(self, move):
        """Sets the castle flags to false
           in case a king / rook moved

           Keyword arguments:
           move -- Move object (start row, start col, end row, end col)
        """
        temp = CastleFlags(self.castling_flags.wks, self.castling_flags.bks,
                           self.castling_flags.wqs, self.castling_flags.bqs)
        if move.place_to_go == "wR":
            if move.end_col == 0:
                temp.wqs = False
            elif move.end_col == 7:
                temp.wks = False
        elif move.place_to_go == "bR":
            if move.end_col == 0:
                temp.bqs = False
            elif move.end_col == 7:
                temp.bks = False

        if move.piece_to_move == 'wK':
            temp.wqs = False
            temp.wks = False
        elif move.piece_to_move == 'bK':
            temp.bqs = False
            temp.bks = False
        elif move.piece_to_move == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:
                    temp.wqs = False
                elif move.start_col == 7:
                    temp.wks = False
        elif move.piece_to_move == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:
                    temp.bqs = False
                elif move.start_col == 7:
                    temp.bks = False
        return temp

    def get_all_possible_moves(self):
        """Calls every move function in
           order to get every possible move
           (invalid ones too)
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                piece_color = self.board[row][col][0]
                if (piece_color == 'w' and self.white_moves) or (piece_color == 'b' and not self.white_moves):
                    self.move_functions[self.board[row][col][1]](row, col, moves)
        return moves

    def king_helper(self):
        """Returns the pinned squares, the squares
           which generate check (with the direction of the
           attacking piece) and the state of the king
        """
        checked = False
        pins = []
        checks = []
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))

        (start_row, start_col) = self.white_king_location if self.white_moves else self.black_king_location
        enemy = "b" if self.white_moves else "w"
        ally = "w" if self.white_moves else "b"

        for i in range(len(directions)):
            d = directions[i]
            eventual_pin = ()
            for j in range(1, 8):
                end_row = start_row + d[0] * j
                end_col = start_col + d[1] * j
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    # the first piece between the king an an `eventual enemy` might be pinned
                    if end_piece[0] == ally and end_piece[1] != "K":
                        if eventual_pin == ():
                            eventual_pin = (end_row, end_col, d[0], d[1])
                        else:
                            # if the second piece is found, there's no pin
                            break
                    elif end_piece[0] == enemy:
                        # In case an enemy piece is found, there are 5 cases:
                        # 1) orthogonal direction and piece is a rook (first 3 directions)
                        # 2) diagonal direction and piece is a bishop
                        # 3) pawn pin (can't go to a place defended by a pawn)
                        # 4) every direction and piece is a queen
                        # 5) kings (can't face each other)
                        enemy_piece = end_piece[1]
                        if (0 <= i <= 3 and enemy_piece == "R") or (4 <= i <= 7 and enemy_piece == "B") or (
                                j == 1 and enemy_piece == "P" and (
                                (enemy == "w" and 6 <= i <= 7 and not k.flip) or
                                (enemy == "b" and 4 <= i <= 5 and not k.flip) or
                                (enemy == "b" and 6 <= i <= 7 and k.flip) or
                                (enemy == "w" and 4 <= i <= 5 and k.flip))) or (
                                enemy_piece == "Q") or (j == 1 and enemy_piece == "K"):
                            if eventual_pin == ():
                                checked = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:
                                pins.append(eventual_pin)
                                break
                        else:
                            break
                else:
                    break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy and end_piece[1] == "N":
                    checked = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return checked, pins, checks

    def get_valid_moves(self):
        """After pins and checks are calculated
           Remove illegal moves and get castle moves (if any)
           Set state to checkmate / stalemate if no valid moves
        """
        temp_castle_rights = CastleFlags(self.castling_flags.wks, self.castling_flags.bks,
                                         self.castling_flags.wqs, self.castling_flags.bqs)

        self.eventual_ambiguous_moves = []
        moves = []
        self.checked, self.pins, self.checks = self.king_helper()

        (king_row, king_col) = self.white_king_location if self.white_moves else self.black_king_location

        if self.checked:
            if len(self.checks) == 1:
                moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break

                for i in range(len(moves)-1, -1, -1):
                    if moves[i].piece_to_move[1] != "K":
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:
                self.get_king_moves(king_row, king_col, moves)
        else:
            moves = self.get_all_possible_moves()
            if not k.imported:
                if self.white_moves:
                    self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves)
                else:
                    self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.castling_flags = temp_castle_rights
        self.valid_moves_counter = len(moves)
        return moves

    def in_check(self):
        """Return true if the king of
           the current play is
           under attack (checked)
        """
        if self.white_moves:
            return self.square_attacked(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.square_attacked(self.black_king_location[0], self.black_king_location[1])

    def square_attacked(self, row, col):
        """Return true if the square
           with the coordinates (row, col)
           is attacked by any enemy piece

           Keyword arguments:
           row -- (0-7)
           col -- (0-7)
        """
        self.white_moves = not self.white_moves
        opponent_moves = self.get_all_possible_moves()
        self.white_moves = not self.white_moves
        for move in opponent_moves:
            if move.end_row == row and move.end_col == col:
                return True
        return False

    def get_pawn_moves(self, row, col, moves):
        """Appends the pawn moves to
           the final valid moves list
           removes eventual-pinned pieces

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        pinned = False
        pin_direction = ()

        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        king_row, king_col = self.white_king_location if self.white_moves else self.black_king_location
        increment = -1 if (self.white_moves and not k.flip) or\
                          (not self.white_moves and k.flip) else 1
        start_pos = 6 if (self.white_moves and not k.flip) or (not self.white_moves and k.flip) else 1
        enemy = "b" if self.white_moves else "w"

        if self.board[row + increment][col] == k.empty:
            if not pinned or pin_direction == (increment, 0):
                k.insert_move_ordering(moves, Move((row, col), (row + increment, col), self))
                if row == start_pos and self.board[row + 2 * increment][col] == k.empty:
                    k.insert_move_ordering(moves, Move((row, col), (row + 2 * increment, col), self))

        if col-1 >= 0:
            if not pinned or pin_direction == (increment, -1):
                if self.board[row + increment][col - 1][0] == enemy:
                    k.insert_move_ordering(moves, Move((row, col), (row + increment, col - 1), self))
                if (row + increment, col - 1) == self.en_passant:
                    attack_piece = block_piece = False
                    if king_row == row:
                        if king_col < col:
                            inside = range(king_col + 1, col - 1)
                            outside = range(col + 1, 8)
                        else:
                            inside = range(king_col - 1, col, -1)
                            outside = range(col - 2, -1, -1)
                        for i in inside:
                            if self.board[row][i] != k.empty:
                                block_piece = True
                        for i in outside:
                            square = self.board[row][i]
                            if square[0] == enemy and (square[1] == "R" or square[1] == "Q"):
                                attack_piece = True
                            elif square != k.empty:
                                block_piece = True
                    if not attack_piece or block_piece:
                        k.insert_move_ordering(moves,
                                               Move((row, col), (row + increment, col - 1), self, en_passant=True))

        if col + 1 <= 7:
            if not pinned or pin_direction == (increment, 1):
                if self.board[row + increment][col + 1][0] == enemy:
                    k.insert_move_ordering(moves, Move((row, col), (row + increment, col + 1), self))
                if (row + increment, col + 1) == self.en_passant:
                    attack_piece = block_piece = False
                    if king_row == row:
                        if king_col < col:
                            inside = range(king_col + 1, col)
                            outside = range(col + 2, 8)
                        else:
                            inside = range(king_col - 1, col + 1, -1)
                            outside = range(col - 1, -1, -1)
                        for i in inside:
                            if self.board[row][i] != k.empty:
                                block_piece = True
                        for i in outside:
                            square = self.board[row][i]
                            if square[0] == enemy and (square[1] == "R" or square[1] == "Q"):
                                attack_piece = True
                            elif square != k.empty:
                                block_piece = True
                    if not attack_piece or block_piece:
                        k.insert_move_ordering(moves,
                                               Move((row, col), (row + increment, col + 1), self, en_passant=True))

    def get_knight_moves(self, row, col, moves):
        """Appends the knight moves to
           the final valid moves list
           removes eventual-pinned pieces

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        pinned = False

        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        ally = "w" if self.white_moves else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if not pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally:
                        knight_move = Move((row, col), (end_row, end_col), self)
                        k.insert_move_ordering(moves, knight_move)
                        self.eventual_ambiguous_moves.append([end_row, end_col, f"N{'w' if self.white_moves else 'b'}"])

    def get_bishop_moves(self, row, col, moves):
        """Appends the bishop moves to
           the final valid moves list
           removes eventual-pinned pieces

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        pinned = False
        pin_direction = ()

        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemy = "b" if self.white_moves else "w"
        ally = "w" if self.white_moves else "b"
        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "xx":
                            k.insert_move_ordering(moves, Move((row, col), (end_row, end_col), self))
                            if self.board[row][col][1] == 'Q':
                                self.eventual_ambiguous_moves.append([end_row, end_col,
                                                                      str(self.board[row][col][1] + ally)])
                        elif end_piece[0] == enemy:
                            k.insert_move_ordering(moves, Move((row, col), (end_row, end_col), self))
                            if self.board[row][col][1] == 'Q':
                                self.eventual_ambiguous_moves.append([end_row, end_col,
                                                                      str(self.board[row][col][1] + ally)])
                            break
                        else:
                            break
                else:
                    break

    def get_rook_moves(self, row, col, moves):
        """Appends the rook moves to
           the final valid moves list
           removes eventual-pinned pieces

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        pinned = False
        pin_direction = ()

        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != "Q":
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy = "b" if self.white_moves else "w"
        ally = "w" if self.white_moves else "b"
        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == k.empty:
                            k.insert_move_ordering(moves, Move((row, col), (end_row, end_col), self))
                            self.eventual_ambiguous_moves.append([end_row, end_col,
                                                                  str(self.board[row][col][1] + ally)])
                        elif end_piece[0] == enemy:
                            k.insert_move_ordering(moves, Move((row, col), (end_row, end_col), self))
                            self.eventual_ambiguous_moves.append([end_row, end_col,
                                                                  str(self.board[row][col][1] + ally)])
                            break
                        else:
                            break
                else:
                    break

    def get_queen_moves(self, row, col, moves):
        """Appends the queen moves to
           the final valid moves list
           removes eventual-pinned pieces
           queen moves = bishop moves + rook moves

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    def get_king_moves(self, row, col, moves):
        """Appends the king moves to
           the final valid moves list
           removes eventual-pinned piece
           and updates the king location

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally = "w" if self.white_moves else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally:
                    if ally == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)

                    checked, pins, checks = self.king_helper()
                    if not checked:
                        k.insert_move_ordering(moves, Move((row, col), (end_row, end_col), self))

                    if ally == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def get_castle_moves(self, row, col, moves):
        """Returns valid castle moves

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        if self.square_attacked(row, col):
            return
        if (self.white_moves and self.castling_flags.wks) or (not self.white_moves and self.castling_flags.bks):
            self.get_king_side_castle_moves(row, col, moves)
        if (self.white_moves and self.castling_flags.wqs) or (not self.white_moves and self.castling_flags.bqs):
            self.get_queen_side_castle_moves(row, col, moves)

    def get_king_side_castle_moves(self, row, col, moves):
        """King side castling validator

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        if self.board[row][col + 1] == k.empty and self.board[row][col + 2] == k.empty:
            if not self.square_attacked(row, col + 1) and not self.square_attacked(row, col + 2):
                k.insert_move_ordering(moves, Move((row, col), (row, col + 2), self, castle=True))

    def get_queen_side_castle_moves(self, row, col, moves):
        """Queen side castling validator

           Keyword arguments:
           row   -- (0-7)
           col   -- (0-7)
           moves -- current valid moves
        """
        if self.board[row][col - 1] == k.empty \
                and self.board[row][col - 2] == k.empty \
                and self.board[row][col - 3] == k.empty:
            if not self.square_attacked(row, col - 1) and not self.square_attacked(row, col - 2):
                k.insert_move_ordering(moves, Move((row, col), (row, col - 2), self, castle=True))

    def update_board_fen(self):
        """Calculates the new FEN notation
           after a move is made and also
           computes some preciuous information
           for the evaluation function
        """
        identifier = ""
        for row in range(len(self.board)):
            counter = 0
            for col in range(len(self.board[row])):
                piece = self.board[row][col]
                if piece == k.empty:
                    counter += 1
                else:
                    piece_position_score = k.piece_position_scores[piece][row][col]
                    if piece[0] == "w":
                        self.position_score += k.piece_score[piece[1]] + piece_position_score * 0.05
                    elif piece[0] == "b":
                        self.position_score -= k.piece_score[piece[1]] + piece_position_score * 0.05
                    letter = piece[1].lower() if piece[0] == "b" else piece[1].upper()
                    if counter == 0:
                        identifier += letter
                    else:
                        identifier += str(counter) + letter
                    counter = 0
            if counter != 0:
                identifier += str(counter)
            if row != 7:
                identifier += '/'
        history_identifier = identifier
        self.board_history.append(history_identifier)

        identifier += ' w ' if self.white_moves else ' b '
        castling_symbols = ""
        if self.castling_flags.wks:
            castling_symbols += 'K'
        if self.castling_flags.wqs:
            castling_symbols += 'Q'
        if self.castling_flags.bks:
            castling_symbols += 'k'
        if self.castling_flags.bqs:
            castling_symbols += 'q'
        if castling_symbols != "":
            identifier += castling_symbols + " "
        else:
            identifier += "- "

        if self.en_passant_coordinates is not None:
            identifier += self.en_passant_coordinates + " "
        else:
            identifier += "- "

        identifier += str(self.fifty_draw_counter) + " "
        identifier += str(len(self.pgn_log) // 2 + 1)
        self.fen_notation = identifier
        self.chessboard = chess.Board(self.fen_notation)
        return self.board_history.count(history_identifier)


class Move:
    """Stores every information that
       a specific move needs
    """
    def __init__(self, start_square, end_square, state, en_passant=False, castle=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_to_move = state.board[self.start_row][self.start_col]
        self.place_to_go = state.board[self.end_row][self.end_col]
        self.is_pawn_promotion = (self.piece_to_move == "wP" and self.end_row == 0) or\
                                 (self.piece_to_move == "bP" and self.end_row == 7)
        self.en_passant_move = en_passant
        self.state = state
        self.castle_move = castle
        if self.en_passant_move:
            self.place_to_go = "wP" if self.piece_to_move == "bP" else "bP"
        self.move_score = self.calculate_mvvlva()
        self.id = str(self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col)

    def calculate_mvvlva(self):
        """Computes the Most Valuable Victim
           Least Valuable Attacker score
           for move ordering
        """
        mvv_lva_scores = {"Q": 500, "R": 400, "B": 350, "N": 300, "P": 100, "x": 0, "K": 200}
        victim_score = mvv_lva_scores[self.state.board[self.end_row][self.end_col][1]]
        attacker_score = mvv_lva_scores[self.state.board[self.start_row][self.start_col][1]] // 100
        return victim_score + 6 - attacker_score

    def get_chess_notation(self):
        """Maps the current move to a
           portable game notation (PGN)
        """
        move_string = ""
        king_moved = False

        if self.castle_move:
            if self.end_col != 6:
                move_string = "0-0-0"
            else:
                move_string = "0-0"
            king_moved = True

        enemy = "b" if self.state.white_moves else "w"
        piece_moved = self.state.board[self.end_row][self.end_col][1]
        piece_notation_amb = str(self.state.board[self.end_row][self.end_col][1] + enemy)
        count_col = 0
        knight_special_case = None
        rook_special_case = None
        ambiguous = False

        if self.state.last_ambiguous_moves.count([self.end_row, self.end_col, piece_notation_amb]) >= 2:
            ambiguous = True
            if piece_moved == "N" or piece_moved == "R":
                for row in range(0, 7):
                    if self.state.board[row][self.start_col][1] == piece_moved and\
                            self.state.board[row][self.start_col][0] == enemy:
                        count_col += 1
            if count_col == 1 and piece_moved == "N":
                knight_special_case = k.rows_to_ranks[self.start_row]
            if count_col == 2 and piece_moved == "R":
                rook_special_case = k.rows_to_ranks[self.start_row]

        self.state.undo_flag = False

        if self.en_passant_move:
            move_string += k.get_file_rank_notation(self.start_row, self.start_col)[0] + "x" +\
                   k.get_file_rank_notation(self.end_row, self.end_col) + " e.p."
            return move_string

        if self.place_to_go != k.empty:
            if self.piece_to_move[1] == "P":
                move_string += k.get_file_rank_notation(self.start_row, self.start_col)[0] + "x" + \
                       k.get_file_rank_notation(self.end_row, self.end_col)
            else:
                if ambiguous:
                    if knight_special_case is None and rook_special_case is None:
                        move_string += self.piece_to_move[1] + \
                                       k.get_file_rank_notation(self.start_row, self.start_col)[0] + \
                                       "x" + k.get_file_rank_notation(self.end_row, self.end_col)
                    else:
                        case = knight_special_case if knight_special_case is not None else rook_special_case
                        move_string += self.piece_to_move[1] + case + "x" + k.get_file_rank_notation(self.end_row,
                                                                                                     self.end_col)
                elif not king_moved:
                    move_string += self.piece_to_move[1] + "x" + k.get_file_rank_notation(self.end_row, self.end_col)
        else:
            if self.piece_to_move[1] == "P":
                move_string += k.get_file_rank_notation(self.end_row, self.end_col)
            else:
                if ambiguous:
                    if knight_special_case is None and rook_special_case is None:
                        move_string += self.piece_to_move[1] + \
                                       k.get_file_rank_notation(self.start_row, self.start_col)[0] +\
                                       k.get_file_rank_notation(self.end_row, self.end_col)
                    else:
                        case = knight_special_case if knight_special_case is not None else rook_special_case
                        move_string += self.piece_to_move[1] + case + k.get_file_rank_notation(self.end_row,
                                                                                               self.end_col)
                elif not king_moved:
                    move_string += self.piece_to_move[1] + k.get_file_rank_notation(self.end_row, self.end_col)

        if self.is_pawn_promotion:
            move_string += "=Q"

        return move_string

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.id == other.id
        return False


class CastleFlags:
    """Castling rights information
       wks = white king side
       bks = black king side
       wqs = white queen side
       bqs = black queen side
    """
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

    def __str__(self):
        return f'({self.wks}, {self.bks}, {self.wqs}, {self.bqs})'

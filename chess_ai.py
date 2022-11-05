import time
import random
import chess_mcts
import chess_constants as k


class ChessAI:
    """Contains the implementantion of
       Minimax search algorithms
       and the evaluation function.
    """
    def __init__(self, depth):
        self.DEPTH = depth
        self.depth_score = 0
        self.candidate_moves = []
        self.next_move = None
        self.global_score = 0
        self.counter = 0
        self.timeout = False
        self.start = 0
        self.global_best_move = None
        self.bishop_pair = [None, None]
        self.doubled_pawns = [None, None]
        self.agent_data = []
        self.algorithm_functions = {'negamax_pruning': self.find_best_move_nega_max_alpha_beta,
                                    'minimax': self.find_best_move_minimax,
                                    'negamax_pruning_id_t_2': self.find_best_move_nega_max_alpha_beta_id,
                                    'negamax_pruning_id_t_5': self.find_best_move_nega_max_alpha_beta_id,
                                    'negamax_pruning_id_t_10': self.find_best_move_nega_max_alpha_beta_id,
                                    'mcts': chess_mcts.find_best_move_mcts}

    def append_to_log(self):
        """Adds move-search computations
           to a list that will be found
           in a csv file
        """
        append_data = [self.next_move.get_chess_notation(),
                       self.counter,
                       str("{:.3f}".format(self.depth_score)),
                       round((time.time() - self.start), 2)]
        print(append_data)
        self.agent_data.append(append_data)

    def find_best_move_nega_max_alpha_beta(self, state, valid_moves):
        """Returns the best move after
           negamax algorithm call

           Keyword arguments:
           state       -- information about chess game
           valid_moves -- list containing possible moves
        """
        self.next_move = None
        random.shuffle(valid_moves)
        self.candidate_moves = []
        self.counter = 0
        self.start = time.time()
        self.find_move_nega_max_alpha_beta(state, valid_moves, self.DEPTH, -k.CHECKMATE,
                                           k.CHECKMATE, 1 if state.white_moves else -1)
        if self.next_move is not None:
            self.append_to_log()
        return self.next_move

    def find_best_move_minimax(self, state, valid_moves):
        """Returns the best move after
           minimax algorithm call

           Keyword arguments:
           state       -- information about chess game
           valid_moves -- list containing possible moves
        """
        self.next_move = None
        random.shuffle(valid_moves)
        self.candidate_moves = []
        self.counter = 0
        self.start = time.time()
        self.find_move_minimax(state, valid_moves, self.DEPTH, True if state.white_moves else False)
        if self.next_move is not None:
            self.append_to_log()
        return self.next_move

    def find_best_move_nega_max_alpha_beta_id(self, state, valid_moves):
        """Returns the best move after
           negamax iterative deepening
           algorithm call (with timeout)
           If time runs out, the last
           calculated best move will
           be returned (2s, 5s or 10s)

           Keyword arguments:
           state       -- information about chess game
           valid_moves -- list containing possible moves
        """
        self.next_move = None
        random.shuffle(valid_moves)
        self.candidate_moves = []
        self.counter = 0
        self.DEPTH = 2
        self.timeout = False
        self.start = time.time()
        for depth in range(0, k.MAX_DEPTH):
            self.global_best_move = self.next_move
            self.global_score = self.depth_score
            self.DEPTH = 2 + depth
            self.find_move_nega_max_alpha_beta_id(state, valid_moves, self.DEPTH, -k.CHECKMATE,
                                                  k.CHECKMATE, 1 if state.white_moves else -1)
            if self.timeout:
                if self.global_best_move is not None:
                    self.append_to_log()
                return self.global_best_move

    def find_move_nega_max_alpha_beta(self, state, valid_moves, depth, alpha, beta, turn_polarity):
        """Implementation of negamax
           alpha beta pruning algorithm

           Keyword arguments:
           state         -- information about chess game
           valid_moves   -- list containing possible moves
           depth         -- the number of future states analyzed
           alpha         -- (-inf initial value)
           beta          -- (+inf initial value)
           turn_polarity -- +1 for white player else -1
        """
        self.counter += 1
        if depth == 0:
            return turn_polarity * self.score_material(state)

        max_score = -k.CHECKMATE
        for move in valid_moves:
            draw_made = False
            state.make_move(move)
            if state.draw_rule or state.stalemate:
                draw_made = True
            next_moves = state.get_valid_moves()
            score = -self.find_move_nega_max_alpha_beta(state, next_moves, depth-1, -beta, -alpha, -turn_polarity)
            if score > max_score and not draw_made:
                max_score = score
                if depth == self.DEPTH:
                    self.next_move = move
                    self.depth_score = max_score * turn_polarity
                    self.candidate_moves.append([move.get_chess_notation(),
                                                 str("{:.3f}".format(score * turn_polarity))])
            state.undo_move()
            if max_score > alpha:
                alpha = max_score
            if alpha >= beta:
                break
        return alpha

    def find_move_nega_max_alpha_beta_id(self, state, valid_moves, depth, alpha, beta, turn_polarity):
        """Implementation of negamax
           alpha beta pruning algorithm
           with iterative deepening

           Keyword arguments:
           state         -- information about chess game
           valid_moves   -- list containing possible moves
           depth         -- the number of future states analyzed
           alpha         -- (-inf initial value)
           beta          -- (+inf initial value)
           turn_polarity -- +1 for white player else -1
        """
        if round((time.time() - self.start), 2) > k.timeout:
            self.timeout = True
            self.depth_score = alpha * turn_polarity
            return alpha

        self.counter += 1
        if depth == 0:
            return turn_polarity * self.score_material(state)

        max_score = -k.CHECKMATE
        for move in valid_moves:
            draw_made = False
            state.make_move(move)
            if state.draw_rule or state.stalemate:
                draw_made = True
            next_moves = state.get_valid_moves()
            score = -self.find_move_nega_max_alpha_beta_id(state, next_moves, depth-1, -beta, -alpha, -turn_polarity)
            if score > max_score and not draw_made:
                max_score = score
                if depth == self.DEPTH:
                    self.next_move = move
                    self.depth_score = max_score * turn_polarity
                    self.candidate_moves.append([move.get_chess_notation(),
                                                 str("{:.3f}".format(score * turn_polarity))])
            state.undo_move()
            if max_score > alpha:
                alpha = max_score
            if alpha >= beta:
                break
        return alpha

    def find_move_minimax(self, state, valid_moves, depth, maximize):
        """Implementation of minimax
           algorithm

           Keyword arguments:
           state       -- information about chess game
           valid_moves -- list containing possible moves
           depth       -- the number of future states analyzed
           maximize    -- True for white player else False
        """
        self.counter += 1
        if depth == 0:
            return self.score_material(state)

        if maximize:
            max_score = -k.CHECKMATE
            for move in valid_moves:
                draw_made = False
                state.make_move(move)
                if state.draw_rule or state.stalemate:
                    draw_made = True
                next_moves = state.get_valid_moves()
                score = self.find_move_minimax(state, next_moves, depth-1, not maximize)
                if score > max_score and not draw_made:
                    max_score = score
                    if depth == self.DEPTH:
                        self.next_move = move
                        self.depth_score = max_score
                        self.candidate_moves.append([move.get_chess_notation(),
                                                    str("{:.3f}".format(score))])
                state.undo_move()
            return max_score
        else:
            min_score = k.CHECKMATE
            for move in valid_moves:
                draw_made = False
                state.make_move(move)
                if state.draw_rule or state.stalemate:
                    draw_made = True
                next_moves = state.get_valid_moves()
                score = self.find_move_minimax(state, next_moves, depth-1, not maximize)
                if score < min_score and not draw_made:
                    min_score = score
                    if depth == self.DEPTH:
                        self.next_move = move
                        self.depth_score = min_score
                        self.candidate_moves.append([move.get_chess_notation(),
                                                    str("{:.3f}".format(score))])
                state.undo_move()
            return min_score

    def score_material(self, state):
        """Evaluation function for
           current game state

           Keyword arguments:
           state -- information about chess game
        """
        if state.draw_rule or state.stalemate:
            return k.STALEMATE

        if state.checkmate:
            if state.white_moves:
                return -k.CHECKMATE
            else:
                return k.CHECKMATE

        score = 0
        score += state.position_score

        if state.white_castled:
            score += 1
        elif state.black_castled:
            score -= 1

        if state.repetition_punish[0]:
            score -= 2
        if state.repetition_punish[1]:
            score += 2

        score += state.white_bishop_counter * 0.25
        score -= state.black_bishop_counter * 0.25

        if state.draw_rule and state.white_moves and score < 0:
            self.depth_score = 0
            return k.STALEMATE

        if state.draw_rule and not state.white_moves and score > 0:
            self.depth_score = 0
            return k.STALEMATE

        if score > 5 and not state.pawn_moved_white:
            score -= 2

        if score > -5 and not state.pawn_moved_black:
            score += 2

        return score

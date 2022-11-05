import random
import chess
import math
import chess_constants as k
import time

random.seed(67)

PLAYER = chess.WHITE
OPPONENT = chess.BLACK
file = open(f"{k.mcts_data}", "w")


class TreeNode:
    """Contains Monte Carlo Tree Search steps
       1) selection
       2) expansion
       3) simulation
       4) back-propagation

       This is an experiment written by Dominik Klein
       in the paper 'Neural Networks for Chess
       The magic of deep and reinforcement
       learning revealed'
    """
    def __init__(self, board):
        self.M = 0
        self.V = 0
        self.visited_moves_and_nodes = []
        self.non_visited_legal_moves = []
        self.board = board
        self.parent = None

        for m in self.board.legal_moves:
            self.non_visited_legal_moves.append(m)

    def is_mcts_leaf_node(self):
        return len(self.non_visited_legal_moves) != 0

    def is_terminal_node(self):
        return len(self.non_visited_legal_moves) == 0 and len(self.visited_moves_and_nodes) == 0


def uct_value(node, parent):
    """Returns the Upper Condifcence
       bounds applied to the Tree
       (a guide of the selection process)
    """
    val = (node.M / node.V) + 2 * math.sqrt(math.log(parent.V) / node.V)
    return val


def select(node):
    """Selection step
       If the node is not a leaf node, the maximum UCT value
       child will be recursively selected
    """
    if node.is_mcts_leaf_node() or node.is_terminal_node():
        return node
    else:
        max_uct_child = None
        max_uct_value = -1000000
        for move, child in node.visited_moves_and_nodes:
            uct_val_child = uct_value(child, node)
            if uct_val_child > max_uct_value:
                max_uct_child = child
                max_uct_value = uct_val_child
        if max_uct_child is None:
            raise ValueError("Could not identify child with best uct value")
        else:
            return select(max_uct_child)


def expand(node):
    """Expansion step
       New child node is made from current node
       and returned (currently shares the same board as
       it's parent)
    """
    move_to_expand = node.non_visited_legal_moves.pop()
    board = node.board.copy()
    board.push(move_to_expand)
    child_node = TreeNode(board)
    child_node.parent = node
    node.visited_moves_and_nodes.append((move_to_expand, child_node))
    return child_node


def simulate(node):
    """Plays a random chess game until
       the end, and returns the payout
       1 = win, 0.5 = draw and 0 = lose
    """
    board = node.board.copy()
    while board.outcome(claim_draw=True) is None:
        ls = []
        for m in board.legal_moves:
            ls.append(m)
        move = random.choice(ls)
        board.push(move)
    file.write("---------------\n")
    file.write(str(board))

    payout = 0.5
    o = board.outcome(claim_draw=True)

    file.write("\nWinner: " + str(o.winner))
    file.write("\n")

    if o.winner == PLAYER:
        payout = 1
    if o.winner == OPPONENT:
        payout = 0.
    if o.winner is None:
        payout = 0.5
    return payout


def backpropagate(node, payout):
    """Returns the payout and the visit
       increment back to it's parents
       (up to it's roots)
    """
    node.M = node.M + payout
    node.V = node.V + 1

    if node.parent is not None:
        return backpropagate(node.parent, payout)


def find_best_move_mcts(chessboard, valid_moves):
    """Returns best MCTS move
       after a number of iterations
       the move with the highest score will be selected
    """
    root = TreeNode(chessboard)
    start = time.time()
    for i in range(0, 250):
        node = select(root)
        if not node.is_terminal_node():
            node = expand(node)
        payout = simulate(node)
        backpropagate(node, payout)

    run_time = round((time.time() - start), 2)
    next_move = None
    max_score = 0
    file_app = open(f"{k.mcts_data}", "a")

    for move, child in root.visited_moves_and_nodes:
        file_app.write("\n")
        file_app.write(f"Move: {str(move)} |"
                       f" score = {str(child.M)} | visits = {str(child.V)}\n")
        if child.M > max_score:
            max_score = child.M
            next_move = str(move)

    for move in valid_moves:
        move_aux = k.get_file_rank_notation(move.start_row, move.start_col) +\
                   k.get_file_rank_notation(move.end_row, move.end_col)
        if next_move == move_aux:
            file_app.write(f"Runtime: {run_time} [s]")
            return move
    return

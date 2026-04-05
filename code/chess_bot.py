import random


PIECE_VALUES = {
    "Pawn": 100,
    "Knight": 320,
    "Bishop": 330,
    "Rook": 500,
    "Queen": 900,
    "King": 20000
}

CHECKMATE = 100000
STALEMATE = 0
DEPTH = 3

next_move = None


def get_ai_move(gs, valid_moves):
    global next_move
    next_move = None

    root_moves = valid_moves[:]
    random.shuffle(root_moves)

    is_maximizing = gs.white_to_move
    _minimax(gs, DEPTH, -float('inf'), float('inf'), is_maximizing, root_moves)

    return next_move


def _minimax(gs, depth, alpha, beta, is_maximizing, valid_moves=None):
    if valid_moves is None:
        valid_moves = gs.get_valid_moves()

    if depth == 0 or not valid_moves:
        return _evaluate_terminal_or_position(gs, valid_moves, is_maximizing, depth)

    global next_move

    if is_maximizing:
        max_score = -float('inf')

        for move in valid_moves:
            gs.make_move(move)
            next_moves = gs.get_valid_moves()
            score = _minimax(gs, depth - 1, alpha, beta, False, next_moves)
            gs.undo_move()

            if score > max_score:
                max_score = score
                if depth == DEPTH:
                    next_move = move

            alpha = max(alpha, max_score)
            if beta <= alpha:
                break

        return max_score

    else:
        min_score = float('inf')

        for move in valid_moves:
            gs.make_move(move)
            next_moves = gs.get_valid_moves()
            score = _minimax(gs, depth - 1, alpha, beta, True, next_moves)
            gs.undo_move()

            if score < min_score:
                min_score = score
                if depth == DEPTH:
                    next_move = move

            beta = min(beta, min_score)
            if beta <= alpha:
                break

        return min_score


def _evaluate_terminal_or_position(gs, valid_moves, is_maximizing, depth):
    if not valid_moves:
        color_to_move = 'w' if gs.white_to_move else 'b'

        if gs.is_in_check(color_to_move):
            if is_maximizing:
                return -CHECKMATE - depth
            else:
                return CHECKMATE + depth

        return STALEMATE

    return _evaluate_board(gs)


def _evaluate_board(gs):
    score = 0

    for row in gs.board:
        for piece in row:
            if piece != "..":
                value = PIECE_VALUES[piece.__class__.__name__]
                if piece.color == 'w':
                    score += value
                else:
                    score -= value

    return score

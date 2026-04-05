from pieces import Pawn, Knight, Bishop, Rook, Queen, King


class GameState:
    def __init__(self):
        self.board = self._setup_board()
        self.white_to_move = True

        self.move_log = []
        self.redo_log = []

        # Позиции королей
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)

        # Клетка для взятия на проходе
        # Например, если пешка пошла на 2 клетки, сюда записываем промежуточную клетку
        self.en_passant_target = None

        # Счётчик повторений позиций для троекратного повторения
        self.position_counts = {}
        self._increment_position_count()

    def _setup_board(self):
        board = [[".." for _ in range(8)] for _ in range(8)]
        board[0] = [Rook('b'), Knight('b'), Bishop('b'), Queen('b'), King('b'), Bishop('b'), Knight('b'), Rook('b')]
        board[1] = [Pawn('b') for _ in range(8)]
        board[6] = [Pawn('w') for _ in range(8)]
        board[7] = [Rook('w'), Knight('w'), Bishop('w'), Queen('w'), King('w'), Bishop('w'), Knight('w'), Rook('w')]
        return board

    def _current_color(self):
        return 'w' if self.white_to_move else 'b'

    def _enemy_color(self, color):
        return 'b' if color == 'w' else 'w'

    def _set_king_pos(self, color, pos):
        if color == 'w':
            self.white_king_pos = pos
        else:
            self.black_king_pos = pos

    def _get_king_pos(self, color):
        return self.white_king_pos if color == 'w' else self.black_king_pos

    def _resolve_promotion_class(self, promotion_piece):
        # Можно передать:
        # None -> Ферзь
        # класс, например Queen
        # объект, например Queen('w')
        if promotion_piece is None:
            return Queen

        if isinstance(promotion_piece, type):
            return promotion_piece

        return promotion_piece.__class__

    def _piece_symbol(self, piece):
        if isinstance(piece, Pawn):
            return 'P'
        if isinstance(piece, Knight):
            return 'N'
        if isinstance(piece, Bishop):
            return 'B'
        if isinstance(piece, Rook):
            return 'R'
        if isinstance(piece, Queen):
            return 'Q'
        if isinstance(piece, King):
            return 'K'
        return '..'

    def _get_castling_rights(self):
        rights = []

        # Белые
        if self.white_king_pos == (7, 4):
            white_king = self.board[7][4]
            if isinstance(white_king, King) and white_king.color == 'w' and not white_king.has_moved:
                white_rook_short = self.board[7][7]
                if isinstance(white_rook_short, Rook) and white_rook_short.color == 'w' and not white_rook_short.has_moved:
                    rights.append("K")

                white_rook_long = self.board[7][0]
                if isinstance(white_rook_long, Rook) and white_rook_long.color == 'w' and not white_rook_long.has_moved:
                    rights.append("Q")

        # Черные
        if self.black_king_pos == (0, 4):
            black_king = self.board[0][4]
            if isinstance(black_king, King) and black_king.color == 'b' and not black_king.has_moved:
                black_rook_short = self.board[0][7]
                if isinstance(black_rook_short, Rook) and black_rook_short.color == 'b' and not black_rook_short.has_moved:
                    rights.append("k")

                black_rook_long = self.board[0][0]
                if isinstance(black_rook_long, Rook) and black_rook_long.color == 'b' and not black_rook_long.has_moved:
                    rights.append("q")

        return "".join(rights) if rights else "-"

    def _effective_en_passant_target(self):
        # Для троекратного повторения учитываем en passant
        # только если текущий игрок действительно может взять на проходе
        if self.en_passant_target is None:
            return None

        target_r, target_c = self.en_passant_target
        color = self._current_color()
        direction = -1 if color == 'w' else 1
        pawn_row = target_r - direction

        for dc in (-1, 1):
            c = target_c + dc
            if 0 <= pawn_row < 8 and 0 <= c < 8:
                piece = self.board[pawn_row][c]
                if piece != ".." and piece.color == color and isinstance(piece, Pawn):
                    return self.en_passant_target

        return None

    def _get_position_key(self):
        board_state = []

        for r in range(8):
            row_state = []
            for c in range(8):
                piece = self.board[r][c]
                if piece == "..":
                    row_state.append("..")
                else:
                    row_state.append(piece.color + self._piece_symbol(piece))
            board_state.append(tuple(row_state))

        side_to_move = 'w' if self.white_to_move else 'b'
        castling_rights = self._get_castling_rights()
        en_passant = self._effective_en_passant_target()

        return (tuple(board_state), side_to_move, castling_rights, en_passant)

    def _increment_position_count(self):
        key = self._get_position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def _decrement_position_count(self):
        key = self._get_position_key()
        if key in self.position_counts:
            self.position_counts[key] -= 1
            if self.position_counts[key] <= 0:
                del self.position_counts[key]

    def is_threefold_repetition(self):
        key = self._get_position_key()
        return self.position_counts.get(key, 0) >= 3

    def is_square_attacked(self, row, col, by_color):
        # Проверка атак пешек
        # Если клетка бьется белой пешкой, значит белая пешка стоит на row+1
        pawn_row = row + 1 if by_color == 'w' else row - 1
        for dc in (-1, 1):
            pawn_col = col + dc
            if 0 <= pawn_row < 8 and 0 <= pawn_col < 8:
                piece = self.board[pawn_row][pawn_col]
                if piece != ".." and piece.color == by_color and isinstance(piece, Pawn):
                    return True

        # Проверка атак коней
        knight_jumps = [
            (-2, -1), (-2, 1), (2, -1), (2, 1),
            (-1, -2), (1, -2), (-1, 2), (1, 2)
        ]
        for dr, dc in knight_jumps:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != ".." and piece.color == by_color and isinstance(piece, Knight):
                    return True

        # Проверка атак короля
        king_dirs = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        for dr, dc in king_dirs:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != ".." and piece.color == by_color and isinstance(piece, King):
                    return True

        # Проверка атак по диагоналям
        diagonal_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in diagonal_dirs:
            for i in range(1, 8):
                r, c = row + dr * i, col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break

                piece = self.board[r][c]
                if piece == "..":
                    continue

                if piece.color == by_color and isinstance(piece, (Bishop, Queen)):
                    return True
                break

        # Проверка атак по прямым
        straight_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in straight_dirs:
            for i in range(1, 8):
                r, c = row + dr * i, col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break

                piece = self.board[r][c]
                if piece == "..":
                    continue

                if piece.color == by_color and isinstance(piece, (Rook, Queen)):
                    return True
                break

        return False

    def is_in_check(self, color):
        king_r, king_c = self._get_king_pos(color)
        return self.is_square_attacked(king_r, king_c, self._enemy_color(color))

    def _get_king_normal_moves(self, row, col, color):
        moves = []
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target = self.board[r][c]
                if target == ".." or target.color != color:
                    moves.append(((row, col), (r, c)))

        return moves

    def _get_en_passant_moves(self, row, col, color):
        moves = []

        if self.en_passant_target is None:
            return moves

        target_r, target_c = self.en_passant_target
        direction = -1 if color == 'w' else 1

        # Пешка может взять на проходе, если целевая клетка находится
        # по диагонали вперед на 1 клетку
        # взятие на проходе можно совершить только ответным ходом СРАЗУ после хода противника
        # Это надо обеспечить в _apply_move()
        if target_r == row + direction and abs(target_c - col) == 1:
            moves.append(((row, col), (target_r, target_c)))
        return moves

    def _get_castle_moves(self, row, col, color):
        moves = []
        piece = self.board[row][col]

        if not isinstance(piece, King) or piece.color != color:
            return moves

        # Если король уже ходил - рокировка невозможна
        if piece.has_moved:
            return moves

        # Нельзя рокироваться, если король под шахом
        if self.is_in_check(color):
            return moves

        # Короткая рокировка
        if self._can_castle_short(row, col, color):
            moves.append(((row, col), (row, col + 2)))

        # Длинная рокировка
        if self._can_castle_long(row, col, color):
            moves.append(((row, col), (row, col - 2)))

        return moves

    def _can_castle_short(self, row, col, color):
        rook = self.board[row][7]

        if not (isinstance(rook, Rook) and rook.color == color and not rook.has_moved):
            return False

        if self.board[row][5] != ".." or self.board[row][6] != "..":
            return False

        # Клетки, через которые проходит король, не должны быть под боем
        if self.is_square_attacked(row, 5, self._enemy_color(color)):
            return False
        if self.is_square_attacked(row, 6, self._enemy_color(color)):
            return False

        return True

    def _can_castle_long(self, row, col, color):
        rook = self.board[row][0]

        if not (isinstance(rook, Rook) and rook.color == color and not rook.has_moved):
            return False

        if self.board[row][1] != ".." or self.board[row][2] != ".." or self.board[row][3] != "..":
            return False

        # Клетки, через которые проходит король, не должны быть под боем
        if self.is_square_attacked(row, 3, self._enemy_color(color)):
            return False
        if self.is_square_attacked(row, 2, self._enemy_color(color)):
            return False

        return True

    def _get_all_pseudo_moves(self, color):
        moves = []

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]

                if piece == ".." or piece.color != color:
                    continue

                # Для короля обычные ходы и рокировку обрабатываем отдельно,
                # чтобы не зависеть от логики King.get_possible_moves()
                if isinstance(piece, King):
                    moves.extend(self._get_king_normal_moves(r, c, color))
                    moves.extend(self._get_castle_moves(r, c, color))
                    continue

                # Для пешки добавляем обычные ходы + взятие на проходе
                if isinstance(piece, Pawn):
                    for move_r, move_c in piece.get_possible_moves(r, c, self.board):
                        moves.append(((r, c), (move_r, move_c)))
                    moves.extend(self._get_en_passant_moves(r, c, color))
                    continue

                # Остальные фигуры
                for move_r, move_c in piece.get_possible_moves(r, c, self.board):
                    moves.append(((r, c), (move_r, move_c)))

        return moves

    def get_valid_moves(self):
        color = self._current_color()
        valid_moves = []

        for move in self._get_all_pseudo_moves(color):
            move_info = self._apply_move(move, promotion_piece=None, record_in_history=False, clear_redo=False)

            # После своего хода нельзя оставлять своего короля под шахом
            if not self.is_in_check(color):
                valid_moves.append(move)

            self._undo_applied_move(move_info)

        return valid_moves

    def _apply_move(self, move, promotion_piece=None, record_in_history=True, clear_redo=True):
        start, end = move
        sr, sc = start
        er, ec = end

        piece_moved = self.board[sr][sc]
        piece_captured = self.board[er][ec]

        if piece_moved == "..":
            return None

        promotion_class = self._resolve_promotion_class(promotion_piece)

        move_info = {
            "move": move,
            "piece_moved": piece_moved,
            "piece_captured": piece_captured,
            "piece_moved_has_moved_before": piece_moved.has_moved,
            "white_to_move_before": self.white_to_move,
            "white_king_pos_before": self.white_king_pos,
            "black_king_pos_before": self.black_king_pos,
            "en_passant_target_before": self.en_passant_target,
            "rook_move": None,
            "promotion": None,
            "promotion_class": promotion_class,
            "en_passant_capture": None,
        }

        # Проверка на взятие на проходе:
        # пешка идет по диагонали, но на конечной клетке пусто
        is_en_passant = (
            isinstance(piece_moved, Pawn)
            and sc != ec
            and piece_captured == ".."
        )

        if is_en_passant:
            captured_row = er + 1 if piece_moved.color == 'w' else er - 1
            captured_piece = self.board[captured_row][ec]

            move_info["piece_captured"] = captured_piece
            move_info["en_passant_capture"] = {
                "piece": captured_piece,
                "pos": (captured_row, ec),
            }

            self.board[captured_row][ec] = ".."

        # Перемещаем фигуру
        self.board[er][ec] = piece_moved
        self.board[sr][sc] = ".."

        # Если ходил король - обновляем его позицию
        if isinstance(piece_moved, King):
            self._set_king_pos(piece_moved.color, (er, ec))

            # Если король пошел на 2 клетки - это рокировка
            if abs(ec - sc) == 2:
                if ec > sc:
                    rook_start_col = 7
                    rook_end_col = 5
                else:
                    rook_start_col = 0
                    rook_end_col = 3

                rook = self.board[sr][rook_start_col]

                move_info["rook_move"] = {
                    "piece": rook,
                    "start": (sr, rook_start_col),
                    "end": (sr, rook_end_col),
                    "has_moved_before": rook.has_moved,
                }

                self.board[sr][rook_end_col] = rook
                self.board[sr][rook_start_col] = ".."
                rook.has_moved = True

        # По умолчанию en passant сбрасывается
        self.en_passant_target = None

        # Если пешка пошла на 2 клетки - записываем промежуточную клетку
        if isinstance(piece_moved, Pawn) and abs(er - sr) == 2:
            middle_row = (sr + er) // 2
            self.en_passant_target = (middle_row, sc)

        # Превращение пешки
        if isinstance(piece_moved, Pawn):
            if (piece_moved.color == 'w' and er == 0) or (piece_moved.color == 'b' and er == 7):
                promoted_piece = promotion_class(piece_moved.color)
                promoted_piece.has_moved = True
                self.board[er][ec] = promoted_piece

                move_info["promotion"] = {
                    "pawn": piece_moved,
                    "promoted_piece": promoted_piece,
                }

        # Фигура теперь считается походившей
        piece_moved.has_moved = True

        # Передаем ход
        self.white_to_move = not self.white_to_move

        # Записываем в историю
        if record_in_history:
            if clear_redo:
                self.redo_log.clear()
            self.move_log.append(move_info)
            self._increment_position_count()

        return move_info

    def _undo_applied_move(self, move_info):
        if move_info is None:
            return

        start, end = move_info["move"]
        sr, sc = start
        er, ec = end

        piece_moved = move_info["piece_moved"]
        piece_captured = move_info["piece_captured"]

        # Возвращаем чей был ход
        self.white_to_move = move_info["white_to_move_before"]

        # Если было превращение - на старт возвращаем исходную пешку
        if move_info["promotion"] is not None:
            self.board[sr][sc] = move_info["promotion"]["pawn"]
        else:
            self.board[sr][sc] = piece_moved

        # Если это было взятие на проходе, конечная клетка должна стать пустой,
        # а побитая пешка возвращается отдельно
        if move_info["en_passant_capture"] is not None:
            self.board[er][ec] = ".."
            cap = move_info["en_passant_capture"]
            cap_r, cap_c = cap["pos"]
            self.board[cap_r][cap_c] = cap["piece"]
        else:
            self.board[er][ec] = piece_captured

        # Если была рокировка - возвращаем ладью
        rook_move = move_info["rook_move"]
        if rook_move is not None:
            rook = rook_move["piece"]
            rsr, rsc = rook_move["start"]
            rer, rec = rook_move["end"]

            self.board[rsr][rsc] = rook
            self.board[rer][rec] = ".."
            rook.has_moved = rook_move["has_moved_before"]

        # Возвращаем флаг первого хода фигуре
        piece_moved.has_moved = move_info["piece_moved_has_moved_before"]

        # Возвращаем позиции королей
        self.white_king_pos = move_info["white_king_pos_before"]
        self.black_king_pos = move_info["black_king_pos_before"]

        # Возвращаем en passant
        self.en_passant_target = move_info["en_passant_target_before"]

    def make_move(self, move, promotion_piece=None):
        self._apply_move(move, promotion_piece=promotion_piece, record_in_history=True, clear_redo=True)

    def undo_move(self):
        if len(self.move_log) == 0:
            return

        # Уменьшаем счетчик текущей позиции
        self._decrement_position_count()

        move_info = self.move_log.pop()
        self._undo_applied_move(move_info)

        self.redo_log.append(move_info)

    def redo_move(self):
        if len(self.redo_log) == 0:
            return

        move_info = self.redo_log.pop()

        # При redo не очищаем redo_log целиком,
        # чтобы можно было делать несколько redo подряд
        self._apply_move(
            move_info["move"],
            promotion_piece=move_info["promotion_class"],
            record_in_history=True,
            clear_redo=False
        )

    def check_game_over(self):
        valid_moves = self.get_valid_moves()

        if len(valid_moves) == 0:
            color = self._current_color()

            if self.is_in_check(color):
                return "Мат! Победили " + ("черные" if color == 'w' else "белые")
            else:
                return "Пат! Ничья."

        if self.is_threefold_repetition():
            return "Ничья по троекратному повторению позиции"

        return "Игра продолжается"

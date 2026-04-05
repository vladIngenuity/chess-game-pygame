from abc import ABC, abstractmethod


class Piece(ABC):
    def __init__(self, color):
        self.color = color  # 'w' или 'b'
        self.has_moved = False

    @abstractmethod
    def get_possible_moves(self, row, col, board):
        # Виртуальный метод
        pass

    def get_sliding_moves(self, row, col, board, directions):
        # Только для ферзя, слона и ладьи !не конь
        moves = []

        for dr, dc in directions:
            for i in range(1, 8):
                r = row + dr * i
                c = col + dc * i

                if not (0 <= r < 8 and 0 <= c < 8):
                    break

                target = board[r][c]

                if target == "..":
                    moves.append((r, c))
                elif target.color != self.color:
                    moves.append((r, c))
                    break
                else:
                    break

        return moves


class Pawn(Piece):
    def get_possible_moves(self, row, col, board):
        moves = []
        direction = -1 if self.color == 'w' else 1

        # Пешка идет вперед
        one_step_row = row + direction
        if 0 <= one_step_row < 8 and board[one_step_row][col] == "..":
            moves.append((one_step_row, col))

            # 2 хода вперед
            two_step_row = row + 2 * direction
            if (
                not self.has_moved
                and 0 <= two_step_row < 8
                and board[two_step_row][col] == ".."
            ):
                moves.append((two_step_row, col))

        # Взятие на диагонали
        for dc in (-1, 1):
            r = row + direction
            c = col + dc

            if 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target != ".." and target.color != self.color:
                    moves.append((r, c))

        return moves

      
class Knight(Piece):
    def get_possible_moves(self, row, col, board):
        moves = []
        jumps = [
            (-2, -1), (-2, 1),
            (2, -1), (2, 1),
            (-1, -2), (1, -2),
            (-1, 2), (1, 2)
        ]  # направления прыжка коня

        for dr, dc in jumps:
            r = row + dr
            c = col + dc

            if 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target == ".." or target.color != self.color:
                    moves.append((r, c))

        return moves


class Bishop(Piece):
    def get_possible_moves(self, row, col, board):
        return self.get_sliding_moves(
            row, col, board,
            [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        )


class Rook(Piece):
    def get_possible_moves(self, row, col, board):
        return self.get_sliding_moves(
            row, col, board,
            [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )


class Queen(Piece):
    def get_possible_moves(self, row, col, board):
        return self.get_sliding_moves(
            row, col, board,
            [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ]
        )


class King(Piece):
    def get_possible_moves(self, row, col, board):
        moves = []
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        for dr, dc in directions:
            r = row + dr
            c = col + dc

            if 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target == ".." or target.color != self.color:
                    moves.append((r, c))

        # Рокировку здесь не добавляем
        return moves

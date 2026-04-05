import time
import pygame
from gamestate import GameState
from chess_bot import get_ai_move
from pieces import Pawn, Knight, Queen, Rook, Bishop


BOARD_SIZE = 720
STATUS_BAR_HEIGHT = 32

WIDTH = BOARD_SIZE
HEIGHT = BOARD_SIZE + STATUS_BAR_HEIGHT

DIMENSION = 8
SQ_SIZE = BOARD_SIZE // DIMENSION
FPS = 30

ONGOING_STATUS = "Игра продолжается"

IMAGES = {}

LIGHT_COLOR = pygame.Color(240, 217, 181)
DARK_COLOR = pygame.Color(181, 136, 99)

SELECT_COLOR = pygame.Color(246, 246, 105)
MOVE_COLOR = pygame.Color(106, 168, 79)
CAPTURE_COLOR = pygame.Color(204, 0, 0)

TEXT_BG_COLOR = pygame.Color(30, 30, 30)
TEXT_COLOR = pygame.Color("white")

MENU_BG = pygame.Color(40, 40, 40)
BUTTON_COLOR = pygame.Color(70, 70, 70)
BUTTON_HOVER = pygame.Color(100, 100, 100)
BUTTON_TEXT = pygame.Color("white")


def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK',
              'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']

    for piece in pieces:
        IMAGES[piece] = pygame.transform.scale(
            pygame.image.load(f"images/{piece}.png"),
            (SQ_SIZE, SQ_SIZE)
        )


def get_piece_image_key(piece):
    if isinstance(piece, Pawn):
        return piece.color + "P"
    if isinstance(piece, Knight):
        return piece.color + "N"
    return piece.color + piece.__class__.__name__[0]


def draw_board(screen):
    colors = [LIGHT_COLOR, DARK_COLOR]

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )


def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "..":
                key = get_piece_image_key(piece)
                screen.blit(
                    IMAGES[key],
                    pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                )


def is_en_passant_move(gs, move):
    (sr, sc), (er, ec) = move
    piece = gs.board[sr][sc]

    if piece == ".." or not isinstance(piece, Pawn):
        return False

    if sc == ec:
        return False

    if gs.board[er][ec] != "..":
        return False

    return gs.en_passant_target == (er, ec)


def highlight_squares(screen, gs, valid_moves, selected_sq):
    if selected_sq == ():
        return

    r, c = selected_sq
    piece = gs.board[r][c]

    if piece == "..":
        return

    current_color = 'w' if gs.white_to_move else 'b'
    if piece.color != current_color:
        return

    select_surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
    select_surface.fill((SELECT_COLOR.r, SELECT_COLOR.g, SELECT_COLOR.b, 120))
    screen.blit(select_surface, (c * SQ_SIZE, r * SQ_SIZE))

    for move in valid_moves:
        start, end = move
        if start != selected_sq:
            continue

        end_r, end_c = end
        target_piece = gs.board[end_r][end_c]
        is_capture = target_piece != ".." or is_en_passant_move(gs, move)

        mark_surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)

        if is_capture:
            mark_surface.fill((CAPTURE_COLOR.r, CAPTURE_COLOR.g, CAPTURE_COLOR.b, 110))
        else:
            mark_surface.fill((MOVE_COLOR.r, MOVE_COLOR.g, MOVE_COLOR.b, 90))

        screen.blit(mark_surface, (end_c * SQ_SIZE, end_r * SQ_SIZE))

        center_x = end_c * SQ_SIZE + SQ_SIZE // 2
        center_y = end_r * SQ_SIZE + SQ_SIZE // 2

        if is_capture:
            pygame.draw.circle(screen, pygame.Color(255, 255, 255), (center_x, center_y), 10, 3)
        else:
            pygame.draw.circle(screen, pygame.Color(30, 30, 30), (center_x, center_y), 10)


def get_turn_text(gs, vs_bot, bot_thinking, bot_last_think_time):
    game_status = gs.check_game_over()
    if game_status != ONGOING_STATUS:
        return game_status

    if vs_bot:
        if bot_thinking:
            return "Ход чёрных (бот думает...)"

        if gs.white_to_move:
            if bot_last_think_time > 0:
                return f"Ход белых (ты) | бот думал: {bot_last_think_time:.2f} c"
            return "Ход белых (ты)"

        return "Ход чёрных (бот)"

    return "Ход белых" if gs.white_to_move else "Ход чёрных"


def draw_status_bar(screen, text):
    font = pygame.font.SysFont("arial", 20, bold=True)

    bar_rect = pygame.Rect(0, BOARD_SIZE, WIDTH, STATUS_BAR_HEIGHT)
    pygame.draw.rect(screen, TEXT_BG_COLOR, bar_rect)

    rendered = font.render(text, True, TEXT_COLOR)
    text_y = BOARD_SIZE + (STATUS_BAR_HEIGHT - rendered.get_height()) // 2
    screen.blit(rendered, (10, text_y))


def draw_game_state(screen, gs, valid_moves, selected_sq, status_text):
    draw_board(screen)
    highlight_squares(screen, gs, valid_moves, selected_sq)
    draw_pieces(screen, gs.board)
    draw_status_bar(screen, status_text)


def refresh_game_state(gs):
    valid_moves = gs.get_valid_moves()
    game_status = gs.check_game_over()
    return valid_moves, game_status


def handle_human_click(gs, valid_moves, selected_sq, player_clicks, mouse_pos):
    x, y = mouse_pos

    if y >= BOARD_SIZE:
        return selected_sq, player_clicks, False

    col = x // SQ_SIZE
    row = y // SQ_SIZE
    clicked_sq = (row, col)

    piece = gs.board[row][col]
    current_color = 'w' if gs.white_to_move else 'b'

    if selected_sq == clicked_sq:
        return (), [], False

    if selected_sq == ():
        if piece != ".." and piece.color == current_color:
            return clicked_sq, [clicked_sq], False
        return (), [], False

    if piece != ".." and piece.color == current_color:
        return clicked_sq, [clicked_sq], False

    move = (selected_sq, clicked_sq)

    if move in valid_moves:
        gs.make_move(move, promotion_piece=Queen)#пока так
        return (), [], True

    return selected_sq, player_clicks, False


def reset_game_state():
    gs = GameState()
    valid_moves, game_status = refresh_game_state(gs)
    selected_sq = ()
    player_clicks = []
    bot_last_think_time = 0.0
    bot_thinking = False
    return gs, valid_moves, game_status, selected_sq, player_clicks, bot_last_think_time, bot_thinking


def draw_menu(screen, mouse_pos):
    screen.fill(MENU_BG)

    title_font = pygame.font.SysFont("arial", 36, bold=True)
    button_font = pygame.font.SysFont("arial", 24, bold=True)

    title = title_font.render("Шахматы", True, TEXT_COLOR)
    title_rect = title.get_rect(center=(WIDTH // 2, 90))
    screen.blit(title, title_rect)

    button_width = 260
    button_height = 60

    human_button = pygame.Rect(WIDTH // 2 - button_width // 2, 170, button_width, button_height)
    bot_button = pygame.Rect(WIDTH // 2 - button_width // 2, 250, button_width, button_height)
    exit_button = pygame.Rect(WIDTH // 2 - button_width // 2, 330, button_width, button_height)

    for rect, text in [
        (human_button, "Человек vs человек"),
        (bot_button, "Человек vs бот"),
        (exit_button, "Выход")
    ]:
        color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(180, 180, 180), rect, 2, border_radius=10)

        label = button_font.render(text, True, BUTTON_TEXT)
        label_rect = label.get_rect(center=rect.center)
        screen.blit(label, label_rect)

    pygame.display.flip()
    return human_button, bot_button, exit_button


def show_main_menu(screen, clock):
    while True:
        mouse_pos = pygame.mouse.get_pos()
        human_button, bot_button, exit_button = draw_menu(screen, mouse_pos)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

            if e.type == pygame.MOUSEBUTTONDOWN:
                if human_button.collidepoint(e.pos):
                    return "human"
                if bot_button.collidepoint(e.pos):
                    return "bot"
                if exit_button.collidepoint(e.pos):
                    return "quit"

        clock.tick(FPS)


def run_human_vs_human(screen, clock):
    gs, valid_moves, game_status, selected_sq, player_clicks, bot_last_think_time, bot_thinking = reset_game_state()

    while True:
        status_text = get_turn_text(gs, False, False, 0.0)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"

                if e.key == pygame.K_r:
                    gs, valid_moves, game_status, selected_sq, player_clicks, bot_last_think_time, bot_thinking = reset_game_state()

                elif e.key == pygame.K_z:
                    gs.undo_move()
                    valid_moves, game_status = refresh_game_state(gs)
                    selected_sq = ()
                    player_clicks = []

                elif e.key == pygame.K_x:
                    gs.redo_move()
                    valid_moves, game_status = refresh_game_state(gs)
                    selected_sq = ()
                    player_clicks = []

            elif e.type == pygame.MOUSEBUTTONDOWN and game_status == ONGOING_STATUS:
                selected_sq, player_clicks, move_made = handle_human_click(
                    gs,
                    valid_moves,
                    selected_sq,
                    player_clicks,
                    e.pos
                )

                if move_made:
                    valid_moves, game_status = refresh_game_state(gs)

        status_text = get_turn_text(gs, False, False, 0.0)
        draw_game_state(screen, gs, valid_moves, selected_sq, status_text)
        clock.tick(FPS)
        pygame.display.flip()


def run_human_vs_bot(screen, clock):
    gs, valid_moves, game_status, selected_sq, player_clicks, bot_last_think_time, bot_thinking = reset_game_state()

    while True:
        human_turn = gs.white_to_move
        status_text = get_turn_text(gs, True, bot_thinking, bot_last_think_time)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"

                if e.key == pygame.K_r:
                    gs, valid_moves, game_status, selected_sq, player_clicks, bot_last_think_time, bot_thinking = reset_game_state()

                elif e.key == pygame.K_z:
                    if len(gs.move_log) > 0:
                        gs.undo_move()
                    if len(gs.move_log) > 0:
                        gs.undo_move()

                    valid_moves, game_status = refresh_game_state(gs)
                    selected_sq = ()
                    player_clicks = []
                    bot_last_think_time = 0.0
                    bot_thinking = False

                elif e.key == pygame.K_x:
                    if len(gs.redo_log) > 0:
                        gs.redo_move()
                    if len(gs.redo_log) > 0:
                        gs.redo_move()

                    valid_moves, game_status = refresh_game_state(gs)
                    selected_sq = ()
                    player_clicks = []
                    bot_last_think_time = 0.0
                    bot_thinking = False

            elif e.type == pygame.MOUSEBUTTONDOWN and human_turn and game_status == ONGOING_STATUS:
                selected_sq, player_clicks, move_made = handle_human_click(
                    gs,
                    valid_moves,
                    selected_sq,
                    player_clicks,
                    e.pos
                )

                if move_made:
                    valid_moves, game_status = refresh_game_state(gs)

        if game_status == ONGOING_STATUS and not gs.white_to_move:
            bot_thinking = True
            status_text = get_turn_text(gs, True, bot_thinking, bot_last_think_time)
            draw_game_state(screen, gs, valid_moves, selected_sq, status_text)
            pygame.display.flip()

            start_time = time.perf_counter()
            ai_move = get_ai_move(gs, valid_moves)
            bot_last_think_time = time.perf_counter() - start_time
            bot_thinking = False

            if ai_move:
                gs.make_move(ai_move, promotion_piece=Queen)
                valid_moves, game_status = refresh_game_state(gs)

        status_text = get_turn_text(gs, True, bot_thinking, bot_last_think_time)
        draw_game_state(screen, gs, valid_moves, selected_sq, status_text)
        clock.tick(FPS)
        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Шахматы")
    clock = pygame.time.Clock()

    load_images()

    while True:
        mode = show_main_menu(screen, clock)

        if mode == "quit":
            break

        if mode == "human":
            result = run_human_vs_human(screen, clock)
            if result == "quit":
                break

        if mode == "bot":
            result = run_human_vs_bot(screen, clock)
            if result == "quit":
                break

    pygame.quit()


if __name__ == "__main__":
    main()

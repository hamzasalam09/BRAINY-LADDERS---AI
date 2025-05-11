import pygame
import random
import time
import nltk
from nltk.corpus import wordnet
import math

nltk.download('wordnet')

WIDTH, HEIGHT = 600, 700
ROWS, COLS = 10, 10
SQUARE_SIZE = WIDTH // COLS
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (200, 200, 200)

pygame.init()
FONT = pygame.font.SysFont(None, 28)
BIG_FONT = pygame.font.SysFont(None, 40)
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brainy Ladders")

board_img = pygame.image.load("board_image.png").convert()
board_img = pygame.transform.scale(board_img, (WIDTH, WIDTH))

AI_MODE = None
players = [(GREEN, 1), (BLUE, 1)]
current_player = 0

snakes = {32: 10, 34: 6, 48: 26, 62: 18, 88: 89, 95: 56, 97: 78}
ladders = {1: 38, 4: 14, 8: 30, 21: 42, 28: 74, 50: 67, 71: 92, 88: 99}

easy_riddles = [
    ("What has hands but can't clap?", "clock"),
    ("What has to be broken before you can use it?", "egg"),
    ("What has a face and two hands but no arms or legs?", "clock"),
    ("What has one eye but can't see?", "needle"),
    ("What can you catch but not throw?", "cold"),
    ("I'm tall when I'm young, and I'm short when I'm old. What am I?", "candle"),
    ("What has a neck but no head?", "bottle"),
    ("The more you take, the more you leave behind. What am I?", "footsteps"),
    ("What has many keys but can't open a single lock?", "piano"),
    ("What gets wetter the more it dries?", "towel")
]
hard_riddles = [
    (syn.definition(), syn.lemmas()[0].name()) for syn in wordnet.all_synsets('n') if len(syn.lemmas()) > 0
]

user_answer = ""
show_question = False
question_text = ""
correct_answer = ""
dice_result = 0
message = ""
awaiting_ai_turn = False

def draw_text_wrapped(surface, text, x, y, font, color, max_width):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    for i, line in enumerate(lines):
        rendered_line = font.render(line, True, color)
        surface.blit(rendered_line, (x, y + i * 30))

def draw_mode_selection():
    WIN.fill(WHITE)
    title = BIG_FONT.render("Choose Game Mode", True, BLACK)
    vs_ai = FONT.render("1. Player vs AI (Press 1)", True, BLACK)
    vs_human = FONT.render("2. Player vs Player (Press 2)", True, BLACK)
    WIN.blit(title, (180, 200))
    WIN.blit(vs_ai, (180, 260))
    WIN.blit(vs_human, (180, 300))
    pygame.display.update()

def get_coords(position):
    position = max(position, 1) - 1
    row = position // 10
    col = position % 10
    col = col if row % 2 == 0 else 9 - col
    x = col * SQUARE_SIZE
    y = (9 - row) * SQUARE_SIZE
    return x, y

def draw_board():
    WIN.blit(board_img, (0, 0))

    for color, pos in players:
        x, y = get_coords(pos)
        pygame.draw.circle(WIN, color, (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2), 10)

    pygame.draw.rect(WIN, GRAY, (0, 600, WIDTH, 100))
    if AI_MODE and current_player == 1:
        turn_msg = "AI's Turn (Click to continue)"
    else:
        turn_msg = f"Player {current_player + 1}'s Turn (Click to Answer)"
    turn_text = BIG_FONT.render(turn_msg, True, BLACK)

    WIN.blit(turn_text, (20, 610))
    result_text = FONT.render(f"{message}", True, BLACK)
    WIN.blit(result_text, (20, 645))

    if show_question:
        pygame.draw.rect(WIN, WHITE, (50, 250, 500, 200))
        pygame.draw.rect(WIN, BLACK, (50, 250, 500, 200), 2)
        draw_text_wrapped(WIN, question_text, 60, 270, FONT, BLACK, 480)
        input_text = FONT.render(f"Your Answer: {user_answer}", True, BLACK)
        WIN.blit(input_text, (60, 350))

    pygame.display.update()

def animate_move(player_index, steps):
    global players
    color, pos = players[player_index]
    for _ in range(steps):
        pos += 1
        if pos > 100:
            pos = 100
        players[player_index] = (color, pos)
        draw_board()
        pygame.time.wait(200)
    if pos in snakes:
        pos = snakes[pos]
    elif pos in ladders:
        pos = ladders[pos]
    players[player_index] = (color, pos)

def move_player(player_index, steps):
    animate_move(player_index, steps)

def bayesian_win_estimate(ai_pos, human_pos):
    return 1 / (1 + math.exp(human_pos - ai_pos))

def ask_question():
    global question_text, correct_answer
    _, pos = players[current_player]
    _, opp_pos = players[1 - current_player]
    if AI_MODE and current_player == 1:
        prob = bayesian_win_estimate(pos, opp_pos)
        q = random.choice(easy_riddles if prob < 0.4 else hard_riddles)
    else:
        lead = pos - opp_pos
        q = random.choice(easy_riddles if lead < -10 else hard_riddles if lead > 10 else easy_riddles + random.sample(hard_riddles, 10))
    question_text = q[0] if isinstance(q[0], str) else str(q[0])
    correct_answer = q[1].lower()

def check_answer():
    return user_answer.lower().strip() == correct_answer

def ai_turn():
    global dice_result, message
    dice_result = random.randint(1, 6)
    move_player(current_player, dice_result)
    message = f"AI rolled a {dice_result}."

def choose_mode():
    global AI_MODE
    selecting = True
    while selecting:
        draw_mode_selection()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    AI_MODE = True
                    selecting = False
                elif event.key == pygame.K_2:
                    AI_MODE = False
                    selecting = False

def main():
    global current_player, show_question, user_answer, dice_result, message, awaiting_ai_turn
    choose_mode()
    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(FPS)
        draw_board()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.KEYDOWN and show_question:
                if event.key == pygame.K_BACKSPACE:
                    user_answer = user_answer[:-1]
                elif event.key == pygame.K_RETURN:
                    if check_answer():
                        dice_result = random.randint(1, 6)
                        message = f"Correct! Rolled a {dice_result}."
                        move_player(current_player, dice_result)
                    else:
                        message = f"Incorrect. The correct answer was: {correct_answer}. Click to continue."
                    show_question = False
                    user_answer = ""
                    if players[current_player][1] == 100:
                        message = f"Player {current_player + 1} wins!"
                        run = False
                    else:
                        current_player = (current_player + 1) % 2
                        if AI_MODE and current_player == 1:
                            awaiting_ai_turn = True
                else:
                    user_answer += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and not show_question:
                if AI_MODE and current_player == 1:
                    if awaiting_ai_turn:
                        message = f"AI is thinking." 
                        draw_board()  
                        pygame.time.wait(500)  

                        ai_turn()
                        draw_board()  

                        if players[current_player][1] == 100:
                            message = f"Player {current_player + 1} (AI) wins!"
                            run = False
                        else:
                            current_player = 0
                            message = f"AI rolled a {dice_result}. Your turn! Click to answer."
                            awaiting_ai_turn = False
                    continue
                ask_question()
                show_question = True
                message = f"Solve the riddle to roll the dice!"

    pygame.quit()

if __name__ == "__main__":
    main()

import pygame
import sys
import math
import random
import json
import os

# Pygameの初期化
pygame.init()
pygame.mixer.init()

# 画面サイズとFPS設定
WIDTH, HEIGHT = 800, 600
FPS = 60

# 色の定義
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
GRAY   = (200, 200, 200)
DARK_GRAY = (80, 80, 80)
RED    = (255, 0, 0)
BLUE   = (0, 0, 255)
YELLOW = (255, 215, 0)

# 定数設定
BASE_BALL_SPEED = 5.66
SPEED_INCREMENT = 0.3  # エンドレスモードの各waveでの速度増加量

# Paddleの設定
PADDLE_WIDTH  = 100
PADDLE_HEIGHT = 15
PADDLE_SPEED  = 7

# Ballの設定
BALL_RADIUS = 10

# ブロックレイアウトの設定
BLOCK_ROWS    = 3
BLOCK_COLS    = 8
BLOCK_WIDTH   = 80
BLOCK_HEIGHT  = 20
BLOCK_PADDING = 10
BLOCK_OFFSET_TOP  = 50
BLOCK_OFFSET_LEFT = 35

POINTS_PER_BLOCK = 10

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data.json")

try:
    collision_sound = pygame.mixer.Sound("hit.mp3")
except (pygame.error, FileNotFoundError):
    collision_sound = None

try:
    celebratory_sound = pygame.mixer.Sound("fanfare.mp3")
except (pygame.error, FileNotFoundError):
    celebratory_sound = None


def load_save_data():
    default = {"endless_mode_unlocked": False, "story_best_score": 0, "endless_best_score": 0}
    if not os.path.exists(SAVE_FILE):
        return default
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, val in default.items():
            data.setdefault(key, val)
        return data
    except (json.JSONDecodeError, IOError):
        return default


def save_save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def circle_rect_collision(cx, cy, radius, rect):
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top,  min(cy, rect.bottom))
    distance_x = cx - closest_x
    distance_y = cy - closest_y
    return (distance_x ** 2 + distance_y ** 2) < (radius ** 2)


def create_blocks():
    blocks = []
    for row in range(BLOCK_ROWS):
        for col in range(BLOCK_COLS):
            x = BLOCK_OFFSET_LEFT + col * (BLOCK_WIDTH + BLOCK_PADDING)
            y = BLOCK_OFFSET_TOP + row * (BLOCK_HEIGHT + BLOCK_PADDING)
            blocks.append(pygame.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT))
    return blocks


def reset_game(mode="story", wave=1):
    paddle = pygame.Rect((WIDTH - PADDLE_WIDTH) // 2, HEIGHT - 50, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball_speed = BASE_BALL_SPEED + SPEED_INCREMENT * (wave - 1) if mode == "endless" else BASE_BALL_SPEED
    ball = {'x': WIDTH / 2, 'y': HEIGHT / 2, 'vx': 4, 'vy': -4}
    blocks = create_blocks()
    _normalize_velocity(ball, ball_speed)
    return paddle, ball, blocks, 0, ball_speed


def _normalize_velocity(ball, speed):
    magnitude = math.sqrt(ball['vx'] ** 2 + ball['vy'] ** 2)
    if magnitude != 0:
        ball['vx'] = ball['vx'] / magnitude * speed
        ball['vy'] = ball['vy'] / magnitude * speed


def show_confetti(screen, duration_ms=3000):
    confetti = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
              (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    for _ in range(100):
        confetti.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(-50, 0),
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(2, 5),
            'color': random.choice(colors),
            'size': random.randint(2, 5)
        })
    start_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    while pygame.time.get_ticks() - start_time < duration_ms:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        for p in confetti:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['y'] > HEIGHT:
                p['y'] = random.randint(-50, 0)
                p['x'] = random.randint(0, WIDTH)
        screen.fill(BLACK)
        for p in confetti:
            pygame.draw.rect(screen, p['color'],
                             (int(p['x']), int(p['y']), p['size'], p['size']))
        pygame.display.flip()


def draw_start_screen(screen, font, small_font, save_data):
    screen.fill(BLACK)

    # タイトル
    title = font.render("Block Breaking Game", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 80)))

    # 記録表示
    story_best = save_data["story_best_score"]
    story_rec = small_font.render(f"Story Best: {story_best}", True, YELLOW)
    screen.blit(story_rec, story_rec.get_rect(center=(WIDTH // 2, 170)))

    if save_data["endless_mode_unlocked"]:
        endless_best = save_data["endless_best_score"]
        endless_rec = small_font.render(f"Endless Best: {endless_best}", True, YELLOW)
    else:
        endless_rec = small_font.render("Endless Best: ???", True, GRAY)
    screen.blit(endless_rec, endless_rec.get_rect(center=(WIDTH // 2, 210)))

    # ボタン共通サイズ
    btn_w, btn_h = 220, 60

    # Story Mode ボタン
    story_rect = pygame.Rect(0, 0, btn_w, btn_h)
    story_rect.center = (WIDTH // 2, 320)
    pygame.draw.rect(screen, BLUE, story_rect, border_radius=8)
    story_label = font.render("Story Mode", True, WHITE)
    screen.blit(story_label, story_label.get_rect(center=story_rect.center))

    # Endless Mode ボタン
    endless_rect = pygame.Rect(0, 0, btn_w, btn_h)
    endless_rect.center = (WIDTH // 2, 420)
    unlocked = save_data["endless_mode_unlocked"]
    btn_color = BLUE if unlocked else DARK_GRAY
    pygame.draw.rect(screen, btn_color, endless_rect, border_radius=8)
    endless_label = font.render("Endless Mode", True, WHITE if unlocked else GRAY)
    screen.blit(endless_label, endless_label.get_rect(center=endless_rect.center))

    if not unlocked:
        lock_label = small_font.render("[Clear Story to Unlock]", True, GRAY)
        screen.blit(lock_label, lock_label.get_rect(center=(WIDTH // 2, 490)))

    pygame.display.flip()
    return story_rect, endless_rect


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ブロック崩し")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 32)

    save_data = load_save_data()
    state = "start"
    paddle, ball, blocks, score, ball_speed = None, None, None, 0, BASE_BALL_SPEED
    wave = 1
    story_btn, endless_btn = None, None

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "start" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if story_btn and story_btn.collidepoint(pos):
                    state = "story"
                    wave = 1
                    paddle, ball, blocks, score, ball_speed = reset_game("story", wave)
                elif endless_btn and endless_btn.collidepoint(pos) and save_data["endless_mode_unlocked"]:
                    state = "endless"
                    wave = 1
                    paddle, ball, blocks, score, ball_speed = reset_game("endless", wave)

        if state == "start":
            story_btn, endless_btn = draw_start_screen(screen, font, small_font, save_data)
            continue

        # --- パドル操作 ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT]:
            paddle.x += PADDLE_SPEED
        paddle.left  = max(0, paddle.left)
        paddle.right = min(WIDTH, paddle.right)

        # --- ボールの更新 ---
        ball['x'] += ball['vx']
        ball['y'] += ball['vy']

        # --- 壁との衝突 ---
        if ball['x'] - BALL_RADIUS < 0:
            ball['x'] = BALL_RADIUS
            ball['vx'] = -ball['vx']
            if collision_sound: collision_sound.play()
        if ball['x'] + BALL_RADIUS > WIDTH:
            ball['x'] = WIDTH - BALL_RADIUS
            ball['vx'] = -ball['vx']
            if collision_sound: collision_sound.play()
        if ball['y'] - BALL_RADIUS < 0:
            ball['y'] = BALL_RADIUS
            ball['vy'] = -ball['vy']
            if collision_sound: collision_sound.play()

        # --- パドルとの衝突 ---
        if circle_rect_collision(ball['x'], ball['y'], BALL_RADIUS, paddle):
            ball['y'] = paddle.top - BALL_RADIUS
            ball['vy'] = -abs(ball['vy'])
            if collision_sound: collision_sound.play()
            offset = (ball['x'] - paddle.centerx) / (PADDLE_WIDTH / 2)
            ball['vx'] += offset * 2

        # --- ブロックとの衝突 ---
        for block in blocks[:]:
            if circle_rect_collision(ball['x'], ball['y'], BALL_RADIUS, block):
                blocks.remove(block)
                ball['vy'] = -ball['vy']
                if collision_sound: collision_sound.play()
                score += POINTS_PER_BLOCK
                break

        _normalize_velocity(ball, ball_speed)

        # --- ブロック全滅処理 ---
        if not blocks:
            if state == "story":
                # ストーリーモードクリア
                if score > save_data["story_best_score"]:
                    save_data["story_best_score"] = score
                save_data["endless_mode_unlocked"] = True
                save_save_data(save_data)

                clear_text = font.render("Game Clear!", True, RED)
                screen.fill(BLACK)
                screen.blit(clear_text, clear_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                pygame.display.flip()
                if celebratory_sound: celebratory_sound.play()
                show_confetti(screen, 3000)
                state = "start"

            elif state == "endless":
                # 次のwaveへ
                wave += 1
                ball_speed = BASE_BALL_SPEED + SPEED_INCREMENT * (wave - 1)
                blocks = create_blocks()
                # ボールを中央にリセット
                ball['x'], ball['y'] = WIDTH / 2, HEIGHT / 2
                ball['vx'], ball['vy'] = 4, -4
                _normalize_velocity(ball, ball_speed)
            continue

        # --- ゲームオーバー ---
        if ball['y'] - BALL_RADIUS > HEIGHT:
            if state == "endless":
                if score > save_data["endless_best_score"]:
                    save_data["endless_best_score"] = score
                    save_save_data(save_data)

            over_text = font.render("Game Over!", True, RED)
            screen.fill(BLACK)
            screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            pygame.display.flip()
            pygame.time.wait(2000)
            state = "start"
            continue

        # --- 描画 ---
        screen.fill(BLACK)
        pygame.draw.rect(screen, BLUE, paddle)
        pygame.draw.circle(screen, WHITE, (int(ball['x']), int(ball['y'])), BALL_RADIUS)
        for block in blocks:
            pygame.draw.rect(screen, GRAY, block)
        score_text = small_font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, score_text.get_rect(topright=(WIDTH - 10, 10)))
        if state == "endless":
            wave_text = small_font.render(f"Wave: {wave}", True, WHITE)
            screen.blit(wave_text, wave_text.get_rect(topleft=(10, 10)))

        pygame.display.flip()


if __name__ == "__main__":
    main()

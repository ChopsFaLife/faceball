import pygame, sys, math, time

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Basketball Face Shot")

clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 80, 80)
LIGHT_BLUE = (180, 220, 255)

# --- Load assets (use / so pygbag finds them in web root) ---
ball_img = pygame.image.load("/ball.png")
ball_img = pygame.transform.scale(ball_img, (40, 40))

hoop_img = pygame.image.load("/hoop.png")
hoop_img = pygame.transform.scale(hoop_img, (120, 120))

face_img = pygame.image.load("/default_face.png")
face_img = pygame.transform.scale(face_img, (100, 100))

bg_raw = pygame.image.load("/background.png")
bg_raw = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))
background = bg_raw.convert_alpha()
background.set_alpha(100)  # ~40% visible

# Positions
avatar_pos = (80, HEIGHT - 150)
g = 0.8  # gravity strength

# Game state
score = 0
high_score = 0
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)

show_score_text = False
score_timer = 0

# Hoop position
hoop_rect = hoop_img.get_rect(center=(WIDTH - 200, 250))

# Input state
dragging = False
drag_start = None

# Timer logic
game_duration = 30
time_left = game_duration
game_active = False
game_over = False
start_time = None

# Multi-ball storage
balls = []  # each = {"pos": Vector2, "vel": Vector2}


def spawn_ball(vel=None):
    """Spawn a ball at avatar hand with optional velocity"""
    start_pos = pygame.Vector2(avatar_pos[0] + 30, avatar_pos[1] + 50)
    new_ball = {"pos": start_pos, "vel": pygame.Vector2(0, 0)}
    if vel:
        new_ball["vel"] = vel
    balls.append(new_ball)


def restart_game():
    global score, time_left, game_active, game_over, start_time, balls
    score = 0
    time_left = game_duration
    game_active = False
    game_over = False
    start_time = None
    balls = []
    spawn_ball()


def draw(trajectory_points=None, power_ratio=0):
    # Background
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))

    # Hoop with oval backdrop
    hoop_backdrop = hoop_rect.inflate(40, 40)
    pygame.draw.ellipse(screen, LIGHT_BLUE, hoop_backdrop)
    screen.blit(hoop_img, hoop_rect)

    # Avatar with oval backdrop
    avatar_rect = pygame.Rect(avatar_pos[0], avatar_pos[1],
                              face_img.get_width(), face_img.get_height())
    avatar_backdrop = avatar_rect.inflate(40, 40)
    pygame.draw.ellipse(screen, LIGHT_BLUE, avatar_backdrop)
    screen.blit(face_img, avatar_pos)

    # Balls
    for b in balls:
        screen.blit(ball_img, b["pos"])

    # Score + high score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (20, 20))
    hs_text = small_font.render(f"High Score: {high_score}", True, WHITE)
    screen.blit(hs_text, (20, 60))

    # Timer
    if game_active:
        timer_text = font.render(f"{int(time_left)}", True, WHITE)
        screen.blit(timer_text, (WIDTH - 100, 20))
    elif game_over:
        over_text = font.render("GAME OVER", True, RED)
        screen.blit(over_text, (WIDTH // 2 - 120, HEIGHT // 2 - 40))
        restart_text = small_font.render("Tap or SPACE to restart", True, WHITE)
        screen.blit(restart_text, (WIDTH // 2 - 140, HEIGHT // 2 + 10))

    # “SCORE!” popup
    if show_score_text:
        stext = small_font.render("SCORE!", True, WHITE)
        screen.blit(stext, (hoop_rect.centerx - 40, hoop_rect.top - 30))

    # Trajectory preview
    if trajectory_points:
        for point in trajectory_points:
            pygame.draw.circle(screen, WHITE, (int(point[0]), int(point[1])), 3)

    # Power meter
    if power_ratio > 0 and not game_over:
        bar_x = avatar_pos[0]
        bar_y = avatar_pos[1] + 110
        bar_w = 100
        bar_h = 12
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)
        fill_w = int(bar_w * min(1.0, power_ratio))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_w, bar_h))

    pygame.display.flip()


# --- Main loop ---
restart_game()
running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_over:
                restart_game()

        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN) and not game_over:
            dragging = True
            drag_start = (event.pos if hasattr(event, "pos")
                          else (event.x * WIDTH, event.y * HEIGHT))

        elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP) and dragging:
            drag_end = (event.pos if hasattr(event, "pos")
                        else (event.x * WIDTH, event.y * HEIGHT))
            dx = drag_start[0] - drag_end[0]
            dy = drag_start[1] - drag_end[1]
            vel = pygame.Vector2(dx * 0.6, dy * 0.6)
            spawn_ball(vel)
            dragging = False
            if not game_active and not game_over:
                game_active = True
                start_time = time.time()

    # Timer
    if game_active and not game_over:
        elapsed = time.time() - start_time
        time_left = max(0, game_duration - elapsed)
        if time_left <= 0:
            game_active = False
            game_over = True
            if score > high_score:
                high_score = score

    # Update balls
    for b in balls[:]:
        b["vel"].y += g * (dt * 60 / 16)
        b["pos"] += b["vel"] * (dt * 60 / 16)
        bx, by = b["pos"].x + 20, b["pos"].y + 20

        # Score check
        hoop_cx, hoop_cy = hoop_rect.center
        if (hoop_rect.left < bx < hoop_rect.right and
                hoop_cy - 10 < by < hoop_cy + 10 and b["vel"].y > 0):
            score += 1
            show_score_text = True
            score_timer = time.time()
            balls.remove(b)
            continue

        # Remove if out of bounds
        if (b["pos"].y > HEIGHT + 100 or
                b["pos"].x < -100 or b["pos"].x > WIDTH + 100):
            balls.remove(b)

    # Hide SCORE! popup
    if show_score_text and time.time() - score_timer > 1:
        show_score_text = False

    # Trajectory preview
    trajectory_points = None
    power_ratio = 0
    if dragging and not game_over:
        current = pygame.mouse.get_pos()
        dx = drag_start[0] - current[0]
        dy = drag_start[1] - current[1]
        vel = pygame.Vector2(dx * 0.6, dy * 0.6)
        sim_pos = pygame.Vector2(avatar_pos[0] + 30, avatar_pos[1] + 50)
        sim_vel = pygame.Vector2(vel)
        trajectory_points = []
        for _ in range(15):
            sim_vel.y += g
            sim_pos += sim_vel * 0.2
            if 0 < sim_pos.x < WIDTH and 0 < sim_pos.y < HEIGHT:
                trajectory_points.append((sim_pos.x + 20, sim_pos.y + 20))
        drag_len = math.hypot(dx, dy)
        power_ratio = min(drag_len / 300, 1.0)

    draw(trajectory_points, power_ratio)

pygame.quit()
sys.exit()

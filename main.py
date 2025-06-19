import pygame
import random
import math
import sys
from collections import deque
from enum import Enum

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 700
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DodgeMaster++ Enhanced Edition")

# Clock initialization
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (150, 50, 255)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 105, 180)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

# Event colors with transparency
EVENT_COLORS = {
    'RAIN_OF_FIRE': (255, 50, 50, 100),
    'BLACK_HOLE': (0, 0, 0, 150),
    'TIME_WARP': (150, 50, 255, 100)
}

# Power-Up types
class PowerUpType(Enum):
    SPEED_BOOST = 1
    SHIELD = 2
    TIME_SLOW = 3
    MAGNET = 4

# Special Event types
class SpecialEvent(Enum):
    RAIN_OF_FIRE = 1
    MOVING_BLACK_HOLE = 2
    TIME_WARP = 3

# Fonts
font_small = pygame.font.SysFont("Arial", 20)
font_medium = pygame.font.SysFont("Arial", 24)
font_large = pygame.font.SysFont("Arial", 48)
font_title = pygame.font.SysFont("Impact", 72)

# Game states
MENU = 0
GAME = 1
SETTINGS = 2
GAME_OVER = 3
current_state = MENU

# Eye animation variables
BLINK_RATE = 0.01
BLINK_DURATION = 10
player_blinking = 0
enemy_blinking = 0
player_eye_direction = [0, 1]
enemy_eye_direction = [0, 1]
last_enemy_x, last_enemy_y = 0, 0

# Power-Up variables
powerups = []
powerup_duration = 300  # frames (5 seconds at 60fps)
powerup_spawn_rate = 900  # frames (15 seconds)
powerup_timer = 0
active_powerup = None
powerup_active_time = 0
shield_active = False

# Special Event variables
special_events = []
special_event_active = None
special_event_timer = 0
special_event_duration = 480  # 8 seconds
next_special_event_score = 600
black_hole = None
time_warp_factor = 1.0

# Particle effects
particles = []

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)
        
        text_surf = font_medium.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_rect = pygame.Rect(x, y, 20, height + 10)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.text = text
        self.dragging = False
        self.update_knob_pos()
        
    def update_knob_pos(self):
        relative_val = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_rect.x = self.rect.x + int(relative_val * self.rect.width) - 10
        
    def draw(self, surface):
        # Draw slider track
        pygame.draw.rect(surface, LIGHT_GRAY, self.rect, border_radius=5)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2, border_radius=5)
        
        # Draw slider knob
        pygame.draw.rect(surface, BLUE, self.knob_rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.knob_rect, 2, border_radius=5)
        
        # Draw text and value
        text_surf = font_small.render(f"{self.text}: {self.value:.1f}", True, WHITE)
        surface.blit(text_surf, (self.rect.x, self.rect.y - 25))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Calculate new value based on mouse position
            mouse_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            relative_pos = (mouse_x - self.rect.left) / self.rect.width
            self.value = self.min_val + relative_pos * (self.max_val - self.min_val)
            self.update_knob_pos()
            return True
        return False

class AIController:
    def __init__(self):
        self.prediction_strength = 0.5
        self.aggressiveness = 1.0
        
    def predict_player_position(self, history):
        if len(history) < 2:
            return player.center
        
        dx, dy = 0, 0
        for i in range(1, len(history)):
            dx += (history[i][0] - history[i-1][0]) * self.aggressiveness
            dy += (history[i][1] - history[i-1][1]) * self.aggressiveness
        
        dx /= (len(history) - 1)
        dy /= (len(history) - 1)
        
        last_pos = history[-1]
        predicted_x = last_pos[0] + dx * self.prediction_strength * 10
        predicted_y = last_pos[1] + dy * self.prediction_strength * 10
        
        return predicted_x, predicted_y
    
    def adjust_difficulty(self, score, hits_avoided):
        global enemy_speed, projectile_spawn_rate
        
        base_factor = min(1 + score / 5000, 3)
        performance_factor = 1 + (1 - min(hits_avoided / max(score, 1), 1)) * 2
        
        enemy_speed = base_enemy_speed * base_factor * performance_factor * 0.8 * self.aggressiveness * time_warp_factor
        projectile_spawn_rate = max(10, 30 - score // 500)
        self.prediction_strength = min(0.9, 0.5 + score / 10000)

def draw_eyes(rect, direction, blinking, color=WHITE):
    if blinking > 0:
        pygame.draw.arc(win, color, (rect.centerx - 10, rect.centery - 5, 20, 10), 0, math.pi, 2)
        pygame.draw.arc(win, color, (rect.centerx - 10, rect.centery - 5, 20, 10), 0, math.pi, 2)
    else:
        dir_len = math.sqrt(direction[0]**2 + direction[1]**2)
        norm_dir = (direction[0]/max(dir_len, 0.1), direction[1]/max(dir_len, 0.1))
        
        pygame.draw.circle(win, color, (int(rect.centerx - 5 + norm_dir[0] * 8), int(rect.centery - 5 + norm_dir[1] * 5)), 3)
        pygame.draw.circle(win, color, (int(rect.centerx + 5 + norm_dir[0] * 8), int(rect.centery - 5 + norm_dir[1] * 5)), 3)

def update_blinking():
    global player_blinking, enemy_blinking
    
    if player_blinking > 0:
        player_blinking -= 1
    elif random.random() < BLINK_RATE:
        player_blinking = BLINK_DURATION
        
    if enemy_blinking > 0:
        enemy_blinking -= 1
    elif random.random() < BLINK_RATE:
        enemy_blinking = BLINK_DURATION

def create_particles(x, y, color, count=20):
    for _ in range(count):
        particles.append({
            'x': x,
            'y': y,
            'dx': random.uniform(-2, 2),
            'dy': random.uniform(-2, 2),
            'size': random.randint(2, 5),
            'life': random.randint(20, 40),
            'color': color
        })

def update_particles():
    for p in particles[:]:
        p['x'] += p['dx']
        p['y'] += p['dy']
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)

def draw_particles():
    for p in particles:
        alpha = min(255, p['life'] * 6)
        if len(p['color']) == 4:  # If color has alpha
            color = p['color']
        else:
            color = (*p['color'], alpha)
        s = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (p['size']//2, p['size']//2), p['size']//2)
        win.blit(s, (p['x'], p['y']))

def spawn_powerup():
    powerup_type = random.choice(list(PowerUpType))
    x = random.randint(50, WIDTH - 50)
    y = random.randint(50, HEIGHT - 50)
    
    colors = {
        PowerUpType.SPEED_BOOST: ORANGE,
        PowerUpType.SHIELD: CYAN,
        PowerUpType.TIME_SLOW: PURPLE,
        PowerUpType.MAGNET: YELLOW
    }
    
    powerups.append({
        'type': powerup_type,
        'rect': pygame.Rect(x, y, 20, 20),
        'color': colors[powerup_type],
        'animation_timer': 0
    })

def activate_powerup(powerup):
    global active_powerup, powerup_active_time, player_speed, base_enemy_speed, shield_active, enemy_speed
    
    active_powerup = powerup['type']
    powerup_active_time = powerup_duration
    
    if active_powerup == PowerUpType.SPEED_BOOST:
        player_speed *= 1.5
    elif active_powerup == PowerUpType.SHIELD:
        shield_active = True
    elif active_powerup == PowerUpType.TIME_SLOW:
        base_enemy_speed *= 0.5
        enemy_speed *= 0.5
        for p in projectiles:
            p['dx'] *= 0.5
            p['dy'] *= 0.5
    elif active_powerup == PowerUpType.MAGNET:
        # Attract nearby powerups
        for p in powerups[:]:
            dx = player.centerx - p['rect'].centerx
            dy = player.centery - p['rect'].centery
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            if dist < 200:  # Magnet range
                p['rect'].x += dx * 0.05
                p['rect'].y += dy * 0.05
    
    create_particles(powerup['rect'].centerx, powerup['rect'].centery, powerup['color'], 50)

def deactivate_powerup():
    global active_powerup, player_speed, base_enemy_speed, shield_active, enemy_speed
    
    if active_powerup == PowerUpType.SPEED_BOOST:
        player_speed = player_speed_slider.value
    elif active_powerup == PowerUpType.SHIELD:
        shield_active = False
    elif active_powerup == PowerUpType.TIME_SLOW:
        base_enemy_speed = 2
        enemy_speed = base_enemy_speed * ai_controller.aggressiveness
    
    active_powerup = None

def spawn_special_event():
    global special_event_active, special_event_timer, black_hole, time_warp_factor
    
    event_type = random.choice(list(SpecialEvent))
    print(f"Attempting to spawn event: {event_type}")
    special_event_active = event_type
    special_event_timer = special_event_duration
    
    # Create visual effect particles
    if event_type == SpecialEvent.RAIN_OF_FIRE:
        # Spawn 30 projectiles from top
        for _ in range(30):
            projectiles.append({
                'rect': pygame.Rect(random.randint(0, WIDTH), 0, 10, 10),
                'dx': random.uniform(-1, 1),
                'dy': random.uniform(2, 5)
            })
        # Red rain particles
        for _ in range(100):
            particles.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(-50, 0),
                'dx': random.uniform(-1, 1),
                'dy': random.uniform(2, 5),
                'size': random.randint(2, 6),
                'life': random.randint(60, 120),
                'color': EVENT_COLORS['RAIN_OF_FIRE']
            })
    elif event_type == SpecialEvent.MOVING_BLACK_HOLE:
        # Create a black hole that moves across the screen
        print("Creating moving black hole")
        start_side = random.choice(['top', 'bottom', 'left', 'right'])
        if start_side == 'top':
            x, y = random.randint(100, WIDTH-100), -50
            dx, dy = random.uniform(-1, 1), random.uniform(1, 2)
        elif start_side == 'bottom':
            x, y = random.randint(100, WIDTH-100), HEIGHT+50
            dx, dy = random.uniform(-1, 1), random.uniform(-2, -1)
        elif start_side == 'left':
            x, y = -50, random.randint(100, HEIGHT-100)
            dx, dy = random.uniform(1, 2), random.uniform(-1, 1)
        else:  # right
            x, y = WIDTH+50, random.randint(100, HEIGHT-100)
            dx, dy = random.uniform(-2, -1), random.uniform(-1, 1)
            
        black_hole = {
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'radius': 40,
            'strength': 0.7
        }
        
        # Create swirling particles
        for _ in range(50):
            angle = random.uniform(0, 2*math.pi)
            dist = random.uniform(30, 100)
            particles.append({
                'x': x + math.cos(angle) * dist,
                'y': y + math.sin(angle) * dist,
                'dx': math.sin(angle) * 2 + dx,
                'dy': -math.cos(angle) * 2 + dy,
                'size': random.randint(2, 4),
                'life': random.randint(90, 180),
                'color': EVENT_COLORS['BLACK_HOLE']
            })

def draw_special_event_effects():
    if special_event_active == SpecialEvent.MOVING_BLACK_HOLE and black_hole:
        # Change colors to be more visible (temporarily for testing)
        pygame.draw.circle(win, (255, 0, 0), (int(black_hole['x']), int(black_hole['y'])), black_hole['radius'])  # Red for testing
        pygame.draw.circle(win, (150, 0, 0), (int(black_hole['x']), int(black_hole['y'])), black_hole['radius'] - 10)
        
        # Draw bright accretion disk
        for i in range(1, 4):
            radius = black_hole['radius'] + i * 15
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 100, 100, 150), (radius, radius), radius, 3)  # Bright pink
            win.blit(s, (int(black_hole['x'] - radius), int(black_hole['y'] - radius)))

def draw_powerup_indicator():
    if active_powerup:
        # Background bar
        bar_width = 200
        bar_height = 20
        bar_x = WIDTH//2 - bar_width//2
        bar_y = 10
        
        # Calculate progress
        progress = 1 - (powerup_active_time / powerup_duration)
        
        # Draw background
        pygame.draw.rect(win, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        # Draw progress
        pygame.draw.rect(win, BLUE, (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=10)
        # Draw border
        pygame.draw.rect(win, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)
        
        # Draw powerup icon
        icon_size = 15
        if active_powerup == PowerUpType.SPEED_BOOST:
            pygame.draw.polygon(win, ORANGE, [
                (bar_x + 5, bar_y + bar_height//2),
                (bar_x + 5 + icon_size, bar_y + bar_height),
                (bar_x + 5 + icon_size, bar_y)
            ])
        elif active_powerup == PowerUpType.SHIELD:
            pygame.draw.circle(win, CYAN, (bar_x + 5 + icon_size//2, bar_y + bar_height//2), icon_size//2, 2)
        elif active_powerup == PowerUpType.TIME_SLOW:
            pygame.draw.rect(win, PURPLE, (bar_x + 5, bar_y + 2, icon_size, bar_height - 4))
        elif active_powerup == PowerUpType.MAGNET:
            pygame.draw.line(win, YELLOW, (bar_x + 5, bar_y + bar_height//2), 
                           (bar_x + 5 + icon_size, bar_y + bar_height//2), 3)
            pygame.draw.line(win, YELLOW, (bar_x + 5 + icon_size//2, bar_y + 2), 
                           (bar_x + 5 + icon_size//2, bar_y + bar_height - 2), 3)

def draw_special_event_indicator():
    if special_event_active:
        event_names = {
            SpecialEvent.RAIN_OF_FIRE: "RAIN OF FIRE!",
            SpecialEvent.MOVING_BLACK_HOLE: "MOVING BLACK HOLE!",  # Updated
            SpecialEvent.TIME_WARP: "TIME WARP!"
        }
        
        remaining_time = max(0, special_event_duration - special_event_timer)
        text = font_medium.render(event_names[special_event_active], True, RED)
        
        # Pulsing effect
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 255
        s = pygame.Surface((text.get_width() + 20, text.get_height() + 10), pygame.SRCALPHA)
        s.fill((255, 255, 255, pulse//3))
        win.blit(s, (WIDTH//2 - text.get_width()//2 - 10, HEIGHT - 60))
        
        win.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 50))
        
        # Draw event-specific effects
        draw_special_event_effects()
        
def end_special_event():
    global special_event_active, black_hole, time_warp_factor
    
    if special_event_active == SpecialEvent.MOVING_BLACK_HOLE:  # Changed from BLACK_HOLE
        black_hole = None
    elif special_event_active == SpecialEvent.TIME_WARP:
        time_warp_factor = 1.0
    
    special_event_active = None

def apply_black_hole_physics():
    global black_hole
    
    if not black_hole: 
        return
    
    # Update position first
    black_hole['x'] += black_hole['dx'] * time_warp_factor
    black_hole['y'] += black_hole['dy'] * time_warp_factor
    
    # Remove if it goes off screen
    if (black_hole['x'] < -100 or black_hole['x'] > WIDTH+100 or
        black_hole['y'] < -100 or black_hole['y'] > HEIGHT+100):
        black_hole = None
        return
    
    # Rest of physics code remains the same...
    
    # Affect player with stronger close-range pull
    dx = black_hole['x'] - player.centerx
    dy = black_hole['y'] - player.centery
    dist = max(10, math.sqrt(dx*dx + dy*dy))
    
    if dist < 300:  # Larger effect radius
        pull_strength = black_hole['strength'] * (300-dist)/300
        player.x += (dx/dist) * pull_strength * 3
        player.y += (dy/dist) * pull_strength * 3
    
    # Affect projectiles
    for p in projectiles[:]:
        dx = black_hole['x'] - p['rect'].centerx
        dy = black_hole['y'] - p['rect'].centery
        dist_sq = dx*dx + dy*dy
        if dist_sq > 0:
            dist = math.sqrt(dist_sq)
            if dist < 300:
                force = black_hole['strength'] * (1 - dist/300)
                p['rect'].x += dx * 0.02 * force
                p['rect'].y += dy * 0.02 * force
    
    # Affect powerups
    for p in powerups[:]:
        dx = black_hole['x'] - p['rect'].centerx
        dy = black_hole['y'] - p['rect'].centery
        dist_sq = dx*dx + dy*dy
        if dist_sq > 0:
            dist = math.sqrt(dist_sq)
            if dist < 300:
                force = black_hole['strength'] * (1 - dist/300)
                p['rect'].x += dx * 0.015 * force
                p['rect'].y += dy * 0.015 * force

# Game objects
player_size = 30
player = pygame.Rect(WIDTH // 2, HEIGHT // 2, player_size, player_size)
player_speed = 5

enemy_size = 30
enemy = pygame.Rect(random.randint(0, WIDTH - enemy_size), random.randint(0, HEIGHT - enemy_size), enemy_size, enemy_size)
base_enemy_speed = 2
enemy_speed = base_enemy_speed

projectiles = []
projectile_spawn_rate = 30
projectile_timer = 0

player_pos_history = deque(maxlen=20)
ai_controller = AIController()

# GUI Elements
play_button = Button(WIDTH//2 - 100, 300, 200, 50, "Play", BLUE, PURPLE)
settings_button = Button(WIDTH//2 - 100, 370, 200, 50, "Settings", BLUE, PURPLE)
quit_button = Button(WIDTH//2 - 100, 440, 200, 50, "Quit", RED, (255, 100, 100))
restart_button = Button(WIDTH//2 - 100, 400, 200, 50, "Play Again", BLUE, PURPLE)
menu_button = Button(WIDTH//2 - 100, 480, 200, 50, "Main Menu", BLUE, PURPLE)
back_button = Button(50, HEIGHT - 80, 150, 50, "Back", BLUE, PURPLE)
ai_aggressiveness_slider = Slider(300, 300, 400, 20, 0.1, 2.0, 1.0, "AI Aggressiveness")
player_speed_slider = Slider(300, 400, 400, 20, 3, 10, 5, "Player Speed")

def spawn_projectile():
    side = random.choice(['top', 'bottom', 'left', 'right'])
    speed = random.uniform(2.0, 5.0) * (1 + ai_controller.aggressiveness) * time_warp_factor
    
    if side == 'top':
        x, y = random.randint(0, WIDTH), 0
    elif side == 'bottom':
        x, y = random.randint(0, WIDTH), HEIGHT
    elif side == 'left':
        x, y = 0, random.randint(0, HEIGHT)
    else:
        x, y = WIDTH, random.randint(0, HEIGHT)

    target_x, target_y = ai_controller.predict_player_position(player_pos_history) if len(player_pos_history) > 5 else player.center
    angle = math.atan2(target_y - y, target_x - x)
    return {'rect': pygame.Rect(x, y, 10, 10), 'dx': math.cos(angle) * speed, 'dy': math.sin(angle) * speed}

def reset_game():
    global player, enemy, projectiles, score, hits_avoided, player_pos_history
    global powerups, active_powerup, powerup_active_time, shield_active
    global special_event_active, special_event_timer, next_special_event_score
    global black_hole, time_warp_factor, particles
    
    player = pygame.Rect(WIDTH // 2, HEIGHT // 2, player_size, player_size)
    enemy = pygame.Rect(random.randint(0, WIDTH - enemy_size), random.randint(0, HEIGHT - enemy_size), enemy_size, enemy_size)
    projectiles = []
    powerups = []
    particles = []
    score = 0
    hits_avoided = 0
    player_pos_history = deque(maxlen=20)
    active_powerup = None
    powerup_active_time = 0
    shield_active = False
    special_event_active = None
    special_event_timer = 0
    next_special_event_score = 600
    black_hole = None
    time_warp_factor = 1.0

def draw_main_menu():
    win.fill(BLACK)
    title_text = font_title.render("DodgeMaster++", True, BLUE)
    subtitle_text = font_large.render("Enhanced Edition", True, PURPLE)
    win.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
    win.blit(subtitle_text, (WIDTH//2 - subtitle_text.get_width()//2, 180))
    
    play_button.draw(win)
    settings_button.draw(win)
    quit_button.draw(win)
    
    footer_text = font_small.render("Use arrow keys or WASD to move. Avoid the red squares!", True, WHITE)
    win.blit(footer_text, (WIDTH//2 - footer_text.get_width()//2, HEIGHT - 50))

def draw_settings():
    win.fill(BLACK)
    
    title_text = font_large.render("Settings", True, WHITE)
    win.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
    
    ai_aggressiveness_slider.draw(win)
    player_speed_slider.draw(win)
    
    info_text = font_small.render("Adjust the AI behavior and game parameters", True, WHITE)
    win.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 200))
    
    back_button.draw(win)

def draw_game():
    win.fill(BLACK)
    update_blinking()
    
    # Draw particles first (background effects)
    draw_particles()
    
    # Draw black hole if active
    draw_special_event_effects()
    
    # Draw powerups
    for powerup in powerups:
        # Animate powerup pulsing
        powerup['animation_timer'] += 1
        pulse = math.sin(powerup['animation_timer'] * 0.1) * 2 + 22
        pygame.draw.circle(win, powerup['color'], powerup['rect'].center, int(pulse))
        pygame.draw.circle(win, WHITE, powerup['rect'].center, 10)
        
        # Draw icon based on powerup type
        if powerup['type'] == PowerUpType.SPEED_BOOST:
            pygame.draw.polygon(win, BLACK, [
                (powerup['rect'].centerx, powerup['rect'].centery - 8),
                (powerup['rect'].centerx + 8, powerup['rect'].centery + 8),
                (powerup['rect'].centerx - 8, powerup['rect'].centery + 8)
            ])
        elif powerup['type'] == PowerUpType.SHIELD:
            pygame.draw.circle(win, BLACK, powerup['rect'].center, 6, 2)
            pygame.draw.circle(win, BLACK, powerup['rect'].center, 8, 2)
        elif powerup['type'] == PowerUpType.TIME_SLOW:
            pygame.draw.rect(win, BLACK, (powerup['rect'].centerx - 6, powerup['rect'].centery - 8, 12, 16))
        elif powerup['type'] == PowerUpType.MAGNET:
            pygame.draw.line(win, BLACK, 
                           (powerup['rect'].centerx - 8, powerup['rect'].centery),
                           (powerup['rect'].centerx + 8, powerup['rect'].centery), 3)
            pygame.draw.line(win, BLACK, 
                           (powerup['rect'].centerx, powerup['rect'].centery - 8),
                           (powerup['rect'].centerx, powerup['rect'].centery + 8), 3)
    
    # Draw characters with eyes
    pygame.draw.rect(win, GREEN, player)
    draw_eyes(player, player_eye_direction, player_blinking)
    
    # Draw shield if active
    if shield_active:
        shield_alpha = min(255, (powerup_duration - powerup_active_time) * 255 // powerup_duration)
        s = pygame.Surface((player_size + 20, player_size + 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (*CYAN, shield_alpha), (player_size//2 + 10, player_size//2 + 10), player_size//2 + 10, 3)
        win.blit(s, (player.x - 10, player.y - 10))
    
    pygame.draw.rect(win, BLUE, enemy)
    draw_eyes(enemy, enemy_eye_direction, enemy_blinking)
    
    for p in projectiles:
        pygame.draw.rect(win, RED, p['rect'])
    
    # Draw active powerup indicator
    draw_powerup_indicator()
    
    # Draw special event indicator
    draw_special_event_indicator()
    
    # Display stats
    score_text = font_medium.render(f"Score: {score}", True, WHITE)
    difficulty_text = font_medium.render(f"AI Aggressiveness: {ai_controller.aggressiveness:.1f}", True, WHITE)
    win.blit(score_text, (10, 10))
    win.blit(difficulty_text, (10, 40))
    
    # Draw time warp effect if active
    if time_warp_factor != 1.0:
        warp_text = font_small.render(f"TIME x{time_warp_factor:.1f}", True, PINK)
        win.blit(warp_text, (WIDTH - 100, 40))

def draw_game_over():
    win.fill(BLACK)
    game_over_text = font_large.render("Game Over!", True, RED)
    score_text = font_medium.render(f"Final Score: {score}", True, WHITE)
    win.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 200))
    win.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 280))
    
    feedback = ""
    if score > 5000:
        feedback = "Amazing! You're an AI training master!"
    elif score > 2000:
        feedback = "Great job! The AI had trouble predicting you!"
    else:
        feedback = "The AI outsmarted you this time. Try again!"
    
    feedback_text = font_medium.render(feedback, True, YELLOW)
    win.blit(feedback_text, (WIDTH//2 - feedback_text.get_width()//2, 340))
    
    restart_button.draw(win)
    menu_button.draw(win)

# Game stats
score = 0
hits_avoided = 0
paused = False
run = True

# Main game loop
while run:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        
        # Handle button hover states
        if current_state == MENU:
            play_button.check_hover(mouse_pos)
            settings_button.check_hover(mouse_pos)
            quit_button.check_hover(mouse_pos)
            
            if play_button.is_clicked(mouse_pos, event):
                current_state = GAME
                reset_game()
            elif settings_button.is_clicked(mouse_pos, event):
                current_state = SETTINGS
            elif quit_button.is_clicked(mouse_pos, event):
                run = False
                
        elif current_state == SETTINGS:
            back_button.check_hover(mouse_pos)
            ai_aggressiveness_slider.handle_event(event)
            player_speed_slider.handle_event(event)
            
            if back_button.is_clicked(mouse_pos, event):
                current_state = MENU
                
        elif current_state == GAME_OVER:
            restart_button.check_hover(mouse_pos)
            menu_button.check_hover(mouse_pos)
            
            if restart_button.is_clicked(mouse_pos, event):
                current_state = GAME
                reset_game()
            elif menu_button.is_clicked(mouse_pos, event):
                current_state = MENU
        
        # Pause game with ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and current_state == GAME:
            paused = not paused
    
    # Update AI settings from sliders
    ai_controller.aggressiveness = ai_aggressiveness_slider.value
    player_speed = player_speed_slider.value
    
    # Game logic when not paused and in game state
    if current_state == GAME and not paused:
        # Update particles
        update_particles()
        
        # Powerup spawning
        powerup_timer += 1
        if powerup_timer >= powerup_spawn_rate:
            spawn_powerup()
            powerup_timer = 0
        
        # Update active powerup timer
        if active_powerup:
            powerup_active_time += 1
            if powerup_active_time >= powerup_duration:
                deactivate_powerup()
        
        # Check for powerup collisions
        for powerup in powerups[:]:
            if player.colliderect(powerup['rect']):
                activate_powerup(powerup)
                powerups.remove(powerup)
                break
        
        # Check for special event triggering
        if score >= next_special_event_score:
            spawn_special_event()
            next_special_event_score += 600  # Set next threshold
        
        # Update special event timer
        if special_event_active:
            special_event_timer += 1
            if special_event_timer >= special_event_duration:
                end_special_event()
        
        # Apply black hole physics if active
        if black_hole:
            apply_black_hole_physics()
        
        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.x -= player_speed * time_warp_factor
            player_eye_direction = [-1, 0]
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.x += player_speed * time_warp_factor
            player_eye_direction = [1, 0]
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player.y -= player_speed * time_warp_factor
            player_eye_direction = [0, -1]
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player.y += player_speed * time_warp_factor
            player_eye_direction = [0, 1]
        player.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        
        # Record player position for AI
        player_pos_history.append((player.centerx, player.centery))
        
        # AI-controlled enemy movement
        predicted_x, predicted_y = ai_controller.predict_player_position(player_pos_history)
        angle = math.atan2(predicted_y - enemy.centery, predicted_x - enemy.centerx)
        enemy.x += int(math.cos(angle) * enemy_speed * time_warp_factor)
        enemy.y += int(math.sin(angle) * enemy_speed * time_warp_factor)
        
        enemy_eye_direction = [enemy.x - last_enemy_x, enemy.y - last_enemy_y]
        last_enemy_x, last_enemy_y = enemy.x, enemy.y
        
        # Projectile spawning
        projectile_timer += 1
        if projectile_timer >= projectile_spawn_rate:
            projectiles.append(spawn_projectile())
            projectile_timer = 0
        
        # Update projectiles
        for p in projectiles[:]:
            p['rect'].x += p['dx'] * time_warp_factor
            p['rect'].y += p['dy'] * time_warp_factor
            
            if (p['rect'].x < -50 or p['rect'].x > WIDTH + 50 or 
                p['rect'].y < -50 or p['rect'].y > HEIGHT + 50):
                projectiles.remove(p)
                hits_avoided += 1
        
        # Collision detection
        if not shield_active:
            for p in projectiles[:]:
                if player.colliderect(p['rect']):
                    create_particles(player.centerx, player.centery, RED, 30)
                    current_state = GAME_OVER
                    break
        
        if player.colliderect(enemy):
            create_particles(player.centerx, player.centery, RED, 30)
            current_state = GAME_OVER
        
        # Update score and difficulty
        score += 1
        ai_controller.adjust_difficulty(score, hits_avoided)
    
    # Drawing
    if current_state == MENU:
        draw_main_menu()
    elif current_state == SETTINGS:
        draw_settings()
    elif current_state == GAME:
        draw_game()
        if paused:
            # Draw pause overlay
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            win.blit(s, (0, 0))
            pause_text = font_large.render("PAUSED", True, WHITE)
            win.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2))
    elif current_state == GAME_OVER:
        draw_game_over()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
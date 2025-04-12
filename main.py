import pygame
import sys
from collections import deque

# ---------------------------------------------------
# Konstante Einstellungen
# ---------------------------------------------------
WIDTH = 800
HEIGHT = 600
TILE_SIZE = 20
FPS = 10

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (100, 100, 100)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)

# ---------------------------------------------------
# Snake-Klasse: Spieler oder KI
# ---------------------------------------------------
class Snake:
    def __init__(self, x, y, color=GREEN, is_ai=False):
        self.segments = [(x, y)]
        self.direction = (0, 0)  # zu Beginn keine Bewegung
        self.grow_segments = 0
        self.color = color
        self.is_ai = is_ai
        self.alive = True

    def head_position(self):
        """Aktuelle Position des Snake-Kopfes."""
        return self.segments[0]

    def move(self):
        """Bewegt die Schlange um ein Feld."""
        if not self.alive:
            return

        x, y = self.head_position()
        dx, dy = self.direction
        new_head = (x + dx, y + dy)

        # Schlange "schiebt" sich nach: vorderster Block kommt vorne, letzter fällt weg
        self.segments.insert(0, new_head)
        if self.grow_segments > 0:
            self.grow_segments -= 1
        else:
            self.segments.pop()

    def grow(self):
        """Vergrößert Schlange."""
        self.grow_segments += 1

    def set_direction(self, dx, dy):
        """Setzt neue Bewegungsrichtung, wenn es nicht die entgegengesetzte ist."""
        # Keine 180°-Drehung
        current_dx, current_dy = self.direction
        if (dx, dy) != (-current_dx, -current_dy):
            self.direction = (dx, dy)

    def check_collision_with_self(self):
        """Überprüft Selbst-Kollision."""
        if len(self.segments) > 4 and self.head_position() in self.segments[1:]:
            self.alive = False

    def check_collision_with_wall(self, max_cols, max_rows):
        """Überprüft Wand-Kollision."""
        x, y = self.head_position()
        if x < 0 or x >= max_cols or y < 0 or y >= max_rows:
            self.alive = False

# ---------------------------------------------------
# KI-Controller für die Schlange (BFS Pfadfindung)
# ---------------------------------------------------
class AIController:
    def __init__(self):
        pass

    def get_move(self, snake, food_pos, grid_cols, grid_rows, obstacles):
        """Berechnet den nächsten Schritt per BFS vom Schlangenkopf zum Food."""
        # BFS, um kürzesten Weg zu finden
        start = snake.head_position()
        if start == food_pos:
            return snake.direction  # schon auf dem Food
        visited = set([start])
        queue = deque()
        # queue-Einträge: (position, path)
        queue.append((start, []))

        found_path = None

        while queue:
            current_pos, path = queue.popleft()
            if current_pos == food_pos:
                found_path = path
                break

            x, y = current_pos
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = x+dx, y+dy
                # Prüfen, ob im Spielfeld
                if 0 <= nx < grid_cols and 0 <= ny < grid_rows:
                    # Hindernisse: Schlangen-Segmente + visited
                    if (nx, ny) not in obstacles and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [(dx, dy)]))

        if found_path and len(found_path) > 0:
            # Nächster Schritt auf dem Pfad
            return found_path[0]
        else:
            # Keine Route gefunden -> z.B. zufällige oder "Nicht bewegen"
            return snake.direction

# ---------------------------------------------------
# Hauptspiel-Klasse
# ---------------------------------------------------
class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake AI Arena - Demo")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        # Anzahl Kacheln in x- und y-Richtung
        self.grid_cols = WIDTH // TILE_SIZE
        self.grid_rows = HEIGHT // TILE_SIZE

        # Initialisiere Schlangen
        # Spieler1 (Pfeiltasten)
        self.snake1 = Snake(self.grid_cols // 2, self.grid_rows // 2, color=GREEN, is_ai=False)
        # Spieler2 (WASD)
        self.snake2 = Snake(self.grid_cols // 2, (self.grid_rows // 2)+3, color=BLUE, is_ai=False)
        # KI Snake
        self.ai_snake = Snake((self.grid_cols // 2), (self.grid_rows // 2)-6, color=RED, is_ai=True)
        self.ai_controller = AIController()

        # Erstes Essen generieren
        self.food_position = (5, 5)

        # Scores
        self.score1 = 0
        self.score2 = 0
        self.score_ai = 0

        # Spielstatus
        self.running = True

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Eingaben / Events verarbeiten."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Snake1 Steuerung (Pfeiltasten)
                if event.key == pygame.K_UP:
                    self.snake1.set_direction(0, -1)
                elif event.key == pygame.K_DOWN:
                    self.snake1.set_direction(0, 1)
                elif event.key == pygame.K_LEFT:
                    self.snake1.set_direction(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.snake1.set_direction(1, 0)

                # Snake2 Steuerung (WASD)
                if event.key == pygame.K_w:
                    self.snake2.set_direction(0, -1)
                elif event.key == pygame.K_s:
                    self.snake2.set_direction(0, 1)
                elif event.key == pygame.K_a:
                    self.snake2.set_direction(-1, 0)
                elif event.key == pygame.K_d:
                    self.snake2.set_direction(1, 0)

    def update(self):
        """Spielzustand updaten (Positionen, Kollisionen, KI)."""

        # --- KI-Bewegung berechnen (BFS) ---
        obstacles = self.get_all_snake_positions()
        next_move_ai = self.ai_controller.get_move(
            self.ai_snake, self.food_position,
            self.grid_cols, self.grid_rows, obstacles
        )
        self.ai_snake.set_direction(next_move_ai[0], next_move_ai[1])

        # --- Schlangen bewegen ---
        self.snake1.move()
        self.snake2.move()
        self.ai_snake.move()

        # --- Kollision mit Food ---
        self.check_food_collision(self.snake1, player_id=1)
        self.check_food_collision(self.snake2, player_id=2)
        self.check_food_collision(self.ai_snake, player_id=3)

        # --- Kollision mit eigener Schlange ---
        self.snake1.check_collision_with_self()
        self.snake2.check_collision_with_self()
        self.ai_snake.check_collision_with_self()

        # --- Kollision mit Wand ---
        self.snake1.check_collision_with_wall(self.grid_cols, self.grid_rows)
        self.snake2.check_collision_with_wall(self.grid_cols, self.grid_rows)
        self.ai_snake.check_collision_with_wall(self.grid_cols, self.grid_rows)

    def check_food_collision(self, snake, player_id):
        """Prüfen, ob der Snake-Kopf auf das Essen trifft."""
        if snake.alive and snake.head_position() == self.food_position:
            snake.grow()
            # Score
            if player_id == 1:
                self.score1 += 1
            elif player_id == 2:
                self.score2 += 1
            else:
                self.score_ai += 1
            # Neues Essen
            self.spawn_food()

    def spawn_food(self):
        """Neues Food an zufälliger Stelle platzieren, die nicht von einer Schlange belegt ist."""
        import random
        while True:
            new_x = random.randint(0, self.grid_cols - 1)
            new_y = random.randint(0, self.grid_rows - 1)
            if (new_x, new_y) not in self.get_all_snake_positions():
                self.food_position = (new_x, new_y)
                break

    def get_all_snake_positions(self):
        """Gibt eine Menge aller Snake-Felder zurück (für die KI)."""
        obstacles = set()
        if self.snake1.alive:
            obstacles.update(self.snake1.segments)
        if self.snake2.alive:
            obstacles.update(self.snake2.segments)
        if self.ai_snake.alive:
            obstacles.update(self.ai_snake.segments)
        return obstacles

    def draw(self):
        """Alles auf den Bildschirm zeichnen."""
        self.screen.fill(BLACK)

        # Food zeichnen
        fx, fy = self.food_position
        pygame.draw.rect(self.screen, WHITE, (fx*TILE_SIZE, fy*TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Snake1
        self.draw_snake(self.snake1)
        # Snake2
        self.draw_snake(self.snake2)
        # AI-Snake
        self.draw_snake(self.ai_snake)

        # Scores
        score_text = f"Score P1: {self.score1}   Score P2: {self.score2}   Score AI: {self.score_ai}"
        text_surface = self.font.render(score_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))

        pygame.display.flip()

    def draw_snake(self, snake):
        """Snake zeichnen."""
        if not snake.alive:
            return
        for (x, y) in snake.segments:
            rect = (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, snake.color, rect)

# ---------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------
if __name__ == "__main__":
    game = SnakeGame()
    game.run()

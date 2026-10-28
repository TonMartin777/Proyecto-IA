import pygame
import random
import sys
import math

# --- CONFIGURACIÓN GRÁFICA ---
CELL_SIZE = 20  # Tamaño de celda reducido
COLS = 60       # Ampliado a 60 columnas
ROWS = 30       # Ampliado a 30 filas
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

# Colores (R, G, B)
WHITE = (240, 240, 240)
BLACK = (40, 40, 40)
GRAY = (200, 200, 200)
BLUE = (50, 100, 255)
RED = (220, 50, 50)
YELLOW = (255, 215, 0)
VISION_COLOR = (0, 180, 150, 90)

class GameEnvironment:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.agent_pos = None
        self.goal_pos = None
        self.obstacles = []
        self.enemies = []

    def set_agent(self, x, y):
        self.agent_pos = (x, y)

    def set_goal(self, x, y):
        self.goal_pos = (x, y)

    def add_enemy(self, x, y, dx=0, dy=1):
        self.enemies.append({'pos': (x, y), 'dir': (dx, dy)})

    def add_obstacle_rect(self, start_x, start_y, width, height):
        for x in range(start_x, start_x + width):
            for y in range(start_y, start_y + height):
                if (x, y) not in self.obstacles:
                    self.obstacles.append((x, y))

    def has_line_of_sight(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if (x0, y0) in self.obstacles:
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return True

    def calculate_vision_cones(self):
        vision_cells = set()
        VIEW_RADIUS = 12
        FOV_ANGLE = math.radians(45)
        HALF_FOV = FOV_ANGLE / 2

        for enemy in self.enemies:
            ex, ey = enemy['pos']
            dx, dy = enemy['dir']
            enemy_angle = math.atan2(dy, dx)

            for y in range(max(0, ey - VIEW_RADIUS), min(self.height, ey + VIEW_RADIUS + 1)):
                for x in range(max(0, ex - VIEW_RADIUS), min(self.width, ex + VIEW_RADIUS + 1)):
                    if x == ex and y == ey:
                        continue
                    
                    dist = math.hypot(x - ex, y - ey)
                    if dist <= VIEW_RADIUS:
                        cell_angle = math.atan2(y - ey, x - ex)
                        angle_diff = abs(math.atan2(math.sin(cell_angle - enemy_angle), 
                                                    math.cos(cell_angle - enemy_angle)))
                        
                        if angle_diff <= HALF_FOV:
                            if self.has_line_of_sight(ex, ey, x, y):
                                vision_cells.add((x, y))
        return vision_cells

    def run_simulation(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simulador de Sigilo - Entorno Masivo (60x30)")
        clock = pygame.time.Clock()
        vision_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        turn_delay = 500
        last_turn_time = pygame.time.get_ticks()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            current_time = pygame.time.get_ticks()
            if current_time - last_turn_time > turn_delay:
                # Rotación enemiga aleatoria para testear el rebote de la visión en los muros
                for enemy in self.enemies:
                    if random.random() < 0.20:
                        enemy['dir'] = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
                last_turn_time = current_time

            screen.fill(WHITE)
            vision_surface.fill((0, 0, 0, 0))
            
            # Dibujar cuadrícula y obstáculos gruesos
            for y in range(self.height):
                for x in range(self.width):
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    # Dibujar líneas de cuadrícula muy tenues
                    pygame.draw.rect(screen, (220, 220, 220), rect, 1)
                    if (x, y) in self.obstacles:
                        # Rellenar los bloques macizos
                        pygame.draw.rect(screen, BLACK, rect)
            
            # Dibujar Meta
            gx, gy = self.goal_pos
            pygame.draw.rect(screen, YELLOW, (gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            
            # Dibujar Conos de Visión
            vision_cells = self.calculate_vision_cones()
            for vx, vy in vision_cells:
                rect = pygame.Rect(vx * CELL_SIZE, vy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(vision_surface, VISION_COLOR, rect)
            screen.blit(vision_surface, (0, 0))
            
            # Dibujar Enemigos
            for enemy in self.enemies:
                ex, ey = enemy['pos']
                cx, cy = ex * CELL_SIZE + CELL_SIZE // 2, ey * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(screen, RED, (cx, cy), CELL_SIZE // 2 - 2)
                dx, dy = enemy['dir']
                pygame.draw.line(screen, BLACK, (cx, cy), (cx + dx * (CELL_SIZE // 2), cy + dy * (CELL_SIZE // 2)), 3)

            # Dibujar Agente
            if self.agent_pos:
                ax, ay = self.agent_pos
                pygame.draw.circle(screen, BLUE, (ax * CELL_SIZE + CELL_SIZE // 2, ay * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 2)
            
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    env = GameEnvironment(COLS, ROWS)
    
    # --- CREACIÓN DEL ESCENARIO A GRAN ESCALA (60x30) ---
    # add_obstacle_rect(x_inicial, y_inicial, ancho_columnas, alto_filas)
    
    # Complejo Noroeste
    env.add_obstacle_rect(5, 5, 15, 5)
    env.add_obstacle_rect(5, 15, 5, 10)
    
    # Gran Pabellón Central
    env.add_obstacle_rect(25, 5, 10, 20)
    
    # Zonas Este y Sureste
    env.add_obstacle_rect(40, 10, 15, 5)
    env.add_obstacle_rect(45, 20, 5, 8)
    env.add_obstacle_rect(15, 20, 5, 5)
    
    # Posición inicial del Agente (Esquina superior izquierda)
    env.set_agent(2, 2)
    
    # Posición de la Meta (Esquina inferior derecha)
    env.set_goal(57, 27)
    
    # --- PATRULLAS ENEMIGAS ---
    # Vigila el pasillo entre el complejo noroeste y el pabellón central
    env.add_enemy(22, 10, dx=0, dy=1)    
    
    # Vigila el corredor superior derecho
    env.add_enemy(48, 5, dx=-1, dy=0)  
    
    # Cubre el espacio estrecho entre el pabellón central y la zona este
    env.add_enemy(37, 15, dx=0, dy=-1) 
    
    # Vigila la parte inferior del mapa
    env.add_enemy(30, 27, dx=-1, dy=0) 
    
    # Guardia en la esquina suroeste
    env.add_enemy(8, 27, dx=1, dy=0)
    
    # Guardia protegiendo la aproximación final a la meta
    env.add_enemy(54, 22, dx=0, dy=1)
    
    env.run_simulation()
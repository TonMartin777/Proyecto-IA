import pygame
import random
import sys
import math

# --- CONFIGURACIÓN GRÁFICA ---
CELL_SIZE = 20  
COLS = 60       
ROWS = 30       
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

    def add_enemy(self, x, y, dx=0, dy=1, patrol_route=None):
        self.enemies.append({
            'pos': (x, y), 
            'dir': (dx, dy),
            'patrol_route': patrol_route if patrol_route else [],
            'patrol_index': 0
        })

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
        VIEW_RADIUS = 18
        FOV_ANGLE = math.radians(60) 
        HALF_FOV = FOV_ANGLE / 3

        for enemy in self.enemies:
            ex, ey = enemy['pos']
            dx, dy = enemy['dir']
            enemy_angle = math.atan2(dy, dx)

            for y in range(max(0, ey - VIEW_RADIUS), min(self.height, ey + VIEW_RADIUS + 1)):
                for x in range(max(0, ex - VIEW_RADIUS), min(self.width, ex + VIEW_RADIUS + 1)):
                    if x == ex and y == ey:
                        continue
                    
                    dist = math.hypot(x - ex, y - ey)
                    
                    # 1. Filtro inicial amplio por distancia máxima
                    if dist <= VIEW_RADIUS:
                        cell_angle = math.atan2(y - ey, x - ex)
                        angle_diff = abs(math.atan2(math.sin(cell_angle - enemy_angle), 
                                                    math.cos(cell_angle - enemy_angle)))
                        
                        # 2. Comprobar si está dentro del abanico angular
                        if angle_diff <= HALF_FOV:
                            
                            # 3. EL REDONDEO: Reducir el alcance efectivo en los bordes del cono.
                            # Si el ángulo se acerca al límite (HALF_FOV), el radio permitido es menor.
                            # math.cos( (angle_diff / HALF_FOV) * (math.pi / 2) ) crea una curva suave.
                            effective_radius = VIEW_RADIUS * math.cos((angle_diff / HALF_FOV) * (math.pi / 4))
                            
                            if dist <= effective_radius:
                                if self.has_line_of_sight(ex, ey, x, y):
                                    vision_cells.add((x, y))
        return vision_cells

    def update_enemy_patrols(self):
        for enemy in self.enemies:
            if not enemy['patrol_route']:
                continue # Si no tiene ruta de patrulla, se queda quieto (puede rotar si se desea)

            ex, ey = enemy['pos']
            route = enemy['patrol_route']
            target_x, target_y = route[enemy['patrol_index']]

            # Si el enemigo ya está en el punto destino, cambia al siguiente punto
            if ex == target_x and ey == target_y:
                enemy['patrol_index'] = (enemy['patrol_index'] + 1) % len(route)
                target_x, target_y = route[enemy['patrol_index']]

            # Calcular la dirección del movimiento hacia el objetivo (en línea recta)
            dx = 0
            if target_x > ex: dx = 1
            elif target_x < ex: dx = -1
            
            dy = 0
            if target_y > ey: dy = 1
            elif target_y < ey: dy = -1

            # Calcular el siguiente paso
            next_x, next_y = ex + dx, ey + dy
            
            # Verificar colisiones con obstáculos o bordes del mapa
            # En una patrulla simple, si choca, debería detenerse (o recalcular con A* después)
            if 0 <= next_x < self.width and 0 <= next_y < self.height and (next_x, next_y) not in self.obstacles:
                enemy['pos'] = (next_x, next_y)
                enemy['dir'] = (dx, dy) # La visión se alinea con el movimiento


    def run_simulation(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simulador de Sigilo - Patrullas Dinámicas")
        clock = pygame.time.Clock()
        vision_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        turn_delay = 300 # Reducido un poco para que el movimiento sea fluido
        last_turn_time = pygame.time.get_ticks()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            current_time = pygame.time.get_ticks()
            if current_time - last_turn_time > turn_delay:
                # Actualizar la posición y dirección de los enemigos según sus patrullas
                self.update_enemy_patrols()
                last_turn_time = current_time

            screen.fill(WHITE)
            vision_surface.fill((0, 0, 0, 0))
            
            # Dibujar cuadrícula y obstáculos gruesos
            for y in range(self.height):
                for x in range(self.width):
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(screen, (220, 220, 220), rect, 1)
                    if (x, y) in self.obstacles:
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
    env.add_obstacle_rect(5, 5, 15, 5)
    env.add_obstacle_rect(5, 15, 5, 10)
    env.add_obstacle_rect(25, 5, 10, 20)
    env.add_obstacle_rect(40, 10, 15, 5)
    env.add_obstacle_rect(45, 20, 5, 8)
    env.add_obstacle_rect(15, 20, 5, 5)
    
    env.set_agent(2, 2)
    env.set_goal(57, 27)
    
    # --- PATRULLAS ENEMIGAS ---
    # Patrulla horizontal de lado a lado
    env.add_enemy(22, 10, dx=0, dy=1, patrol_route=[(22, 10), (22, 25), (22, 10)])    
    
    # Patrulla a lo largo de un pasillo ancho
    env.add_enemy(48, 5, dx=-1, dy=0, patrol_route=[(48, 5), (38, 5), (48, 5)])  
    
    # Patrulla vertical entre edificios
    env.add_enemy(37, 15, dx=0, dy=-1, patrol_route=[(37, 15), (37, 28), (37, 15)]) 
    
    # Patrulla cerca de la zona final
    env.add_enemy(30, 27, dx=-1, dy=0, patrol_route=[(30, 27), (15, 27), (30, 27)]) 
    
    # Guardias estáticos (sin ruta, solo vigilan una dirección)
    env.add_enemy(8, 27, dx=1, dy=0)
    env.add_enemy(54, 22, dx=0, dy=1)
    
    env.run_simulation()
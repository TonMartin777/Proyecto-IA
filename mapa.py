import os
import time
import random

class GameEnvironment:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [['.' for _ in range(width)] for _ in range(height)]
        
        self.agent_pos = None
        self.goal_pos = None
        self.obstacles = []
        
        # Los enemigos guardan su posición y la dirección hacia la que miran
        # Formato: {'pos': (x, y), 'dir': (dx, dy)}
        self.enemies = []

    # Posición inicial del agente
    def set_agent(self, x, y):
        self.agent_pos = (x, y)

    # Posición del objetivo
    def set_goal(self, x, y):
        self.goal_pos = (x, y)
        self.grid[y][x] = 'G'

    # Añadir enemigo
    def add_enemy(self, x, y, dx=0, dy=1):
        self.enemies.append({'pos': (x, y), 'dir': (dx, dy)})

    # Añadir muro
    def add_obstacle(self, x, y):
        self.obstacles.append((x, y))

    # Comprueba si el movimiento que se intenta es valido
    def is_valid_move(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        if (x, y) in self.obstacles:
            return False
        return True

    # Calcula los conos de visión de los enemigos
    def calculate_vision_cones(self):
        vision_cells = set()
        for enemy in self.enemies:
            ex, ey = enemy['pos']
            dx, dy = enemy['dir']
            
            # El enemigo ve hasta 2 casillas en la dirección que mira
            for step in range(1, 3):
                vx, vy = ex + (dx * step), ey + (dy * step)
                if self.is_valid_move(vx, vy):
                    vision_cells.add((vx, vy))
                else:
                    break # La visión se bloquea con las paredes
        return vision_cells

    # Actualiza la matriz
    def update_grid(self):
        self.grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        
        # Dibujar Meta y Obstáculos
        if self.goal_pos:
            self.grid[self.goal_pos[1]][self.goal_pos[0]] = 'G'
        for ox, oy in self.obstacles:
            self.grid[oy][ox] = '#'
            
        # Dibujar visión de los enemigos (con una 'v')
        vision_cells = self.calculate_vision_cones()
        for vx, vy in vision_cells:
            self.grid[vy][vx] = 'v'
            
        # Dibujar Enemigos
        for enemy in self.enemies:
            ex, ey = enemy['pos']
            self.grid[ey][ex] = 'E'
            
        # Dibujar Agente
        if self.agent_pos:
            ax, ay = self.agent_pos
            self.grid[ay][ax] = 'S'

    def print_environment(self):
        # Limpia la consola según el sistema operativo (Windows o Linux/Mac)
        os.system('cls' if os.name == 'nt' else 'clear')
        self.update_grid()
        print("\n--- Simulador de Sigilo ---")
        for row in self.grid:
            print(" ".join(row))
        print("---------------------------\n")

    def run_simulation(self):
        game_over = False
        
        while not game_over:
            self.print_environment()
            
            ax, ay = self.agent_pos
            
            # Condición de victoria
            if self.agent_pos == self.goal_pos:
                print("¡Misión Cumplida! El agente ha llegado a la extracción.")
                break
                
            # Condición de derrota (pisar a un enemigo o entrar en su visión)
            vision_cells = self.calculate_vision_cones()
            enemy_positions = [e['pos'] for e in self.enemies]
            if self.agent_pos in vision_cells or self.agent_pos in enemy_positions:
                print("¡ALERTA! El agente ha sido detectado.")
                break

            # --- TURNO DEL AGENTE ---
            # Movimiento aleatorio simple para probar el motor (más adelante usaremos Q-Learning)
            moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            random.shuffle(moves)
            for dx, dy in moves:
                next_x, next_y = ax + dx, ay + dy
                if self.is_valid_move(next_x, next_y):
                    self.agent_pos = (next_x, next_y)
                    break
                    
            # --- TURNO DE LOS ENEMIGOS ---
            # Rotar aleatoriamente la visión de los enemigos
            for enemy in self.enemies:
                enemy['dir'] = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])

            # Pausa para crear el efecto de animación
            time.sleep(0.5)

# --- Prueba del escenario ---
if __name__ == "__main__":
    env = GameEnvironment(10, 10)
    
    paredes = [(2,1), (2,2), (2,3), (4,4), (4,5), (5,2)]
    for px, py in paredes:
        env.add_obstacle(px, py)
        
    env.set_agent(0, 0)
    env.set_goal(6, 6)
    
    # Añadimos enemigos especificando hacia dónde miran inicialmente
    env.add_enemy(3, 1, dx=0, dy=1) # Mira hacia abajo
    env.add_enemy(4, 6, dx=-1, dy=0) # Mira hacia la izquierda
    
    env.run_simulation()
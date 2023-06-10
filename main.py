import pygame
import random
import math

# pygame setup
pygame.init()
GRIDTILE_SIZE = 8
WIDTH = GRIDTILE_SIZE * 160
HEIGHT = GRIDTILE_SIZE * 80
SCREEN_SIZE = (WIDTH, HEIGHT)
screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()
FPS = 60
MAIN_FONT = pygame.font.Font(None, 36)


def main_loop():
    # setup
    running = True

    n_rows = HEIGHT // GRIDTILE_SIZE
    n_cols = WIDTH // GRIDTILE_SIZE

    colonies = [AntColony(color="gray", grid_spawn_location=(random.randint(10, 90), random.randint(10, 40)))]
    
    food_sources = [FoodSource((random.randint(0, WIDTH), random.randint(0, HEIGHT))) for i in range(3)]
    feromones = {
        "food": [],
        "home": []
    }
    frames_since_start = 0

    grid = {
        "food": {},
        "home": {}
    }
    # MAKE THIS DICTS WITH TUPLE KEYS


    while running:
        frames_since_start += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
        if pygame.key.get_pressed()[pygame.K_g]:
            draw_grid(screen)



        # set background based on current screen
        screen.fill(color="black")

        for fero_type in ["home", "food"]:
            for coords in list(grid[fero_type].keys()):
                fero = grid[fero_type][coords]
                if fero.evaporate(current_frame=frames_since_start):
                    # print(f"Remove feromone at{fero.grid_location}")
                    grid[fero_type].pop(fero.grid_location)

                else:
                    fero.display(screen)
        
        
        # print(f"Amount of feromones: {len(list(grid['food'].keys()) + list(grid['home'].keys()))} | Estimated number of collion checks: {13* 13 * len(colonies[0].all_ants)}")

        for colony in colonies:
            
            if frames_since_start % 60 * 5 == 0:
                colony.spawn_ant()

            colony.display(screen)
            colony.drop_feromone(grid=grid, current_frame=frames_since_start)
            for f in food_sources:
                if f.amount_remaining > 0:
                    f.display(screen)
                else:
                    food_sources.remove(f)
                    food_sources.append(FoodSource((random.randint(0, SCREEN_SIZE[0]), random.randint(0, SCREEN_SIZE[1]))))
                f.drop_feromone(grid=grid, current_frame=frames_since_start)


            for ant in colony.all_ants:
                ant.move(feromones, grid)
                ant.display(screen)
                ant.forage(food_sources)
                ant.return_food()

                if frames_since_start % 5 == 0:
                    # emit fermones
                    ant.drop_feromone(frames_since_start, feromones, grid)
        
        # print(f"{int(clock.get_fps())} FPS")

        # flip() the display to put your work on dawscreen
        pygame.display.flip()

        clock.tick(FPS)


def draw_grid(screen):
    for i in range(0, WIDTH, GRIDTILE_SIZE):
        pygame.draw.line(screen, color="yellow", start_pos=(i, 0), end_pos=(i, HEIGHT))

    for i in range(0, HEIGHT, GRIDTILE_SIZE):
        pygame.draw.line(screen, color="yellow", start_pos=(0, i), end_pos=(WIDTH, i))




class Ant:

    def __init__(self, spawn_loaction, colony) -> None:
        self.colony = colony
        self.rect = pygame.Rect(spawn_loaction, (5, 5))
        self.spawn_loaction = spawn_loaction

        self.x_velocity = 0
        self.y_velocity = 0

        self.max_velocity = 3
        self.color = self.colony.color
        self.has_food = False
        self.looking_for = "food"
        self.step = 0

        self.max_hp = 2000
        self.hp = self.max_hp

        self.surface = pygame.Surface((5, 5))


    def lose_hp(self, amount):
        self.hp -= amount
        # print(self.hp)
        if (self.hp <= self.max_hp // 20) and (self.has_food):
            print("Ant ate")
            self.step += 100 # just in case?
            self.hp = self.max_hp
            self.has_food = False
            self.looking_for = "food"

        elif self.hp <= 0:
            print("Ant died")
            self.colony.all_ants.remove(self)



    def move(self, all_feromones: list, grid):
        # age
        self.lose_hp(1)

        self.step += 1
        fero_x, fero_y = self.search_feromone(all_feromones, grid)
        self.x_velocity += fero_x
        self.y_velocity += fero_y

        if (self.x_velocity > self.max_velocity):
            self.x_velocity = self.max_velocity
        if (self.x_velocity < -self.max_velocity):
            self.x_velocity = -self.max_velocity

        if (self.y_velocity > self.max_velocity):
            self.y_velocity = self.max_velocity
        if (self.y_velocity < -self.max_velocity):
            self.y_velocity = -self.max_velocity

        self.rect = self.rect.move(self.x_velocity, self.y_velocity)

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.bottom > SCREEN_SIZE[1]:
            self.rect.bottom = SCREEN_SIZE[1]
        if self.rect.right > SCREEN_SIZE[0]:
            self.rect.right = SCREEN_SIZE[0]


    def display(self, screen: pygame.Surface):
        
        self.surface.fill(color=self.color)
        if self.has_food:
            food = pygame.Surface(size=(2, 2))
            food.fill("green")
            self.surface.blit(food, dest=(0, 0))
        screen.blit(self.surface, dest=self.rect.topleft)


    def forage(self, food_sources):
        for food in food_sources:
            if self.rect.colliderect(food.rect):
                self.step = 0
                if not self.has_food:
                    self.has_food = True
                    self.looking_for = "home"
                    food.amount_remaining -= 1  


    def return_food(self):
        if self.rect.colliderect(self.colony.rect):
            self.step = 0
            if self.has_food:
                self.has_food = False
                self.looking_for = "food"


    def drop_feromone(self, frames_since_start: int, all_feromones: list, grid):
        coords = (self.rect.left//GRIDTILE_SIZE) * GRIDTILE_SIZE, (self.rect.top//GRIDTILE_SIZE)*GRIDTILE_SIZE
        grid_coords = (coords[0]//GRIDTILE_SIZE, coords[1]//GRIDTILE_SIZE)

        if self.has_food:
            freo_to_drop = "food"
        else:
            freo_to_drop = "home"


        current_feromone_on_grid = grid[freo_to_drop].get(grid_coords, None)
        if current_feromone_on_grid:
            if current_feromone_on_grid.feromone_type == freo_to_drop:
                # already on here
                step = None
                if self.step < current_feromone_on_grid.step:
                    step = self.step
                current_feromone_on_grid.refresh(current_frame=frames_since_start, step=step)
                return
        
        new_feromone = Feromone(coords, freo_to_drop, frame_spawned=frames_since_start, step=self.step)
        all_feromones[freo_to_drop].append(new_feromone)
        grid[freo_to_drop][grid_coords] = new_feromone
        # print(grid)


    def search_feromone(self, all_feromones: list, grid: dict):
        search_range = GRIDTILE_SIZE * 4
        tilerange = 6
        grid_coords = (self.rect.centerx // GRIDTILE_SIZE, self.rect.centery // GRIDTILE_SIZE)
        relevant_feromones = []

        for x in range(grid_coords[0] - tilerange, grid_coords[0] + tilerange):
            for y in range(grid_coords[1] - tilerange, grid_coords[1] + tilerange):
                c = (x, y)
                if grid[self.looking_for].get(c, None):
                    relevant_feromones.append(grid[self.looking_for][c])

        feromone_with_least_steps = None

        for fero in relevant_feromones:
            dist = math.hypot(fero.rect.centerx-self.rect.centerx, fero.rect.centery-self.rect.centery)
            if dist <= tilerange * GRIDTILE_SIZE:
                if not feromone_with_least_steps:
                    feromone_with_least_steps = fero
                
                elif fero.step < feromone_with_least_steps.step:
                    feromone_with_least_steps = fero
                


        random_ignore = random.randint(0, 100) > 90
        if (not feromone_with_least_steps) or (random_ignore):
            return (random.randint(-1, 1), random.randint(-1, 1))
        
        return (feromone_with_least_steps.rect.centerx - self.rect.centerx, feromone_with_least_steps.rect.centery - self.rect.centery)
        

class AntColony:

    def __init__(self, color, grid_spawn_location) -> None:
        self.rect = pygame.Rect((GRIDTILE_SIZE * grid_spawn_location[0], GRIDTILE_SIZE * grid_spawn_location[1]), (GRIDTILE_SIZE * 4, GRIDTILE_SIZE * 4))
        self.grid_coords = (self.rect.centerx // GRIDTILE_SIZE, self.rect.centery // GRIDTILE_SIZE)
        self.color = color
        self.ant_batch_size = 20
        self.all_ants = []


    def spawn_ant(self):
        if len(self.all_ants) >= 200:
            # print(f"Maximum number of ants reached ({len(self.all_ants)}).")
            return
        # print("Spawning ant...")

        for i in range(self.ant_batch_size):
            new_ant = Ant(spawn_loaction=self.rect.center, colony=self)
            self.all_ants.append(new_ant)
        # print(f"Total ants: {len(self.all_ants)}")


    def display(self, screen: pygame.Surface):
        self.surface = pygame.Surface(size=(self.rect.width, self.rect.height))
        self.surface.fill(color=self.color)

        text = f"{len(self.all_ants)}"
        font = pygame.font.Font(size=20)
        font_surface = font.render(text, False, "black")
        self.surface.blit(font_surface, dest=(5, 5))

        screen.blit(self.surface, dest=self.rect.topleft)


    def drop_feromone(self, grid, current_frame):
        # drop in frame 1
        if not grid["home"].get(self.grid_coords, None):
            new_feromone = Feromone(spawn_location=self.rect.center, feromone_type="home", frame_spawned=1, step=-1)
            grid["home"][self.grid_coords] = new_feromone

        else:
            grid["home"][self.grid_coords].refresh(current_frame)


class Feromone:

    def __init__(self, spawn_location, feromone_type, frame_spawned, step) -> None:
        self.spawn_location = spawn_location
        self.grid_location = (spawn_location[0] // GRIDTILE_SIZE, spawn_location[1] // GRIDTILE_SIZE)
        self.step = step
        self.feromone_type = feromone_type
        self.frame_spawned = frame_spawned
        self.rect = pygame.Rect(self.spawn_location, (GRIDTILE_SIZE, GRIDTILE_SIZE))
        self.surface = pygame.Surface(size=(self.rect.width//2, self.rect.height//2))
        self.multi = 2
        self.lifespan = 255 * self.multi
        self.alpha = 255

        if self.feromone_type == "food":
            self.color = pygame.Color(75, 255, 130, 255)
        elif self.feromone_type == "home":
            self.color = pygame.Color(255, 255, 255, 255)



    def display(self, screen: pygame.Surface):
        self.surface.fill(color=self.color)
        self.surface.set_alpha(self.alpha)
        # print(self.color.a)
        dest = (self.spawn_location[0] + self.rect.width//4, self.spawn_location[1] + self.rect.height//4)
        screen.blit(self.surface, dest=dest)


    def evaporate(self, current_frame) -> bool:
        life = current_frame - self.frame_spawned
        if life >= self.lifespan:
            return True

        self.color.g = 255 - life//self.multi
        self.alpha = 255 - life//self.multi

        #self.color.update(self.start_color.lerp(self.end_color, life/self.lifespan))

        
        return False
    

    def refresh(self, current_frame, step=None):
        self.frame_spawned = current_frame
        if step:
            self.step = step


class FoodSource:

    def __init__(self, spawn_location) -> None:
        self.spawn_location = spawn_location
        width = heigth = GRIDTILE_SIZE * 5
        self.rect = pygame.Rect(self.spawn_location, (width, heigth))
        self.grid_coords = (self.spawn_location[0] // GRIDTILE_SIZE, self.spawn_location[1] // GRIDTILE_SIZE)
        self.center_grid_coords = (self.rect.centerx // GRIDTILE_SIZE, self.rect.centery // GRIDTILE_SIZE)
        self.amount_remaining = 100
        self.surface = pygame.Surface(size=(self.rect.width, self.rect.height))

    
    def display(self, screen: pygame.Surface):
        self.surface.fill(color="green")

        text = f"{self.amount_remaining}"
        font = pygame.font.Font(size=20)
        font_surface = font.render(text, False, "black")
        self.surface.blit(font_surface, dest=(5, 5))

        screen.blit(self.surface, dest=self.spawn_location)

    def drop_feromone(self, grid, current_frame):
        
        # drop in frame 1
        if not grid["food"].get(self.center_grid_coords, None):
            # print(self.center_grid_coords, self.rect.center)
            new_feromone = Feromone(spawn_location=self.rect.center, feromone_type="food", frame_spawned=1, step=-1)
            grid["food"][self.center_grid_coords] = new_feromone

        else:
            #print(self.grid_coords)
            grid["food"][self.center_grid_coords].refresh(current_frame)


class Tile:
    def __init__(self, coords) -> None:
        
        self.coords = coords
        self.grid_x = coords[0]
        self.grid_y = coords[1]
        self.feromones = {
            "home": None,
            "food": None
        }

    


    












#### 
if __name__ == "__main__":
    main_loop()
import random
import pygame

# Initialization
pygame.font.init()
SCORE_FONT = pygame.font.SysFont('Arial', 36)
SMALL_FONT = pygame.font.SysFont('Arial', 30)
GAMEOVER_FONT = pygame.font.SysFont('Arial', 45, bold=True)

global_score = 0
game_over = False
pygame.init()
screen = pygame.display.set_mode((480, 720)) # modifie scrren resolution
clock = pygame.time.Clock()
running = True

# Colors (R, G, B, Alpha), add color here
WHITE = (255, 255, 255, 1)
GREEN = (0, 128, 0, 1)
RED = (255, 0, 0, 1)
BLUE = (0, 0, 255, 1)
YELLOW = (255, 255, 0, 1)
VOID = (0, 0, 0, 1)
COLORS = [WHITE, GREEN, RED, BLUE, YELLOW ] # you should add colors also in this array

TILE_SIZE = 30



## Creation Functions
def create_grid(width, height):
    """Creates a 2D list filled with the VOID color."""
    return [[VOID for _ in range(height)] for _ in range(width)]


def create_block(grid):
    """Generates a random vertical block of 1 to 3 colors."""
    while True:
        k = random.randint(1, 3)
        if is_grid_free(grid, k):
            break

    block_colors = [random.choice(COLORS) for _ in range(k)]
    free_columns = get_free_sections(grid, k)
    return block_colors, random.choice(free_columns), k


def draw_score(score):
    """Displays the current score on the screen."""
    text_surface = SCORE_FONT.render(f'Score: {score}', True, (255, 255, 255))
    screen.blit(text_surface, (60, 630))


def draw_grid(grid):
    """Renders the grid tiles to the pygame window."""
    width = len(grid)
    height = len(grid[0])
    for x in range(width):
        for y in range(height):
            # Calculate position from bottom to top
            rect = pygame.Rect(60 + (x * TILE_SIZE), 30 + ((height - 1 - y) * TILE_SIZE),
                               TILE_SIZE - 1, TILE_SIZE - 1)
            pygame.draw.rect(screen, grid[x][y], rect)


def is_grid_free(grid, k):
    """Checks if there is space at the top for a new block of size k."""
    width = len(grid)
    height = len(grid[0])
    for i in range(width):
        if grid[i][height - k: height] == [VOID] * k:
            return True
    return False


def get_free_sections(grid, k=1):
    """Returns a list of column indices that can fit a block of size k."""
    free_list = []
    width = len(grid)
    empty_space = [VOID] * k
    for i in range(width):
        if grid[i][-k:] == empty_space:
            free_list.append(i)
    return free_list


## Movement Functions
def move_block(grid, x, y, k, direction):
    """Moves the block horizontally if the space is free."""
    if not (0 <= x + direction < len(grid)):
        return grid, x
    if grid[x + direction][y: y + k] == [VOID] * k:
        grid[x][y: y + k], grid[x + direction][y: y + k] = grid[x + direction][y: y + k], grid[x][y: y + k]
        return grid, x + direction
    return grid, x


def drop_block(grid, x, y, k):
    """Moves the block down by one tile."""
    if y > 0 and grid[x][y - 1] == VOID:
        grid[x][y - 1: y + k - 1], grid[x][y + k - 1] = grid[x][y: y + k], grid[x][y - 1]
    return grid, y - 1


def fast_drop(grid, x, y, k):
    """Instantly drops the block to the lowest possible position."""
    block_colors = grid[x][y: y + k]
    for j in range(y, y + k):
        grid[x][j] = VOID

    destination = y
    while destination > 0 and grid[x][destination - 1] == VOID:
        destination -= 1

    grid[x][destination: destination + k] = block_colors
    return grid


def swap_colors(grid, x, y, k):
    """Cycles the colors within the falling block."""
    if k > 1:
        grid[x][y: y + k - 1], grid[x][y + k - 1] = grid[x][y + 1: y + k], grid[x][y]
    return grid


## Scoring Logic
def detect_alignment(row):
    """Identifies sequences of 3+ identical colors in a list."""
    n = len(row)
    marking = [False] * n
    score = 0
    i = 0
    while i < n:
        if row[i] == VOID:
            i += 1
            continue
        j = i
        while j < n and row[j] == row[i]:
            j += 1

        length = j - i
        if length >= 3:
            score += (length - 2)
            for idx in range(i, j):
                marking[idx] = True
        i = j
    return marking, score


def check_line_score(grid, temp_grid, i, j, dx, dy):
    """Scans for alignments in a specific direction (horizontal, vertical, diagonal)."""
    width, height = len(grid), len(grid[0])
    line = []
    coords = []
    curr_i, curr_j = i, j

    while 0 <= curr_i < width and 0 <= curr_j < height:
        line.append(grid[curr_i][curr_j])
        coords.append((curr_i, curr_j))
        curr_i += dx
        curr_j += dy

    marking, points = detect_alignment(line)
    for k in range(len(marking)):
        if marking[k]:
            cx, cy = coords[k]
            temp_grid[cx][cy] = VOID
    return points


def clear_alignments(grid):
    """Scans the entire grid for all possible alignments."""
    width, height = len(grid), len(grid[0])
    temp_grid = [column[:] for column in grid]
    total_points = 0
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for i in range(width):
        for j in range(height):
            for dx, dy in directions:
                total_points += check_line_score(grid, temp_grid, i, j, dx, dy)
    return temp_grid, total_points


def settle_grid(grid):
    """Makes tiles fall down to fill VOID spaces after clearing alignments."""
    width, height = len(grid), len(grid[0])
    new_grid = []
    for x in range(width):
        column = [tile for tile in grid[x] if tile != VOID]
        column.extend([VOID] * (height - len(column)))
        new_grid.append(column)
    return new_grid


def calculate_score(grid):
    """Recursively clears alignments and settles the grid until no more matches exist."""
    total_score = 0
    processing = True
    while processing:
        new_grid, step_points = clear_alignments(grid)
        if step_points > 0:
            total_score += step_points
            grid[:] = settle_grid(new_grid)
        else:
            processing = False
    return total_score


# Main Game Loop
grid = create_grid(12, 19) # pick the value you want
current_total_score = 0

while running:
    if not game_over:
        # Check if a new block can be spawned
        free_cols = get_free_sections(grid, 1)
        if not free_cols:
            game_over = True
            continue

        block, x, k = create_block(grid)
        y = len(grid[0]) - k
        grid[x][y:] = block

        is_fixed = False
        while not is_fixed and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:  # Move Left
                        grid, x = move_block(grid, x, y, k, -1)
                    elif event.key == pygame.K_d:  # Move Right
                        grid, x = move_block(grid, x, y, k, 1)
                    elif event.key == pygame.K_SPACE:  # Cycle Colors
                        grid = swap_colors(grid, x, y, k)
                    elif event.key == pygame.K_s:  # Fast Drop
                        grid = fast_drop(grid, x, y, k)
                        is_fixed = True

            if not is_fixed:
                if y > 0 and grid[x][y - 1] == VOID:
                    grid, y = drop_block(grid, x, y, k)
                else:
                    is_fixed = True

            screen.fill(VOID)
            draw_grid(grid)
            draw_score(current_total_score)
            pygame.display.flip()
            clock.tick(10)

        current_total_score += calculate_score(grid)


    else:
        screen.fill((0, 0, 0))
        msg = GAMEOVER_FONT.render("GAME OVER", True, (255, 0, 0))
        final_score_txt = SMALL_FONT.render(f"Final Score: {current_total_score}", True, (255, 255, 255))
        restart_txt = SMALL_FONT.render("Press R to Restart", True, (200, 200, 200))
        screen.blit(msg, (60, 80))
        screen.blit(final_score_txt, (60, 150))
        screen.blit(restart_txt, (60, 200))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                grid = create_grid(12, 19)
                current_total_score = 0
                game_over = False

pygame.quit()

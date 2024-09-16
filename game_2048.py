# fichier: game_2048.py

import pygame
import sys
import random
import os

# Configuration du jeu
WIDTH, HEIGHT = 400, 500  # Augmentation de la hauteur pour afficher le score
GRID_SIZE = 4
TILE_SIZE = WIDTH // GRID_SIZE
MARGIN = 10
ANIMATION_SPEED = 10  # Ajustez pour ralentir ou accélérer l'animation
NEW_TILE_HIGHLIGHT_TIME = 5  # Durée pendant laquelle la nouvelle tuile est en surbrillance
COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46)
}
NEW_TILE_COLOR = (143, 122, 102)  # Couleur de surbrillance pour les nouvelles tuiles

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('2048')

font = pygame.font.Font(None, 60)
score_font = pygame.font.Font(None, 40)
clock = pygame.time.Clock()

def read_high_score():
    # Lire le plus haut score depuis un fichier, retourner 0 si le fichier n'existe pas
    if os.path.exists('high_score.txt'):
        with open('high_score.txt', 'r') as file:
            return int(file.read())
    return 0

def save_high_score(high_score):
    # Sauvegarder le plus haut score dans un fichier
    with open('high_score.txt', 'w') as file:
        file.write(str(high_score))

def init_grid():
    # Initialiser la grille avec deux tuiles aléatoires
    grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    add_random_tile(grid)
    add_random_tile(grid)
    return grid

def add_random_tile(grid):
    # Ajouter une tuile aléatoire (2 ou 4) sur une case vide de la grille
    empty_tiles = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid[r][c] == 0]
    if empty_tiles:
        r, c = random.choice(empty_tiles)
        grid[r][c] = 2 if random.random() < 0.9 else 4
        return r, c  # Retourner la position de la nouvelle tuile
    return None

def draw_grid(grid, score, high_score, new_tile_pos):
    # Afficher la grille, le score actuel et le plus haut score
    screen.fill((187, 173, 160))
    score_text = score_font.render(f'Score: {score}', True, (119, 110, 101))
    high_score_text = score_font.render(f'High Score: {high_score}', True, (119, 110, 101))
    screen.blit(score_text, (10, 410))
    screen.blit(high_score_text, (10, 450))

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            value = grid[r][c]
            if new_tile_pos == (r, c) and NEW_TILE_HIGHLIGHT_TIME > 0:
                color = NEW_TILE_COLOR
            else:
                color = COLORS.get(value, (60, 58, 50))
            rect = pygame.Rect(c * TILE_SIZE + MARGIN, r * TILE_SIZE + MARGIN, TILE_SIZE - 2 * MARGIN, TILE_SIZE - 2 * MARGIN)
            pygame.draw.rect(screen, color, rect)
            if value != 0:
                text = font.render(str(value), True, (119, 110, 101))
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
    pygame.display.flip()

def slide_left(row):
    # Faire glisser les tuiles vers la gauche
    new_row = [i for i in row if i != 0]
    new_row += [0] * (GRID_SIZE - len(new_row))
    return new_row

def combine(row, score):
    # Combiner les tuiles adjacentes identiques et mettre à jour le score
    combined = []
    for i in range(GRID_SIZE - 1):
        if row[i] != 0 and row[i] == row[i + 1]:
            row[i] *= 2
            score += row[i]  # Mise à jour du score
            row[i + 1] = 0
            combined.append((i, i + 1))  # Track the merge for animation
    return row, score, combined

def move_left(grid, score):
    # Effectuer un mouvement vers la gauche sur toute la grille
    moved = False
    new_grid = []
    combined_positions = []  # Track combined positions for animation
    for row in grid:
        new_row = slide_left(row)
        combined_row, score, combined = combine(new_row, score)
        combined_positions.extend(combined)  # Collect combine information
        final_row = slide_left(combined_row)
        if row != final_row:
            moved = True
        new_grid.append(final_row)
    return new_grid, moved, score, combined_positions

def rotate_grid(grid):
    # Faire pivoter la grille dans le sens horaire
    return [list(row) for row in zip(*grid[::-1])]

def calculate_animation_positions(old_grid, new_grid, combined_positions):
    # Calculer les positions de départ et d'arrivée pour chaque tuile
    positions = {}
    merged = {}  # Track merged tiles

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            value = old_grid[r][c]
            if value != 0:
                # Find where this tile is in the new grid
                found = False
                for new_r in range(GRID_SIZE):
                    for new_c in range(GRID_SIZE):
                        if new_grid[new_r][new_c] == value and (new_r, new_c) not in positions.values():
                            positions[(r, c)] = (new_r, new_c)
                            found = True
                            break
                    if found:
                        break

    # Track merging tiles
    for start, end in combined_positions:
        for r in range(GRID_SIZE):
            if old_grid[r][start] != 0 and old_grid[r][start] == old_grid[r][end]:
                merged[(r, start)] = (r, end)
                merged[(r, end)] = (r, end)  # Both merge into the same tile

    return positions, merged

def animate_move(old_grid, new_grid, combined_positions):
    # Utiliser calculate_animation_positions pour garantir un mappage correct de l'animation
    positions, merged = calculate_animation_positions(old_grid, new_grid, combined_positions)
    frames = TILE_SIZE // ANIMATION_SPEED

    for i in range(frames + 1):  # Inclure la dernière frame où i = frames
        screen.fill((187, 173, 160))
        for (start_pos, end_pos) in positions.items():
            r, c = start_pos
            new_r, new_c = end_pos
            value = old_grid[r][c]
            if value == 0:
                continue
            color = COLORS.get(value, (60, 58, 50))

            # Calculate interpolated position
            x = c * TILE_SIZE + MARGIN + (new_c - c) * (i * ANIMATION_SPEED // frames)
            y = r * TILE_SIZE + MARGIN + (new_r - r) * (i * ANIMATION_SPEED // frames)

            rect = pygame.Rect(x, y, TILE_SIZE - 2 * MARGIN, TILE_SIZE - 2 * MARGIN)
            pygame.draw.rect(screen, color, rect)
            text = font.render(str(value), True, (119, 110, 101))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

        # Animate merging tiles
        for (start_pos, merge_pos) in merged.items():
            r, c = start_pos
            merge_r, merge_c = merge_pos
            value = old_grid[r][c] * 2 if start_pos in merged else old_grid[r][c]  # Show value doubling at merge
            color = COLORS.get(value, (60, 58, 50))

            # Interpolate merging tiles towards merge position
            x = c * TILE_SIZE + MARGIN + (merge_c - c) * (i * ANIMATION_SPEED // frames)
            y = r * TILE_SIZE + MARGIN + (merge_r - r) * (i * ANIMATION_SPEED // frames)

            rect = pygame.Rect(x, y, TILE_SIZE - 2 * MARGIN, TILE_SIZE - 2 * MARGIN)
            pygame.draw.rect(screen, color, rect)
            text = font.render(str(value), True, (119, 110, 101))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60)

def move(grid, direction, score):
    old_grid = [row[:] for row in grid]  # Copie de la grille avant le déplacement
    combined_positions = []

    if direction == 'LEFT':
        new_grid, moved, score, combined_positions = move_left(grid, score)
    elif direction == 'RIGHT':
        rotated_grid = rotate_grid(rotate_grid(grid))
        new_grid, moved, score, combined_positions = move_left(rotated_grid, score)
        new_grid = rotate_grid(rotate_grid(new_grid))
    elif direction == 'UP':
        rotated_grid = rotate_grid(rotate_grid(rotate_grid(grid)))
        new_grid, moved, score, combined_positions = move_left(rotated_grid, score)
        new_grid = rotate_grid(new_grid)
    elif direction == 'DOWN':
        rotated_grid = rotate_grid(grid)
        new_grid, moved, score, combined_positions = move_left(rotated_grid, score)
        new_grid = rotate_grid(rotate_grid(rotate_grid(new_grid)))

    if moved:
        animate_move(old_grid, new_grid, combined_positions)  # Appel de l'animation avec la correction
    return new_grid, moved, score

def check_game_over(grid):
    # Vérifier si le jeu est terminé (aucun mouvement possible)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == 0:
                return False
            if c < GRID_SIZE - 1 and grid[r][c] == grid[r][c + 1]:
                return False
            if r < GRID_SIZE - 1 and grid[r][c] == grid[r + 1][c]:
                return False
    return True

def display_game_over(score, high_score, new_record):
    # Afficher l'écran de fin de partie avec le score, le plus haut score et un message de félicitations si un nouveau record est établi
    screen.fill((187, 173, 160))
    game_over_text = font.render('Game Over!', True, (119, 110, 101))
    score_text = score_font.render(f'Score: {score}', True, (119, 110, 101))
    high_score_text = score_font.render(f'High Score: {high_score}', True, (119, 110, 101))
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 50))

    if new_record:
        # Affichage des messages de félicitations sur deux lignes
        congrats_text_line1 = score_font.render('New High Score!', True, (255, 215, 0))
        congrats_text_line2 = score_font.render('Congratulations!', True, (255, 215, 0))
        screen.blit(congrats_text_line1, (WIDTH // 2 - congrats_text_line1.get_width() // 2, HEIGHT // 2 + 100))
        screen.blit(congrats_text_line2, (WIDTH // 2 - congrats_text_line2.get_width() // 2, HEIGHT // 2 + 140))

    pygame.display.flip()

    # Attendre que l'utilisateur appuie sur une touche pour redémarrer
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

def main():
    while True:
        grid = init_grid()  # Initialisation de la grille
        score = 0  # Initialisation du score
        high_score = read_high_score()  # Lecture du plus haut score
        new_tile_pos = None  # Position de la nouvelle tuile
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_high_score(high_score)  # Sauvegarde du plus haut score avant de quitter
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    moved = False
                    if event.key == pygame.K_LEFT:
                        grid, moved, score = move(grid, 'LEFT', score)
                    if event.key == pygame.K_RIGHT:
                        grid, moved, score = move(grid, 'RIGHT', score)
                    if event.key == pygame.K_UP:
                        grid, moved, score = move(grid, 'UP', score)
                    if event.key == pygame.K_DOWN:
                        grid, moved, score = move(grid, 'DOWN', score)
                    if moved:
                        new_tile_pos = add_random_tile(grid)  # Stocker la position de la nouvelle tuile
                    if check_game_over(grid):
                        new_record = False
                        if score > high_score:
                            high_score = score
                            save_high_score(high_score)  # Mise à jour du plus haut score
                            new_record = True
                        display_game_over(score, high_score, new_record)  # Affichage du score et du plus haut score
                        grid = init_grid()  # Réinitialisation de la grille
                        score = 0  # Réinitialisation du score
                        new_tile_pos = None  # Réinitialisation de la nouvelle tuile
                        break  # Sortir de la boucle pour redémarrer le jeu

            draw_grid(grid, score, high_score, new_tile_pos)
            clock.tick(60)

if __name__ == "__main__":
    main()

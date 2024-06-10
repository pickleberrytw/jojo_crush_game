import pygame
import sys
import random

# 初始化Pygame
pygame.init()

# 初始化Pygame混音器
pygame.mixer.init()

# 加载音效文件并进行错误处理
sound_files = ['sound1.wav', 'sound2.wav', 'sound3.wav', 'sound4.wav', 'sound5.wav']
sounds = []

for sound_file in sound_files:
    try:
        sound = pygame.mixer.Sound(sound_file)
        sounds.append(sound)
    except pygame.error as e:
        print(f"Failed to load sound {sound_file}: {e}")
        sys.exit(1)

# 设置游戏窗口的大小
screen_width, screen_height = 635, 680  # 窗口高度增加60像素以容纳记分板
scoreboard_height = 60
game_area_height = screen_height - scoreboard_height
screen = pygame.display.set_mode((screen_width, screen_height))

# 设置窗口标题
pygame.display.set_caption('Candy Crush')

# 加载图片
candy_images = [
    pygame.image.load('candy1.png'),
    pygame.image.load('candy2.png'),
    pygame.image.load('candy3.png'),
    pygame.image.load('candy4.png'),
    pygame.image.load('candy5.png')
]

# 加载记分板图片
score_icon = pygame.image.load('score_icon.png')

# 加載restart按鈕圖片
restart_button_image = pygame.image.load('restart.png')
restart_button_rect = restart_button_image.get_rect(topleft=(screen_width - 100, 10))

# 游戏板参数
board_size = 9
tile_size = 60
padding = 5  # 图片之间的空格
margin = 15  # 游戏区外框留白
gravity_speed = 1.2  # 重力速度，每帧移动的像素数
animation_speed = 8  # 动画速度参数
match_animation_speed = 0.8  # 连续消除的动画速度
glow_effect_duration = 100  # 閃光特效時間

class Tile:
    def __init__(self, image, row, col):
        self.image = image
        self.row = row
        self.col = col
        self.target_y = row * (tile_size + padding) + margin + padding + scoreboard_height
        self.current_y = self.target_y

def initialize_board():
    while True:
        board = [[Tile(random.choice(candy_images), row, col) for col in range(board_size)] for row in range(board_size)]
        if not has_initial_matches(board):
            return board

def has_initial_matches(board):
    for row in range(board_size):
        for col in range(board_size):
            if check_match(board, row, col):
                return True
    return False

def check_match(board, row, col):
    if row >= 2 and board[row][col].image == board[row-1][col].image == board[row-2][col].image:
        return True
    if col >= 2 and board[row][col].image == board[row][col-1].image == board[row][col-2].image:
        return True
    return False

tiles = initialize_board()

selected_tile = None
score = 0
move_count = 15
game_over = False
swapping = False
swap_step = 0
swap_tile1 = None
swap_tile2 = None
removing = False
remove_step = 0
remove_matches_list = []
falling_tiles = []
glow_effect_step = 0

def draw_board(screen, tiles):
    for row in range(board_size):
        for col in range(board_size):
            tile = tiles[row][col]
            if tile.image is not None:
                x = col * (tile_size + padding) + margin + padding
                screen.blit(tile.image, (x, tile.current_y))
            pygame.draw.rect(screen, (0, 0, 0, 128), (x - padding // 2, tile.current_y - padding // 2, tile_size + padding, tile_size + padding), 1)

def draw_scoreboard(screen):
    screen.blit(score_icon, (10, 10))  # 在左上角显示记分板图片
    font = pygame.font.Font(None, 36)
    text = font.render(f'Score: {score}', True, (0, 0, 0))
    screen.blit(text, (10 + score_icon.get_width() + 10, 10))  # 调整文本位置以便与图片对齐
    moves_text = font.render(f'Moves: {move_count}', True, (0, 0, 0))
    screen.blit(moves_text, (10 + score_icon.get_width() + 10, 40))  # 調整文本位置
    screen.blit(restart_button_image, restart_button_rect)

def get_tile_at_pos(pos):
    x, y = pos
    y -= scoreboard_height + margin + padding  # 调整鼠标位置来匹配板块位置
    x -= margin + padding
    if y < 0 or x < 0:
        return None
    row = y // (tile_size + padding)
    col = x // (tile_size + padding)
    if row < board_size and col < board_size:
        return row, col
    return None

def swap_tiles(tile1, tile2):
    tile1.image, tile2.image = tile2.image, tile1.image

def find_matches(tiles):
    matches = set()
    for row in range(board_size):
        for col in range(board_size):
            tile = tiles[row][col]
            if tile.image is None:
                continue

            # Check horizontally
            match_list = [(row, col)]
            for i in range(col + 1, board_size):
                if tiles[row][i].image == tile.image:
                    match_list.append((row, i))
                else:
                    break
            for i in range(col - 1, -1, -1):
                if tiles[row][i].image == tile.image:
                    match_list.append((row, i))
                else:
                    break
            if len(match_list) >= 3:
                matches.update(match_list)

            # Check vertically
            match_list = [(row, col)]
            for i in range(row + 1, board_size):
                if tiles[i][col].image == tile.image:
                    match_list.append((i, col))
                else:
                    break
            for i in range(row - 1, -1, -1):
                if tiles[i][col].image == tile.image:
                    match_list.append((i, col))
                else:
                    break
            if len(match_list) >= 3:
                matches.update(match_list)

    return list(matches)

def remove_matches(tiles, matches):
    global score
    for (row, col) in matches:
        tiles[row][col].image = None
    score += len(matches)

def drop_tiles(tiles):
    global falling_tiles
    falling_tiles = []
    for col in range(board_size):
        empty_row = board_size - 1
        for row in range(board_size - 1, -1, -1):
            if tiles[row][col].image is not None:
                if empty_row != row:
                    tiles[empty_row][col].image = tiles[row][col].image
                    tiles[row][col].image = None
                    tiles[empty_row][col].target_y = empty_row * (tile_size + padding) + margin + padding + scoreboard_height
                    falling_tiles.append(tiles[empty_row][col])
                empty_row -= 1

def fill_empty_tiles(tiles):
    for row in range(board_size):
        for col in range(board_size):
            if tiles[row][col].image is None:
                tiles[row][col].image = random.choice(candy_images)
                tiles[row][col].current_y = - (tile_size + padding)  # Start above the board
                tiles[row][col].target_y = row * (tile_size + padding) + margin + padding + scoreboard_height
                falling_tiles.append(tiles[row][col])

def is_adjacent(tile1, tile2):
    return (abs(tile1.row - tile2.row) == 1 and tile1.col == tile2.col) or (abs(tile1.col - tile2.col) == 1 and tile1.row == tile2.row)

def animate_swap(tile1, tile2, progress):
    x1, y1 = tile1.col * (tile_size + padding) + margin + padding, tile1.row * (tile_size + padding) + margin + padding + scoreboard_height
    x2, y2 = tile2.col * (tile_size + padding) + margin + padding, tile2.row * (tile_size + padding) + margin + padding + scoreboard_height

    x1 += (x2 - x1) * progress
    y1 += (y2 - y1) * progress
    x2 += (x1 - x2) * progress
    y2 += (y1 - y2) * progress

    screen.blit(tile1.image, (x1, y1))
    screen.blit(tile2.image, (x2, y2))

def draw_glow_effect(screen, tile):
    x = tile.col * (tile_size + padding) + margin + padding
    y = tile.row * (tile_size + padding) + margin + padding + scoreboard_height
    glow_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    pygame.draw.rect(glow_surface, (255, 255, 0, 128), glow_surface.get_rect(), border_radius=10)
    screen.blit(glow_surface, (x, y))

def restart_game():
    global tiles, score, move_count, game_over
    tiles = initialize_board()
    score = 0
    move_count = 15
    game_over = False

def check_and_remove_matches():
    global removing, remove_matches_list, glow_effect_step
    matches = find_matches(tiles)
    if matches:
        # 播放对应音效
        for row, col in matches:
            for i, img in enumerate(candy_images):
                if tiles[row][col].image == img:
                    sounds[i].play()
                    break
        remove_matches_list = matches
        removing = True
        remove_step = 0
        glow_effect_step = 0
        return True
    return False

def handle_gravity():
    global removing, remove_step, remove_matches_list, glow_effect_step
    if falling_tiles:
        screen.fill((255, 255, 255))
        draw_board(screen, tiles)
        draw_scoreboard(screen)  # 添加重新繪製計分板
        for tile in falling_tiles:
            if tile.current_y < tile.target_y:
                tile.current_y += gravity_speed
                if tile.current_y > tile.target_y:
                    tile.current_y = tile.target_y
        falling_tiles[:] = [tile for tile in falling_tiles if tile.current_y < tile.target_y]
        pygame.display.flip()
        if not falling_tiles:
            if check_and_remove_matches():
                removing = True
                remove_step = 0
                glow_effect_step = 0
            else:
                removing = False

def animate_removal():
    global remove_step, glow_effect_step, removing
    remove_step += 1
    glow_effect_step += 1
    screen.fill((255, 255, 255))
    draw_board(screen, tiles)
    draw_scoreboard(screen)  # 添加重新繪製計分板
    for row, col in remove_matches_list:
        draw_glow_effect(screen, tiles[row][col])
    pygame.display.flip()
    if remove_step >= glow_effect_duration:  # 使用 glow_effect_duration 來控制閃光特效時間
        remove_matches(tiles, remove_matches_list)
        drop_tiles(tiles)
        fill_empty_tiles(tiles)
        removing = False

# 修改游戏主循环来处理匹配
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if game_over:
                if restart_button_rect.collidepoint(pos):
                    restart_game()
            else:
                if restart_button_rect.collidepoint(pos):
                    restart_game()
                else:
                    tile_pos = get_tile_at_pos(pos)
                    if tile_pos:
                        selected_tile = tiles[tile_pos[0]][tile_pos[1]]
        elif event.type == pygame.MOUSEMOTION and selected_tile and not swapping and not removing and not game_over:
            pos = pygame.mouse.get_pos()
            tile_pos = get_tile_at_pos(pos)
            if tile_pos:
                target_tile = tiles[tile_pos[0]][tile_pos[1]]
                if target_tile != selected_tile and is_adjacent(selected_tile, target_tile):
                    swap_tile1 = selected_tile
                    swap_tile2 = target_tile
                    swapping = True
                    swap_step = 0
                    selected_tile = None
                    move_count -= 1
                    if move_count <= 0:
                        game_over = True
        elif event.type == pygame.MOUSEBUTTONUP:
            selected_tile = None

    if swapping:
        swap_step += 1
        progress = swap_step / (10 * animation_speed)
        screen.fill((255, 255, 255))
        draw_board(screen, tiles)
        draw_scoreboard(screen)  # 添加重新繪製計分板
        animate_swap(swap_tile1, swap_tile2, progress)
        pygame.display.flip()
        if swap_step >= 10 * animation_speed:
            swap_tiles(swap_tile1, swap_tile2)
            if not check_and_remove_matches():
                swap_tiles(swap_tile1, swap_tile2)  # Swap back if no match
            swapping = False

    if removing:
        animate_removal()

    handle_gravity()

    if not swapping and not removing and not falling_tiles:
        # 填充窗口背景
        screen.fill((255, 255, 255))

        # 绘制游戏板
        draw_board(screen, tiles)
        draw_scoreboard(screen)  # 添加重新繪製計分板

        if game_over:
            font = pygame.font.Font(None, 48)
            game_over_text = font.render('Game Over', True, (255, 0, 0))
            screen.blit(game_over_text, (screen_width // 2 - game_over_text.get宽度 // 2, screen_height // 2))

    # 更新显示
    pygame.display.flip()

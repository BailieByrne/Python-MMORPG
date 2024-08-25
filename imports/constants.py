import ctypes
user32 = ctypes.windll.user32
IP_ADDRESS = "192.168.0.117"
PORT = 60002
assetpath = "assets/"
mappath = "maps/"
configpath = "config/"
g = 9.81

screen_width = int(user32.GetSystemMetrics(0))
screen_height = int(user32.GetSystemMetrics(1))

menu_width = screen_width
menu_height = screen_height
menu_x = (screen_width - menu_width) // 2
menu_y = (screen_height - menu_height) // 2

equipped_x = menu_x + menu_width - 50
equipped_y = (menu_y + menu_height) // 2 - (40) * 2
equipped_size = 30
equipped_spacing = 10



PLAYER_INVENTORY_POS = (20, 60)
CONTAINER_INVENTORY_POS = (screen_width // 2 + 20, 60)  # Adjusted position for the right side
TAB_WIDTH = 130
TAB_HEIGHT = 30
FONT_SIZE = 20
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
DARK_GRAY = (50, 50, 50)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
RED = (255,0,0)
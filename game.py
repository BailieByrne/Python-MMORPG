#Imports neccesary librarys
import pygame
import pygame.sprite
import pytmx
import csv
import sys
import random
import socket
import threading,json
import time
from pygame import mixer
import ctypes
import math
from imports import constants   #imports constants from a fiel to be used
from imports import items #imports a list of existing items to gather infor and values
user32 = ctypes.windll.user32
pygame.init()

#Tests if the device has suitable audio output if not ignores and continues
try:
    mixer.init()
except:
    pass

hostname = socket.gethostname()
client_address = socket.gethostbyname(hostname)
client_address = '192.168.0.117'
COUNTER = 0
fpressed = False
font = pygame.font.SysFont(None, 20)
screen_width = int(user32.GetSystemMetrics(0))
screen_height = int(user32.GetSystemMetrics(1))
screen = pygame.display.set_mode((screen_width, screen_height))

#PACKETS FOR THE CLIENT TO SEND TO THE SERVER
DATA = {"IP": client_address,"X": "0", "Y": "0","HP": "0","RECTX" : "0", "RECTY": "0", "Map": "None", "COMMAND": "GENERAL"}
PING = {"IP": client_address, "COMMAND": "PING"}
INIT = {"COMMAND":"INITINV"}
ENEMYHIT = {"COMMAND":"EH","ID":"-1","DMG":"0"}
CONT = {"COMMAND":"OC","ID":""}
TOCONT = {"COMMAND":"TC","TAB":"Weapons","ID":"0","Item":"Gun","A":"1"}
FROMCONT = {"COMMAND":"FC","TAB":"Weapons","ID":"0","Item":"Gun","A":"1"}
QUESTUPDATE = {"COMMAND":"QU","ID":"","VALUE":""}
RMV = {"COMMAND":"RMV","AMMO":0,"AMOUNT":""}
ULK = {"COMMAND":"ULK","ID":0}

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #CREATE A SOCKET WITH THE SERVER
s.connect((constants.IP_ADDRESS,constants.PORT)) #CONNECT TO SAID SOCKET USING A PORT DEFINED IN CONSTANTS

map_dict = {"0":("pygame.tmx","test_PATHING.csv"),
            "1":("map2.tmx","map2_PATHING.csv")} #HERE A DICTIONARY IS USED TO STORE MAPS AS WELL AS THEIR CORRESPONDING PATHINF FILES, INDEXED WITH AN ID

player = None #Create a blank variable called player to allow player to referenced by functions as python does not support hoisting
clock = pygame.time.Clock() #Sets up the pygame clock to allow a framerate
clock.tick(60) #Sets that framerate to 60

camera_x = 0
camera_y = 0

sprite_ids = [] #Initializes a list to store otherplayers sprites
otherplayers = pygame.sprite.Group() #Pygame group to store instances of other players
enemies = [] #Initializes a list for enemy IDS
enemysprites = pygame.sprite.Group() #Pygame group to store enemy instances
projectiles = pygame.sprite.Group() #Pygame group to store projectile instances
NPCS = pygame.sprite.Group() #Pygame group to store NPC instances
lockedcontainers = []

container_inv = {
    "Weapons": {},
    "Armor": {},
    "Ammo": {},
    "Consumables":{},
    "Misc": {}
}# Template for container inventory to be referenced as a work around for hoisting once again

interrupt = False
class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.running = True  # Control whether the menu is active
        # Define initial menu properties
        self.text_lines = ["Welcome to Wild Wasteland",
                           "Essentially Your Goal Is To Explore The Wasteland And Find A Way To Safety", "",
                           "KeyBinds:", "ESC: Close Menus", "LMB: Attack", "E: Interact", "Tab: Open Inventory",
                           "WASD / Arrow Keys: Movement In Corresponding Direction",
                           "F : Use Equipped Offhand Item", "F1: Open This Menu", "", "", "Tips:",
                           "Search Containers For Useful Items Like Weapons And Armor",
                           "Equip Said Items For Damage And Armor Buffs", "Use Ammo Sparingly", "Stock Up On Meds",
                           "Speak To The Locals "]
        self.button_text = "Close"  # Text for the button
        self.x = 100
        self.line_height = 30
        self.button_height = 50  # Height of the button
        self.text_color = (255, 255, 255)
        self.block_color = (128, 128, 128)

        self.font = pygame.font.Font(None, 36)
        self.width = max(self.font.size(line)[0] for line in self.text_lines)
        self.height = len(self.text_lines) * self.line_height + self.button_height

        self.block = pygame.Surface((self.width, self.height))
        self.block.fill(self.block_color)

        # Position the button at the center bottom
        self.button_x = (constants.screen_width - self.width) // 2
        self.button_y = constants.screen_height - self.button_height

    def draw(self):
        y_offset = self.x
        for line in self.text_lines:
            text_surface = self.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(topleft=(self.x, y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += self.line_height

        # Create the button at the center bottom
        button_surface = pygame.Surface((self.width, self.button_height))
        button_surface.fill((255, 0, 0))  # Red button background
        button_text_surface = self.font.render(self.button_text, True, self.text_color)
        button_text_rect = button_text_surface.get_rect(center=(self.width / 2, self.button_height / 2))
        self.screen.blit(button_surface, (self.button_x, self.button_y))
        self.screen.blit(button_text_surface, (self.button_x + (self.width - button_text_rect.width) / 2, self.button_y + (self.button_height - button_text_rect.height) / 2))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if the mouse click is within the button's area
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(self.button_x, self.button_y, self.width, self.button_height)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.running = False

            self.screen.fill((0, 0, 0))  # Clear the screen
            self.draw()
            pygame.display.flip()
class DeathMenu(Menu):
    def __init__(self, screen, killer):
        super().__init__(screen)
        self.killer = killer
        self.button_text = "Close"
        self.message = f"You were killed by {self.killer}"
        self.message_font = pygame.font.Font(None, 48)  # You can adjust the font size

    def draw(self):
        self.text_lines = []
        super().draw()  # Call the parent class's draw method

        # Draw the "You were killed by (killer)" message
        message_surface = self.message_font.render(self.message, True, self.text_color)
        message_rect = message_surface.get_rect(center=(self.width / 2, self.height / 2))
        self.screen.blit(message_surface, message_rect)

    def run(self):
        start_time = pygame.time.get_ticks()  # Get the current time
        while self.running:
            current_time = pygame.time.get_ticks()
            if current_time - start_time >= 3000:  # Check if 3 seconds have passed
                self.running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.screen.fill((0, 0, 0))  # Clear the screen
            self.draw()
            pygame.display.flip()
class OTHERPLAYER(pygame.sprite.Sprite):
    def __init__(self, sid, x, y,img):
        """
        :param sid:
        :param x:
        :param y:
        :param img:
        """
        super().__init__()
        self.x = x
        self.y = y
        self.sid = sid
        self.rect = pygame.Rect(self.x, self.y, 32, 32) # Define a rect to draw the image to
        self.image = img
        self.image = pygame.image.load(constants.assetpath +self.image) #Image for other player

    def update(self,x,y): #Draws the otherplayers to the map surface
        """
        :param x:
        :param y:
        :return:
        """
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, 32, 32)
        otherplayers.draw(map.map_surface)

otherplayers.add(OTHERPLAYER(-1,-1,-1,"R.png"))
#Create a reference of the other players instance to allow iteration through the sprite group to draw them
class Map:
    def __init__(self, tmx_file, path_file=None):
        '''
        Here is the map class this stores all the map related data such as objects to collide with, intercatables
        The map class also converts the csv into a matrice for pathfinding and tmx file grids
        :param tmx_file:
        :param path_file:
        '''
        self.tmx_file = constants.mappath + tmx_file
        self.path_file = constants.mappath + path_file
        self.tmx_data = pytmx.load_pygame(self.tmx_file, pixelalpha=True)
        self.obstacles = get_object_rects(self.tmx_file)
        self.interactables = get_interactable_rects(self.tmx_file)
        self.map_width = self.tmx_data.width * self.tmx_data.tilewidth
        self.map_height = self.tmx_data.height * self.tmx_data.tileheight
        self.map_surface = pygame.Surface((self.map_width, self.map_height))
        self.map_id = None
        self.path_data = []
        self.collision_boxes = []

        # load path data from csv file if provided, otherwise from tmx file
        if path_file:
            with open(constants.mappath+ path_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.path_data.append(row)

        else:
            for layer in self.tmx_data.layers:
                if layer.name == 'PATHING':
                    self.path_data = layer.data

    #Currently unused function but allows to check for the value of the current tile the player is on for interactable events like enemy spawning
    def get_tile_value(self, x, y):
        row = self.path_data[y]
        tile_value = row[x]
        return tile_value

    #The change map fucntion is called whenever the player chnages map and upates the Map ID and hence forth updates all the new collisions and interactables on that layer of the map specifically.
    def changemap(self,id):
        global map_id
        self.map_width = self.tmx_data.width * self.tmx_data.tilewidth
        self.map_height = self.tmx_data.height * self.tmx_data.tileheight
        self.map_surface = pygame.Surface((self.map_width, self.map_height))
        self.obstacles = get_object_rects(self.tmx_file)
        self.interactables = get_interactable_rects(self.tmx_file)
        self.map_id = id
        for npc in NPCS:
            npc.check_map_change(map_id)
#THE NPC class is very barebones and stores the Name of the NPC as well as its image and lcoation for it to be drawn to the map
#The npc consists of a two step interaction couple of events first it checks if its colliding with the player if so allows the interact fucntion to be called
#This function will check the NPCS name and if any quests related to that npc are available creates dialogue dependant on that quest.
class NPC(pygame.sprite.Sprite):
    def __init__(self, image_path, map_id, rect_x, rect_y,name):
        '''
        Initializes the NPC as a png image drawn in the rect
        :param image_path:
        :param map_id:
        :param rect_x:
        :param rect_y:
        :param name:
        '''
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.map_id = map_id
        self.rect = self.image.get_rect()
        self.rect.x = rect_x
        self.rect.y = rect_y
        self.name = name
        self.talking = False
        NPCS.add(self)

    def check_collision(self, player,keys):
        if str(self.map_id) == str(map.map_id):
            if self.rect.colliderect(player.rect):
                screentext.changetext("PRESS E TO SPEAK")
                if keys[pygame.K_e] or self.talking == True:
                    self.interact(player)
                    self.talking = True
            else:
                self.talking = False

    def interact(self,player):
        # Represents a conversation between the player and the NPC, its behavior varies by NPC's name, the player's current quests, and inventory.
        if self.name == "Tony":
            if any(element == (0,0) for element in player.quests):
                screentext.changetext("HI MY NAMES TONY CAN YOU FIND MY KEY?")
                if 'Key' in player.inventory['Misc']:
                    QUESTUPDATE["ID"] = "0"
                    QUESTUPDATE["VALUE"] = "1"
                    s.send((json.dumps(QUESTUPDATE) + "#").encode())
                    screentext.changetext("THANK YOU FOR FINDING MY KEY HAVE THIS")
                    player.inventory["Misc"]["Key"] -= 1
                    player.quests.remove((0,0))
                    self.talking = False
            else:
                screentext.changetext("I DONT NEED YOUR HELP RIGHT NOW")
        if self.name == "Shade":
            if any(element == (999, 0) for element in player.quests):
                if "Cap(s)" in player.inventory.get("Misc"):
                    if player.inventory["Misc"]["Cap(s)"] >= 10000:
                        screentext.changetext("Now Were Talking")
                        RMV["AMMO"] = "Cap(s)"
                        RMV["AMOUNT"] = 10000
                        s.send((json.dumps(RMV) + "#").encode())
                        player.inventory["Misc"]["Cap(s)"] -= 10000
                        QUESTUPDATE["ID"] = "999"
                        QUESTUPDATE["VALUE"] = "1"
                        s.send((json.dumps(QUESTUPDATE) + "#").encode())
                else:
                    screentext.changetext("Come Back When You Have Some Cash!")
            self.talking = False
        if self.name == "Wrangler":
            screentext.changetext("Thanks for saving my skin")
            if any(element == (1, 0) for element in player.quests):
                screentext.changetext("Would You Mind Finding Me A Machete")
            if any(element == (1, 0) for element in player.quests) and "Machete" in player.inventory['Weapons']:
                screentext.changetext("Hey I Was Just Looking For A Machete")
                QUESTUPDATE["ID"] = "1"
                QUESTUPDATE["VALUE"] = "1"
                s.send((json.dumps(QUESTUPDATE) + "#").encode())
                del player.inventory["Weapons"]["Machete"]
                screentext.changetext("Here Take This Old Tool I Had")
                self.talking = False







    #The check map change is a function that is called to check the current map
    #If the map is not the same as the npcs map id it is removed and killed to prevent NPCs spawning on the wrong map layer
    def check_map_change(self, map_id):
        if map_id != self.map_id:
            NPCS.remove(self)
            self.kill()
#Here is the player class this is the main instance the user controls when using the game
class Player(pygame.sprite.Sprite):
    global screentext
    global fpressed
    #Screen text is a global variable to allow instant reference to it dependant on the players actions

    def __init__(self, x, y, map):
        super().__init__()
        #ANIMATIONS//CONSTANTS used to create the Character
        self.name = "p"
        self.map = map
        self.x = x
        self.y = y
        self.max_hp = 100
        self.hp = 100
        self.speed = 5
        self.direction = "left"

        self.counter = 0 #Counter to identify which step of the animation loop the player is in
        self.walking_index = 0
        #Animations from PNG
        self.walkleft = [pygame.image.load(constants.assetpath+ "left4.png"),
                        pygame.image.load(constants.assetpath+"left2.png"),
                        pygame.image.load(constants.assetpath+"left3.png"),
                        pygame.image.load(constants.assetpath+"left.png")] #Dictionaries storing varous animation loops
        self.walkright = [pygame.image.load(constants.assetpath+"right4.png"),
                         pygame.image.load(constants.assetpath+"right2.png"),
                         pygame.image.load(constants.assetpath+"right3.png"),
                         pygame.image.load(constants.assetpath+"right.png")]
        self.dying = [pygame.image.load(constants.assetpath+"death_1.png"),
                      pygame.image.load(constants.assetpath+"death_2.png"),
                      pygame.image.load(constants.assetpath+"death_3.png")]
        self.image = self.walkleft[0]


        self.rect = pygame.Rect(self.x, self.y, 32, 64)
        self.lastdmgtype = "Gun" #This is the damage type which is displayed when you die telling you chat killed you
        self.lastshot = time.time()
        self.damage_reduc = 1
       #The equipped weapon type changes between guns and melee to indicate hwo the player should attack

        self.inventory = {
            "Weapons": {},
            "Armor": {},
            "Ammo": {},
            "Consumables": {},
            "Misc": {}
        } #Template for the players inventory
        self.equipped = {
            "H":{},
            "C": {},
            "F" :{},
            "Hand": {},
            "Offhand": {}
        }
        self.continv = {
            "Weapons": {},
            "Armor": {},
            "Ammo": {},
            "Consumables":{},
            "Misc": {}
        } # Template for conatiner inventory
        self.quests = set() # Set used to store quests to ensure only one instance of each quest exists
        self.contID = "" # The containerID currently being accessed
        self.equipped_images = {}
        self.lockedcontainers = []

        self.lastshotupdate = time.time()
        self.shots = 0
        self.lastammo = ''

    def statupdate(self):
        temparmor = 1
        for i in player.equipped:
            if i in ["H","C","F"]:
                try:
                    armor_data = items.Armor.get(player.equipped[i])
                    if armor_data:
                        temparmor += armor_data[2]  # Index 2 for the armor value
                except:
                    pass

        player.damage_reduc = temparmor

    def update(self, keys):
        global fpressed
        global camera_x
        global camera_y
        '''
        The main method of the player class the update function is a recursive function called in the main loop to allow
        movement as well as handling all of the keybinds, the update fucntion also is the main driver in collision handling
        it cross refernces the map Classes object list against th players rect to determine collision
        It also handles intercatable types such as doors or containers.
        :param keys:
        :return:
        '''
        self.enlarged_rect = self.rect.inflate(10, 10)
        global time_factor
        dx, dy = 0, 0

        if self.hp <= 0:
            #Script to handle death by cheking health and reverts to first map upon death
            print("You died to a ", self.lastdmgtype)
            self.x = 0
            self.y = 0
            changemaps("0")
            self.rect.x, self.rect.y = 0, 0
            self.hp = 100
            d = DeathMenu(screen, self.lastdmgtype)
            d.run()

        if pygame.mouse.get_pressed()[0]:
            #uses mouse position to get target location and creates an instance of a projectile
            # using the equipped item type and relevant ammo
            mouse_x, mouse_y = pygame.mouse.get_pos()


            if self.equipped["Hand"] != {}:
                weapondata = items.Weapons.get(self.equipped["Hand"])
                if time.time() - self.lastshot > weapondata[2]:
                    self.lastshot = time.time()
                    Projectile(self.equipped["Hand"],self,(mouse_x -camera_x, mouse_y-camera_y))


        if time.time() - self.lastshotupdate >= 2:
            if self.lastammo != '' and self.shots != 0:
                RMV["AMMO"] = self.lastammo
                RMV["AMOUNT"] = self.shots
                s.send((json.dumps(RMV) + "#").encode())
                self.shots = 0
                self.lastshotupdate = time.time()


        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
            self.direction = "up"
            self.counter += 1

        if keys[pygame.K_TAB]:
            inventory_menu = InventoryMenu(constants.screen_width, constants.screen_height, self)
            inventory_menu.show_inventory_menu() #INVENTORY

        if keys[pygame.K_SPACE]:
            self.rect.x = 0
            self.rect.y = 0

        if keys[pygame.K_F1]:
            menu = Menu(screen)
            menu.run()

        if keys[pygame.K_f] and not fpressed:
            fpressed = True
            if self.equipped["Offhand"] != {}:
                consumabledata = items.Consumables.get(self.equipped["Offhand"])
                if consumabledata[1] == "HEAL":
                    player.hp += consumabledata[2]
                    if player.hp > 100:
                        player.hp = 100
                self.inventory["Consumables"][self.equipped["Offhand"]] -= 1
                RMV["AMMO"] = self.equipped["Offhand"]
                RMV["AMOUNT"] = 1
                s.send((json.dumps(RMV) + "#").encode())
                if self.inventory["Consumables"][self.equipped["Offhand"]] <= 0:
                    del self.inventory["Consumables"][self.equipped["Offhand"]]
                    self.equipped["Offhand"] = {}
                    with open("equipped_items.json", "r") as json_file:
                        equipped_data = json.load(json_file)
                        equipped_data["Offhand"] = ""
                    with open("equipped_items.json", "w") as json_file:
                        json.dump(equipped_data, json_file)

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            self.direction = "down"
            self.counter += 1

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self.direction = "left"
            self.counter += 1

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.direction = "right"
            self.direction = "right"
            self.counter += 1

        if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d] or keys[pygame.K_w]:
            if self.counter >= 10:
                self.walking_index = (self.walking_index + 1) % len(self.walkleft)
                self.counter = 0

        #Manages hovering over the player to display their health bar
        mouse_x , mouse_y = pygame.mouse.get_pos()
        if self.rect.collidepoint(((mouse_x - camera_x),(mouse_y-camera_y))):
            self.draw_overhead_health_bar(map.map_surface)
        # Check for collisions with obstacles
        next_rect = self.rect.move(dx, dy)
        for obstacle in map.obstacles:
            if obstacle.colliderect(next_rect):
                return

        #manages intercatbles
        for inter in map.interactables:
            if self.enlarged_rect.colliderect(inter[1]):
                if inter[0] == 'cont':
                    screentext.changetext("PRESS E TO OPEN")
                    if keys[pygame.K_e]:
                        self.contID = inter[2]
                        openCont(inter[2])
                elif inter[0] == 'door':
                    screentext.changetext("PRESS E TO ENTER")
                    if keys[pygame.K_e]:
                        changemaps(str(inter[2]))

        # Update position if no collisions
        self.rect.move_ip(dx, dy)
        self.rect.clamp_ip(pygame.Rect(0, 0, map.map_width, map.map_height))

        if self.direction == "left":
            self.image = self.walkleft[self.walking_index]
        else:
            self.image = self.walkright[self.walking_index]
    def draw_overhead_health_bar(self, screen):
        '''
        Simple ratio method to handle the displaying of the over head health bar when hovering over your player
        :param screen:
        :return:
        '''
        # Define colors
        HEALTH_BAR_BG_COLOR = constants.RED  # Red background color
        HEALTH_BAR_COLOR = constants.GREEN  # Green health color
        BORDER_COLOR = constants.BLACK # Black border color

        # Calculate the width and height of the health bar
        bar_width = self.rect.width
        bar_height = 5

        # Calculate the current width of the health bar based on the current HP and max HP
        current_health_width = int((self.hp / self.max_hp) * bar_width)

        # Calculate the position of the health bar above the enemy
        health_bar_x = self.rect.x
        health_bar_y = self.rect.y - bar_height - 2

        # Draw the background of the health bar
        pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (health_bar_x, health_bar_y, bar_width, bar_height))

        # Draw the current health portion of the health bar
        pygame.draw.rect(screen, HEALTH_BAR_COLOR, (health_bar_x, health_bar_y, current_health_width, bar_height))

        # Draw the border of the health bar
        pygame.draw.rect(screen, BORDER_COLOR, (health_bar_x, health_bar_y, bar_width, bar_height), 1)
class InteractableText():
    def __init__(self, font_size, text, color, screen):
        pygame.font.init()
        self.font = pygame.font.Font(None, font_size)
        self.screen = screen
        self.color = color

        # Load the image and scale it to be 3 times smaller
        self.image = pygame.image.load(constants.assetpath + "notification.png").convert()
        original_size = self.image.get_size()
        new_size = (original_size[0] // 3, original_size[1] // 3)
        self.image = pygame.transform.scale(self.image, new_size)

        self.changetext("")
        self.questnotification = False
        self.questtime = 0
        self.text_rect = self.text_surface.get_rect(center=((screen_width // 2) -200 , (screen_height - self.font.get_height() // 2) - 50))
        self.quest_text_rect = self.text_surface.get_rect(center=((screen_width // 2)- 200, (screen_height - self.font.get_height() // 2)))

    def changetext(self, text):
        self.text = text
        self.text_surface = self.font.render(text, True, self.color)

    def quest(self, reward, amount, sender):
        self.questtime = time.time()
        self.questnotification = True
        self.questtime = time.time()
        self.quest_text = f'You Received {amount} {reward} from {sender}'
        self.quest_text_surface = self.font.render(self.quest_text, True, constants.WHITE)

    def draw(self, time):
        self.screen.blit(self.text_surface, self.text_rect)
        if time - self.questtime >= 3:
            self.questtime = time
            self.questnotification = False
        if self.questnotification == True:
            self.screen.blit(self.image, (screen_width - self.image.get_width(), screen_height -self.image.get_height()))
            self.screen.blit(self.quest_text_surface, self.quest_text_rect)

screentext = InteractableText(48, "", (25,149,21), screen)
#Initiallize an instance of screentext for workaround to hoisting
class Enemy(pygame.sprite.Sprite):
    global enemies
    global enemysprites
    def __init__(self, ID, rectx, recty, speed, name, health, image,damage, map,cooldown):
        '''
        The enemy class is slightly different as a single instance is never created instead the class method
        from csv is used to build the class from information proviided by the server similarly the fromcsv class
        also handles movement, however all basic attributes are found below.
        :param ID:
        :param rectx:
        :param recty:
        :param speed:
        :param name:
        :param health:
        :param image:
        :param map:
        '''
        super().__init__()
        self.ID = ID
        self.x = rectx // 32
        self.y = recty // 32
        self.name = name
        self.health = health
        self.image = image
        self.rect = pygame.Rect(rectx // 32, recty // 32, 32, 32)
        self.rect.x = rectx
        self.rect.y = recty
        self.max_health = 100
        self.hp = hp
        self.map = map
        self.damage = int(damage)
        self.speed = int(speed)
        self.alive = True
        self.player = player
        self.targetcoord = None  # Initialize target coordinate as None
        enemysprites.add(self)
        enemies.append(self.ID)
        self.cooldown = float(cooldown)  # Cooldown duration in seconds
        self.last_attack_time = 0
        self.equippedweapon = "Melee"

    def update(self):
        '''
        This checks if the enemy is hit and tells the server it has been hit by said player
        Futhermore the enemy will also check if its been hit and has a target if not whoever hit it will be immediatley tracked
        and the enemy will pathfind towards said player.
        :return:
        '''
        for proj in projectiles:
            if self.rect.colliderect(proj) and proj.map == self.map:
                self.hit(proj.damage)

        # Check if target coordinate is set and move towards it
        if self.targetcoord is not None:
            target_x, target_y = self.targetcoord
            dx = target_x - self.rect.x
            dy = target_y - self.rect.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            if distance >= 0:
                try:
                    vx = dx / distance
                    vy = dy / distance
                    self.rect.x += vx * self.speed
                    self.rect.y += vy * self.speed
                except ZeroDivisionError:
                    pass

    def hit(self, dmg):
        ENEMYHIT["ID"] = self.ID
        ENEMYHIT["DMG"] = dmg
        s.send((json.dumps(ENEMYHIT) + "#").encode())

        self.hp -= dmg

        if self.hp <= 0:
            self.alive = False
            self.kill()
            enemysprites.remove(self)


        self.damage_text = f"-{dmg}" #formatted the damage text as the dmg taken
        self.damage_timer = pygame.time.get_ticks() + 1000  #display for 1 second

    def draw_health_bar(self, screen):
        '''
        Method copied from the player class to display health of the enemy
        However this method is recusrivley called by the main loop so the enemies health is always shown
        :param screen:
        :return:
        '''
        if str(self.map) == str(map.map_id):
            HEALTH_BAR_BG_COLOR = constants.RED  # Red background color
            HEALTH_BAR_COLOR = constants.GREEN  # Green health color
            BORDER_COLOR = constants.BLACK  # Black border color

            # Calculate the width and height of the health bar
            bar_width = self.rect.width
            bar_height = 5

            # Calculate the current width of the health bar based on the current HP and max HP
            current_health_width = int((self.hp / self.max_health) * bar_width)

            # Calculate the position of the health bar above the enemy
            health_bar_x = self.rect.x
            health_bar_y = self.rect.y - bar_height - 2

            # Draw the background of the health bar
            pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (health_bar_x, health_bar_y, bar_width, bar_height))

            # Draw the current health portion of the health bar
            pygame.draw.rect(screen, HEALTH_BAR_COLOR, (health_bar_x, health_bar_y, current_health_width, bar_height))

            # Draw the border of the health bar
            pygame.draw.rect(screen, BORDER_COLOR, (health_bar_x, health_bar_y, bar_width, bar_height), 1)

            if hasattr(self, 'damage_text') and pygame.time.get_ticks() < self.damage_timer:
                damage_font = pygame.font.Font(None, 36)
                damage_text = damage_font.render(self.damage_text, True, (255, 0, 0))  # Red text
                damage_text_rect = damage_text.get_rect()
                damage_text_rect.center = (self.rect.centerx, self.rect.y - 20)  # Adjust the position

                screen.blit(damage_text, damage_text_rect)

    def check_collision(self, player):
        '''
        THis checks if the player is in contact with the enemy and if so handles the cooldown between enemy attacks
        allowing the enemy to attack the player.

        Ive choosen to handle enemy damage client side in an effort to avoid desync between the client and server
        allowing the what you see is what you get approach.
        :param player:
        :return:
        '''
        current_time = time.time()
        if current_time - self.last_attack_time >= self.cooldown and str(self.map) == str(map.map_id):
            if self.rect.colliderect(player.rect):
                e = str(self.name)
                player.lastdmgtype = e
                player.hp -= int(self.damage * (1- (player.damage_reduc/100)))
                print(int(self.damage * (1- (player.damage_reduc/100))))
                # Update the last attack time
                self.last_attack_time = current_time
    @classmethod
    def from_csv(cls, name, rectx, recty, ID, hp, map):
        '''
        This is the method that is called to actually create the enemy, the server will send a packet if the (enemy) is on your layer
        the recv_server method will see this gather the key info like the type of enemy, position, health and map of the enemy
        and the instance will be created. this method is called to update enemy positioning also by simply checking if the ID
        exists in the enemies lsit if so it will not create a new instance just update that instances values
        :param name:
        :param rectx:
        :param recty:
        :param ID:
        :param hp:
        :param map:
        :return:
        '''

        if ID not in enemies:
            # Open the CSV file and read its contents
            with open(constants.configpath+'enemies.csv', 'r') as file:
                reader = csv.DictReader(file)
                # Loop through each row in the file
                for row in reader:
                    # Check if the name in the row matches the name of the enemy we're looking for
                    if row['name'] == name:
                        # Create a new instance of the Enemy class with the attributes from the row
                            enemy = cls(
                                ID=ID,
                                name=row['name'],
                                rectx=rectx,
                                recty=recty,
                                speed=row['speed'],
                                health=hp,
                                map=map,
                                damage = row['damage'],
                                image=pygame.image.load(constants.assetpath+ row['image']),
                                cooldown=row['cooldown']
                            )
                            return enemy
        else:
            if hp > 0:
                for enemy in enemysprites.sprites():
                    if hasattr(enemy, "ID") and enemy.ID == ID:
                        enemy.targetcoord = (rectx, recty)  # Set the target coordinate as a tuple
                        continue
            if hp <= 0:
                for enemy in enemysprites:
                    if enemy.ID == ID:
                        enemies.remove(ID)
                        enemy.alive = False
                        enemysprites.remove(enemy)
class Transfer:
    global interrupt
    invimgs = []
    def __init__(self, player):
        '''
        This is the constructor for the transfer window that is displayed when interacting with a container
        the paramater player is used so the inventory is able to be referenced allowing updates to it
        :param player:
        '''
        self.player = player
        self.container_inv = player.continv
        self.selected_tab = "Weapons" #Initalizes the transfer window to open on the weapons tab
        self.transfer_all = False  # Flag to indicate transferring all items
        self.screen = None
        self.font = None
        self.hovered_item = None
        self.hovered_player_item = None
        self.item = None
        self.highlight_color = constants.BLUE
        self.type = None

    def getitemdata(self):
        '''
        The item data method is called whenever an object is hovered and displays the releveant data about that item
        from the items.py import and displays this to the user.
        :return:
        '''
        if self.hovered_item:
            self.item = self.hovered_item
        if self.hovered_player_item:
            self.item = self.hovered_player_item

        if self.item:
            if self.selected_tab == "Weapons":
                item_data = items.Weapons.get(self.item)
                if item_data:
                    item = self.item
                    img_path = (item_data[0])
                    dmg = item_data[1]
                    firerate = item_data[2]
                    ammo = item_data[3]
                    img = pygame.image.load(constants.assetpath+img_path)
                    imgrect = img.get_rect()
                    imgrect.center = (screen_width // 2, screen_height - 50)
                    self.screen.blit(img, imgrect)
            elif self.selected_tab == "Armor":
                item_data = items.Armor.get(self.item)
                if item_data:
                    item = self.item
                    img_path = (item_data[0])
                    slot = item_data[1]
                    armorval = item_data[2]
                    img = pygame.image.load(constants.assetpath+img_path)
                    imgrect = img.get_rect()
                    imgrect.center = (screen_width // 2, screen_height - 50)
                    self.screen.blit(img, imgrect)
            elif self.selected_tab == "Ammo":
                item_data = items.Ammo.get(self.item)
                if item_data:
                    item = self.item
                    img_path = (item_data[0])
                    bulletvel = item_data[1]
                    penval = item_data[2]
                    img = pygame.image.load(constants.assetpath+img_path)
                    imgrect = img.get_rect()
                    imgrect.center = (screen_width // 2, screen_height - 50)
                    self.screen.blit(img, imgrect)
            elif self.selected_tab == "Consumables":
                item_data = items.Consumables.get(self.item)
                if item_data:
                    item = self.item
                    img_path = (item_data[0])
                    effect = item_data[1]
                    value = item_data[2]
                    img = pygame.image.load(constants.assetpath+img_path)
                    imgrect = img.get_rect()
                    imgrect.center = (screen_width // 2, screen_height - 50)
                    self.screen.blit(img, imgrect)
            elif self.selected_tab == "Misc":
                item_data = items.Misc.get(self.item)
                if item_data:
                    item = self.item
                    img_path = (item_data[0])
                    MiscID = item_data[1]
                    img = pygame.image.load(constants.assetpath+img_path)
                    imgrect = img.get_rect()
                    imgrect.center = (screen_width // 2, screen_height - 50)
                    self.screen.blit(img, imgrect)

    def initialize(self):
        #Initilaizes fonts and crates a window
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.initialize_fonts()
        pygame.display.set_caption("Container"+str(player.contID))

    def initialize_fonts(self):
        pygame.font.init()
        self.font = pygame.font.Font(None, constants.FONT_SIZE)

    def draw_inventory(self):
        '''
        This is the main driver in drawing all of the UI elements and calles methods to draw the releveant data to the screen
        :return:
        '''
        self.screen.fill(constants.GRAY)  # Set the left side of the screen to gray
        pygame.draw.rect(self.screen, constants.DARK_GRAY, pygame.Rect(screen_width // 2, 0, screen_width // 2, screen_height))  # Set the right side of the screen to dark gray
        self.draw_tabs()
        self.draw_container_inventory()
        self.draw_player_inventory()
        if self.hovered_item or self.hovered_player_item:
            self.getitemdata()
        pygame.display.flip()

    def draw_tabs(self):
        'Lists the tabs using the players inventory as a template'
        tabs = list(self.player.inventory.keys())
        tab_pos = constants.PLAYER_INVENTORY_POS[0]
        for tab in tabs:
            tab_rect = pygame.Rect(tab_pos, constants.PLAYER_INVENTORY_POS[1] - constants.TAB_HEIGHT, constants.TAB_WIDTH, constants.TAB_HEIGHT)
            pygame.draw.rect(self.screen, constants.BLUE if tab == self.selected_tab else constants.GRAY, tab_rect)
            text = self.font.render(tab, True, constants.WHITE)
            self.screen.blit(text, (tab_pos + 10, constants.PLAYER_INVENTORY_POS[1] - constants.TAB_HEIGHT + 5))
            tab_pos += constants.TAB_WIDTH

    def draw_player_inventory(self):
        player_inv = self.player.inventory[self.selected_tab]
        item_pos = list(constants.PLAYER_INVENTORY_POS)
        for item, count in player_inv.items():
            item_rect = pygame.Rect(item_pos[0], item_pos[1], constants.TAB_WIDTH, constants.TAB_HEIGHT)
            pygame.draw.rect(self.screen, constants.GRAY, item_rect)
            if item_rect.collidepoint(pygame.mouse.get_pos()):
                self.hovered_player_item = item
                if self.transfer_all or (pygame.key.get_mods() & pygame.KMOD_SHIFT and item == self.hovered_player_item or item == self.hovered_item):
                    self.highlight_color = constants.RED  # Change highlight color to red
                else:
                    self.highlight_color = constants.BLUE  # Change highlight color back to blue
                pygame.draw.rect(self.screen, self.highlight_color, item_rect, 3)  # Add highlight border
                self.hovered_player_item = item  # Store the hovered item in player's inventory
            text = self.font.render(f"{count}x {item}", True, constants.BLACK)
            self.screen.blit(text, (item_pos[0] + 10, item_pos[1] + 10))
            item_pos[1] += constants.TAB_HEIGHT

    def draw_container_inventory(self):
        item_pos = list(constants.CONTAINER_INVENTORY_POS)
        pygame.draw.rect(self.screen, constants.DARK_GRAY,
                         pygame.Rect(constants.CONTAINER_INVENTORY_POS[0], 20, constants.TAB_WIDTH, constants.TAB_HEIGHT))  # Container header
        text = self.font.render("Container", True, constants.WHITE)
        self.screen.blit(text, (constants.CONTAINER_INVENTORY_POS[0] + 10, 25))
        container_items = []
        for item, count in self.container_inv[self.selected_tab].items():
            container_items.append((item, count))  # Store items in a separate list
        for item, count in container_items:
            item_rect = pygame.Rect(item_pos[0], item_pos[1], constants.TAB_WIDTH, constants.TAB_HEIGHT)
            pygame.draw.rect(self.screen, constants.DARK_GRAY, item_rect)
            if item_rect.collidepoint(pygame.mouse.get_pos()):
                if self.transfer_all or (pygame.key.get_mods() & pygame.KMOD_SHIFT and item == self.hovered_item):
                    self.highlight_color = constants.RED  # Change highlight color to red
                else:
                    self.highlight_color = constants.BLUE  # Change highlight color back to blue
                pygame.draw.rect(self.screen, self.highlight_color, item_rect, 3)  # Add highlight border
                self.hovered_item = item  # Store the hovered item
            text = self.font.render(f"{count}x {item}", True, constants.BLACK)
            self.screen.blit(text, (item_pos[0] + 10, item_pos[1] + 10))
            item_pos[1] += constants.TAB_HEIGHT

    def handle_events(self):
        '''
        This handles keybinds in the transfer for events such as shift clicking items which results in the whole
        stack being transfered
        :return:
        '''
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    player.continv = {
                        "Weapons": {},
                        "Armor": {},
                        "Ammo": {"9mm Ammo": 1},
                        "Consumables": {},
                        "Misc": {}
                    }
                    self.invrunning = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    self.transfer_all = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    self.transfer_all = False

    def handle_click(self, pos):
        # Check if tab is clicked
        tabs = list(self.player.inventory.keys())
        tab_pos = constants.PLAYER_INVENTORY_POS[0]
        for tab in tabs:
            tab_rect = pygame.Rect(tab_pos, constants.PLAYER_INVENTORY_POS[1] - constants.TAB_HEIGHT, constants.TAB_WIDTH, constants.TAB_HEIGHT)
            if tab_rect.collidepoint(pos) and self.selected_tab != tab:
                self.selected_tab = tab
                self.selected_item = None  # Reset the selected item when switching tabs
                break
            tab_pos += constants.TAB_WIDTH
            self.hovered_player_item = None

        # Check if item is clicked in player inventory
        player_inv = self.player.inventory[self.selected_tab]
        item_pos = list(constants.PLAYER_INVENTORY_POS)
        for item, count in player_inv.items():
            item_rect = pygame.Rect(item_pos[0], item_pos[1], constants.TAB_WIDTH, constants.TAB_HEIGHT)
            if item_rect.collidepoint(pos):
                self.type = TOCONT
                if self.transfer_all:
                    self.transfer_all_items(player_inv, self.container_inv[self.selected_tab], item)
                elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.transfer_all_items(player_inv, self.container_inv[self.selected_tab], item)
                else:
                    self.transfer_item(player_inv, self.container_inv[self.selected_tab], item)
                self.hovered_item = None  # Clear the hovered item
                break
            item_pos[1] += constants.TAB_HEIGHT

        # Check if item is clicked in container inventory
        container_inv = self.container_inv[self.selected_tab]
        item_pos = list(constants.CONTAINER_INVENTORY_POS)
        for item, count in container_inv.items():
            item_rect = pygame.Rect(item_pos[0], item_pos[1], constants.TAB_WIDTH, constants.TAB_HEIGHT)
            if item_rect.collidepoint(pos):
                self.type = FROMCONT
                if self.transfer_all:
                    self.transfer_all_items(container_inv, self.player.inventory[self.selected_tab], item)
                elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.transfer_all_items(container_inv, self.player.inventory[self.selected_tab], item)
                else:
                    self.transfer_item(container_inv, self.player.inventory[self.selected_tab], item)
                self.hovered_item = None  # Clear the hovered item
                break
            item_pos[1] += constants.TAB_HEIGHT

    def transfer_item(self, from_inventory, to_inventory, item):
        '''
        Called when you click an item moves from the one inventory to the other
        :param from_inventory:
        :param to_inventory:
        :param item:
        :return:
        '''

        self.type["TAB"] = self.selected_tab
        self.type["Item"] = item
        self.type["A"] = 1
        self.type["ID"] = player.contID
        from_inventory[item] -= 1
        if from_inventory[item] == 0:
            del from_inventory[item]
        s.send((json.dumps(self.type) + "#").encode())
        to_inventory[item] = to_inventory.get(item, 0) + 1

        if self.selected_tab == "Armor":
            if any(item in player.equipped[slot] for slot in ["H", "C", "F"]) and item not in player.inventory.get("Armor"):
                for slot in ["H", "C", "F"]:
                    if item in player.equipped[slot]:
                        player.equipped[slot] = {}
                        player.statupdate()
        if self.selected_tab == "Weapons":
            if item in player.equipped["Hand"] and item not in player.inventory.get("Weapons"):
                    if item in player.equipped["Hand"]:
                        player.equipped["Hand"] = {}
        if self.selected_tab == "Consumables":
            if item in player.equipped["Offhand"] and item not in player.inventory.get("Consumables"):
                    if item in player.equipped["Offhand"]:
                        player.equipped["Offhand"] = {}




    def transfer_all_items(self, from_inventory, to_inventory, item=None):
        if item is None:
            for item in list(from_inventory.keys()):
                count = from_inventory[item]
                to_inventory[item] = to_inventory.get(item, 0) + count
                del from_inventory[item]
        else:
            count = from_inventory[item]
            self.type["TAB"] = self.selected_tab
            self.type["Item"] = item
            self.type["A"] = count
            self.type["ID"] = player.contID
            s.send((json.dumps(self.type) + "#").encode())
            to_inventory[item] = to_inventory.get(item, 0) + count
            del from_inventory[item]
            return  # Exit the method after transferring the specified item

        if self.selected_tab == "Armor":
            if any(item in player.equipped[slot] for slot in ["H", "C", "F"]) and item not in player.inventory.get("Armor"):
                for slot in ["H", "C", "F"]:
                    if item in player.equipped[slot]:
                        player.equipped[slot] = {}
                        player.statupdate()
        if self.selected_tab == "Weapons":
            if item in player.equipped["Hand"] and item not in player.inventory.get("Weapons"):
                    if item in player.equipped["Hand"]:
                        player.equipped["Hand"] = {}
        if self.selected_tab == "Consumables":
            if item in player.equipped["Offhand"] and item not in player.inventory.get("Consumables"):
                    if item in player.equipped["Offhand"]:
                        player.equipped["Offhand"] = {}
    def run(self):
        '''
        The main run loop which recursivley calls fucntions as well as cheking for enemy collisons while in a container
        as opening a container would prevent enemy damage otherwise
        :return:
        '''
        self.initialize()
        self.invrunning = True
        while self.invrunning and interrupt == False:
            for enemy in enemysprites.sprites():
                enemy.check_collision(player)
            if player.hp <= 0:
                self.invrunning = False
            clock.tick(60)
            self.handle_events()
            self.draw_inventory()
            self.hovered_player_item = None
            self.hovered_item = None
            self.item = None
class Projectile(pygame.sprite.Sprite):
    def __init__(self, weapon, source, target_pos):
        super().__init__()
        self.source = source
        self.sourcex = source.rect.x
        self.sourcey = source.rect.y
        self.target_pos = target_pos
        self.rect = None
        self.alivetime = time.time()
        self.lastdistance = 99999


        # Calculate data based on the weapon
        if weapon != {}:
            weapon_data = items.Weapons.get(weapon)
            self.caliber = weapon_data[3]
            self.damage = weapon_data[1]
            bullet_data = items.Ammo.get(self.caliber)
            player.lastammo = self.caliber
            self.speed = 100 * bullet_data[1]
        else:
            self.caliber = None
            self.damage = 1
            self.speed = 0

        self.map = source.map

        # Create a bullet if caliber is not None, otherwise create an inflated rect
        if self.caliber is not None:
            self.rect = pygame.Rect(source.rect.center, (5, 5))
        else:
            self.rect = source.rect.inflate(30, 30)
            self.rect_color = constants.RED


        self.checkammo()
    def checkammo(self):
        if self.caliber == None:
            self.rect = self.rect.inflate(30, 30)
            self.rect_color = constants.RED
            projectiles.add(self)
        if self.caliber in player.inventory["Ammo"] and player.inventory["Ammo"][self.caliber] > 0:
            player.inventory["Ammo"][self.caliber] -= 1
            projectiles.add(self)
            player.shots += 1
        elif self.caliber != None:
            self.kill()
            projectiles.remove(self)

    def update(self):
        if self.caliber is not None:
            if self.speed > 0:
                for obstacle in map.obstacles:
                    if self.rect.colliderect(obstacle):
                        if self.caliber != "50cal":
                            self.speed = 0
                pygame.draw.rect(map.map_surface, constants.WHITE, self.rect)

                # Calculate time elapsed since the last frame
                current_time = time.time()
                time_elapsed = current_time - self.alivetime

                # Calculate new position based on time elapsed and speed
                distance = self.speed * time_elapsed
                target_x, target_y = self.target_pos
                dx = target_x - self.rect.x
                dy = target_y - self.rect.y
                distance_to_target = max(abs(dx), abs(dy))
                if distance_to_target < self.lastdistance:
                    self.lastdistance = distance_to_target
                elif distance_to_target > self.lastdistance:
                    projectiles.remove()
                    self.kill()
                    return

                if distance_to_target > 0:
                    speed_x = (dx / distance_to_target) * distance
                    speed_y = (dy / distance_to_target) * distance


                if distance_to_target == 0:
                    projectiles.remove(self)
                    self.kill()

                try:
                    self.rect.x += int(speed_x)
                    self.rect.y += int(speed_y)
                except UnboundLocalError:
                    self.rect.x += 0
                    self.rect.y += 0

                if self.rect.left < 0 or self.rect.right > map.map_width or self.rect.top < 0 or self.rect.bottom > map.map_height:
                    # Handle if the bullet goes out of bounds
                    projectiles.remove(self)
                    self.kill()

            else:
                screentext.changetext("OUT OF AMMO")
                self.caliber = None
                projectiles.remove(self)
                self.kill()
        else:
            # Draw the inflated rect as red
            pygame.draw.rect(map.map_surface, self.rect_color, self.rect)
            if time.time() - self.alivetime > 0.1:
                projectiles.remove(self)
                self.kill()
class LockpickingGame:
    def __init__(self):
        self.width, self.height = constants.screen_width, constants.screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Mini Game")
        self.clock = pygame.time.Clock()

        # Load images
        self.lock_image = pygame.image.load(constants.assetpath + "lock.png")
        self.lockpick_image = pygame.image.load(constants.assetpath + "lockpick.png")

        # Set up the lock variables
        self.lock_angle = 0
        self.lock_speed = 0
        self.lock_original_angle = 0
        self.lockpick_health = 250
        self.max_lockpickhp = 250

        # Set up the lockpick variables
        self.lockpick_angle = 0
        self.stop_lockpick = False

        # Generate a random angle for the lock
        self.target_angle = random.randint(-179, 180)
        self.target_angles = list(range(self.target_angle - 5, self.target_angle + 6))
        self.target_angles = [i for i in self.target_angles if i <= 180]

        #Flags to check win status
        self.won = False
        self.running = True

    def rotate_lock(self, direction):
        if direction == "right":
            self.lock_speed = 1
            self.stop_lockpick = True
            if self.lockpick_angle // 1 not in self.target_angles:
                self.lockpick_health -= 1
            self.drawhp()

    def stop_rotating(self):
        self.lock_speed = 0
        self.stop_lockpick = False

    def check_win(self):
        if self.lock_angle >= 90 and math.isclose(self.lockpick_angle, self.target_angle, abs_tol=5):
            return True
        return False

    def drawhp(self):
        HEALTH_BAR_BG_COLOR = constants.RED
        HEALTH_BAR_COLOR = constants.GREEN
        BORDER_COLOR = constants.BLACK

        bar_width = 500
        bar_height = 50
        current_health_width = int((self.lockpick_health / self.max_lockpickhp) * bar_width)
        health_bar_x = (constants.screen_width//2) - 250
        health_bar_y = 52 - bar_height - 2

        pygame.draw.rect(self.screen, HEALTH_BAR_BG_COLOR, (health_bar_x, health_bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, HEALTH_BAR_COLOR, (health_bar_x, health_bar_y, current_health_width, bar_height))
        pygame.draw.rect(self.screen, BORDER_COLOR, (health_bar_x, health_bar_y, bar_width, bar_height), 1)

    def run(self,ID):
        global lockedcontainers
        while self.running:
            self.screen.fill(constants.DARK_GRAY)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_d]:
                self.rotate_lock("right")
            else:
                self.stop_rotating()

            if self.lockpick_health <= 0:
                if "Lockpick" in player.inventory.get("Misc"):
                    player.inventory["Misc"]["Lockpick"] -= 1
                    RMV["AMMO"] = ("Lockpick")
                    RMV["AMOUNT"] = 1
                    s.send((json.dumps(RMV) + "#").encode())
                    if player.inventory["Misc"]["Lockpick"] <= 0:
                        del player.inventory["Misc"]["Lockpick"]
                    self.lockpick_health = self.max_lockpickhp
                else:
                    self.running = False

            self.lock_angle += self.lock_speed
            if self.lock_angle >= 90:
                self.lock_angle = 90

            self.drawhp()

            if not self.stop_lockpick:
                self.lockpick_angle = math.degrees(
                    math.atan2(pygame.mouse.get_pos()[1] - self.height / 2, pygame.mouse.get_pos()[0] - self.width / 2)
                )

            if self.check_win():
                if self.lock_angle >= 90:
                    if not self.won:
                        self.won = True
            else:
                pygame.draw.rect(self.screen, constants.RED, (self.width // 2 - 50, self.height // 2 - 50, 100, 100))

            if not self.won:
                rotated_lock = pygame.transform.rotate(self.lock_image, -1 * self.lock_angle)
            else:
                rotated_lock = pygame.transform.rotate(self.lock_image, 270)
                ULK["ID"] = ID
                s.send((json.dumps(ULK) + "#").encode())

                lockedcontainers.remove(ID)

                openCont(ID)
                self.running = False

            rotated_lockpick = pygame.transform.rotate(self.lockpick_image, -1 * self.lockpick_angle)

            lock_rect = rotated_lock.get_rect(center=(self.width // 2, self.height // 2))
            lockpick_rect = rotated_lockpick.get_rect(center=(self.width // 2, self.height // 2))

            self.screen.blit(rotated_lock, lock_rect)
            self.screen.blit(rotated_lockpick, lockpick_rect)

            if not keys[pygame.K_d] and self.lock_angle > self.lock_original_angle:
                self.lock_angle -= 0.5

            if self.lock_speed != 0:
                self.lockpick_moving = True
            else:
                self.lockpick_moving = False

            pygame.display.flip()
            self.clock.tick(60)
class InventoryMenu:
    def __init__(self, screen_width, screen_height, player):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.player_inventory = player.inventory
        self.player_equipped = player.equipped
        self.menu_width = screen_width
        self.menu_height = screen_height
        self.menu_x = (screen_width - self.menu_width) // 2
        self.menu_y = (screen_height - self.menu_height) // 2
        self.selected_tab = 'Weapons'
        self.selected_items = {}  # Dictionary to store selected items for each tab
        self.item_rects = {}  # Dictionary to store item rects
        self.is_running = True
        self.use_button_visible = False

        # Define the positions and sizes of the black squares
        self.equipped_x = self.menu_x + self.menu_width - 50
        self.equipped_y = (self.menu_y + self.menu_height) // 2 - (40) * 2  # Adjusted position
        self.equipped_size = 30
        self.equipped_spacing = 10
        self.checkforzero()

    def checkforzero(self):
        try:
            for i in player.inventory["Ammo"]:
                if player.inventory["Ammo"][i] <= 0:
                    del player.inventory["Ammo"][i]
        except RuntimeError:
            pass

    def show_inventory_menu(self):
        use_button_rect = pygame.Rect(
            (self.menu_x + self.menu_width) // 2 - 50,
            (self.menu_y + self.menu_height) // 2 - 25,
            100,
            50
        )

        while self.is_running:
            clicked_tab = None
            clicked_item = None
            use_button_clicked = False  # Flag to track if the "Use" button was clicked

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        clicked_tab = self.get_clicked_tab(event.pos)
                        clicked_item = self.get_clicked_item(event.pos)
                        if use_button_rect.collidepoint(event.pos):
                            use_button_clicked = True  # Set the flag if the "Use" button is clicked

            if clicked_tab is not None:
                self.selected_tab = clicked_tab
                self.selected_items[self.selected_tab] = None  # Reset selected item when changing tabs
                self.use_button_visible = False  # Hide the "Use" button when switching tabs

            if clicked_item is not None:
                self.selected_items[self.selected_tab] = clicked_item
                # If the selected item is in Weapons, Armor, or Consumables tab, show the Use button
                if self.selected_tab in ["Weapons", "Armor", "Consumables"]:
                    self.use_button_visible = True
                else:
                    self.use_button_visible = False

            # Move the item rects initialization outside the tab selection check
            self.initialize_item_rects()

            self.screen.fill(constants.DARK_GRAY)
            pygame.draw.rect(self.screen, (constants.DARK_GRAY),
                             (self.menu_x, self.menu_y, self.menu_width, self.menu_height))

            self.draw_tabs()
            self.draw_inventory()
            self.draw_selected_item()

            if self.use_button_visible:
                self.show_use_button()
            # Check if the "Use" button is clicked
            if use_button_clicked:
                self.use_item(self.selected_items[self.selected_tab])

            # Call the draw_equipped function to draw the black squares
            self.draw_equipped()

            for enemy in enemysprites.sprites():
                enemy.check_collision(player)

            pygame.display.flip()
            self.clock.tick(60)

    def initialize_item_rects(self):
        self.item_rects = {}
        text_x = self.menu_x + 20
        text_y = self.menu_y + 50
        selected_items = self.player_inventory.get(self.selected_tab, {})

        for item, quantity in selected_items.items():
            item_rect = pygame.Rect(text_x, text_y, self.menu_width - 40, 30)
            self.item_rects[item] = item_rect  # Store item rect in the dictionary
            text_y += 50  # Increase vertical spacing between items

    def draw_tabs(self):
        tab_width = self.menu_width // len(self.player_inventory)
        tab_height = 30
        text_y = self.menu_y + 10
        for i, tab in enumerate(self.player_inventory.keys()):
            tab_rect = pygame.Rect(self.menu_x + (tab_width * i), text_y, tab_width, tab_height)
            tab_text = self.font.render(tab, True, (0, 0, 0))
            pygame.draw.rect(self.screen, (200, 200, 200), tab_rect)
            self.screen.blit(tab_text, (tab_rect.x + 10, tab_rect.y + 5))
            if self.selected_tab == tab:
                pygame.draw.rect(self.screen, (0, 0, 255), tab_rect, 3)

    def draw_inventory(self):
        text_x = self.menu_x + 20
        text_y = self.menu_y + 50
        selected_items = self.player_inventory.get(self.selected_tab, {})

        for item, quantity in selected_items.items():
            item_rect = self.item_rects.get(item, pygame.Rect(text_x, text_y, self.menu_width - 40, 30))
            item_text = self.font.render(f'{item}: {quantity}', True, (0, 0, 0))
            pygame.draw.rect(self.screen, (200, 200, 200), item_rect)
            self.screen.blit(item_text, (text_x + 10, text_y + 5))
            text_y += 50  # Increase vertical spacing between items

    def draw_selected_item(self):
        selected_item = self.selected_items.get(self.selected_tab, None)
        if selected_item:
            text_x = self.menu_x + 20
            text_y = self.menu_y + 50

            try:
                if hasattr(items, self.selected_tab):
                    item_data = None
                    if self.selected_tab == "Weapons":
                        item_data = items.Weapons.get(selected_item)
                    elif self.selected_tab == "Armor":
                        item_data = items.Armor.get(selected_item)
                    elif self.selected_tab == "Ammo":
                        item_data = items.Ammo.get(selected_item)
                    elif self.selected_tab == "Consumables":
                        item_data = items.Consumables.get(selected_item)
                    elif self.selected_tab == "Misc":
                        item_data = items.Misc.get(selected_item)

                    if item_data:
                        item = selected_item
                        img_path = (item_data[0])
                        img = pygame.image.load(constants.assetpath+img_path)
                        imgrect = img.get_rect()
                        imgrect.center = (self.menu_x + self.menu_width // 2, self.menu_y + self.menu_height - 30)
                        self.screen.blit(img, imgrect)

                        text_y += self.menu_height // 2

                        item_details_text = self.font.render(f'Name: {item}', True, (0, 0, 0))
                        self.screen.blit(item_details_text, (text_x, text_y))
                        text_y += 30

                        if self.selected_tab == "Weapons":
                            dmg = item_data[1]
                            firerate = item_data[2]
                            ammo = item_data[3]
                            details = [f'Damage: {dmg}', f'Firerate: {firerate}', f'Ammo Type: {ammo}']
                        elif self.selected_tab == "Armor":
                            slot = item_data[1]
                            armorval = item_data[2]
                            details = [f'Slot: {slot}', f'Armor Value: {armorval}']
                        elif self.selected_tab == "Ammo":
                            bulletvel = item_data[1]
                            penval = item_data[2]
                            details = [f'Bullet Velocity: {bulletvel}', f'Penetration Value: {penval}']
                        elif self.selected_tab == "Consumables":
                            effect = item_data[1]
                            value = item_data[2]
                            details = [f'Effect: {effect}', f'Effect Amount: {value}']
                        elif self.selected_tab == "Misc":
                            MiscID = item_data[1]
                            details = [f'ID: {MiscID}']

                        for detail in details:
                            detail_text = self.font.render(detail, True, (0, 0, 0))
                            self.screen.blit(detail_text, (text_x, text_y))
                            text_y += 30

                    selected_item_text = self.font.render(f'Selected Item: {selected_item}', True, (0, 0, 0))
                    text_y = self.menu_y + self.menu_height - 30
                    self.screen.blit(selected_item_text, (text_x, text_y))

                else:
                    print(f"'{self.selected_tab}' not found in items.")
            except Exception as e:
                print(e)
                pass

    def show_use_button(self):
        # Calculate the position for the centered "Use" button
        button_width = 100
        button_height = 50
        button_x = (self.menu_x + self.menu_width) // 2 - (button_width // 2)
        button_y = (self.menu_y + self.menu_height) // 2 - (button_height // 2)

        # Create a green "Use" button
        use_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, (0, 255, 0), use_button_rect)
        use_text = self.font.render("USE", True, (0, 0, 0))
        use_text_rect = use_text.get_rect(center=use_button_rect.center)
        self.screen.blit(use_text, use_text_rect)

    def draw_equipped(self):
        equipped_slots = player.equipped.keys()
        for i, slot in enumerate(equipped_slots):
            item_name = player.equipped[slot]
            if item_name:
                if item_name in player.equipped_images:
                    img = player.equipped_images[item_name]
                else:
                    # Load the image for the equipped item
                    if self.selected_tab == "Weapons":
                        item_data = items.Weapons.get(item_name)
                    elif self.selected_tab == "Armor":
                        item_data = items.Armor.get(item_name)
                    elif self.selected_tab == "Consumables":
                        item_data = items.Consumables.get(item_name)

                    try:
                        img_path = (item_data[0])
                        img = pygame.image.load(constants.assetpath+img_path)
                        img = pygame.transform.scale(img, (self.equipped_size, self.equipped_size))
                        player.equipped_images[item_name] = img  # Store the image in the dictionary

                    except Exception as e:
                        print(e)
                        pass

                # Scale the image to the size of the equipped square
                try:
                    img = pygame.transform.scale(img, (self.equipped_size, self.equipped_size))

                    # Display the equipped item's image
                    rect_x = self.equipped_x
                    rect_y = self.equipped_y + (i * (self.equipped_size + self.equipped_spacing))
                    rect = pygame.Rect(rect_x, rect_y, self.equipped_size, self.equipped_size)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect)
                    imgrect = img.get_rect(topleft=(rect_x, rect_y))
                    self.screen.blit(img, imgrect)
                except Exception as e:
                    print(e)
            else:
                # If no item is equipped in this slot, draw an empty black square
                rect_x = self.equipped_x
                rect_y = self.equipped_y + (i * (self.equipped_size + self.equipped_spacing))
                rect = pygame.Rect(rect_x, rect_y, self.equipped_size, self.equipped_size)
                pygame.draw.rect(self.screen, (0, 0, 0), rect)

    def get_clicked_tab(self, mouse_pos):
        tab_width = self.menu_width // len(self.player_inventory)
        tab_height = 30
        text_y = self.menu_y + 10
        for i, tab in enumerate(self.player_inventory.keys()):
            tab_rect = pygame.Rect(self.menu_x + (tab_width * i), text_y, tab_width, tab_height)
            if tab_rect.collidepoint(mouse_pos):
                return tab

        return None

    def get_clicked_item(self, mouse_pos):
        for item, item_rect in self.item_rects.items():
            if item_rect.collidepoint(mouse_pos):
                return item

    def save_equipped_items(self,player):
        equipped_data = {
            "H": player.equipped["H"],
            "C": player.equipped["C"],
            "F": player.equipped["F"],
            "Hand": player.equipped["Hand"],
            "Offhand": player.equipped["Offhand"]
        }

        with open("equipped_items.json", "w") as json_file:
            json.dump(equipped_data, json_file)
    def use_item(self, item):
        if self.selected_tab == "Weapons":
            item_data = items.Weapons.get(item)
            player.equipped["Hand"] = item
            player.equipped_images[item] = pygame.image.load(constants.assetpath+item_data[0])
        if self.selected_tab == "Armor":
            item_data = items.Armor.get(item)
            player.equipped[item_data[1]] = item
            player.equipped_images[item] = pygame.image.load(constants.assetpath+item_data[0])
            player.statupdate()
        if self.selected_tab == "Consumables":
            item_data = items.Consumables.get(item)
            player.equipped["Offhand"] = item
            player.equipped_images[item] = pygame.image.load(constants.assetpath+item_data[0])
        self.save_equipped_items(player)
        print("equipped")
def recv_server():
    '''
    This is called via a thread in which the client activley and indepentaley recieves data from the server
    irrelevant to the current going ons, this is mainly used to receive quest information as well as initilazing your inventory
    and players overall data.

    The use of a # is present at the end of a packet to act as a header/footer to ensure the client only recieves the information in that packet
    and also allows ordering of the packets meanign if multipel packets were recieved simultaneously only they would be executed in order
    :return:
    '''
    global pmap #sets global vairbales for the main loop to access
    global xpos
    global ypos
    global hp
    global map
    global enemies
    global interrupt

    while True:
        data = s.recv(2048)
        try:
            data_list = data.decode().split("#") #use as a packet header and footer
            for msg_str in data_list:
                if msg_str != "":
                    msg = json.loads(msg_str) #decode the msg
                    #All the commands related to the command header of the packet
                    if msg["COMMAND"] == "INIT":
                        xpos = msg["X"]
                        ypos = msg["Y"]
                        hp = msg["HP"]
                        pmap = msg["map"]
                        print("PLAYERINTIIALZED")
                    if msg["COMMAND"] == "QUEST":
                        for q, v in player.quests:
                            if q == msg["Q"]:
                                # Update the existing value
                                player.quests.remove((q, v))
                                player.quests.add((q, msg["V"]))
                                break
                        else:
                            # Add a new (QUEST, VALUE) pair if it doesn't exist
                            player.quests.add((msg["Q"],msg["V"]))
                    if msg["COMMAND"] == "DRAW":
                        sid = int(msg["ID"])
                        RECTX = int(msg["RECTX"])
                        RECTY = int(msg["RECTY"])
                        drawotherplayers(sid,RECTX,RECTY)
                    if msg["COMMAND"] == "KILL":
                        sid = msg["ID"]
                        for sprite in otherplayers:
                            if sprite.sid == sid:
                                otherplayers.remove(sid)
                                sprite.kill()
                                sprite_ids.remove(sid)
                    if msg["COMMAND"] == "EU":
                        identifier = msg["ID"]
                        hp = msg["HP"]
                        rectx = msg["RECTX"]
                        recty = msg["RECTY"]
                        name = msg["NAME"]
                        enemymap = msg["MAP"]
                        Enemy.from_csv(name, rectx, recty, identifier,hp,enemymap)
                    if msg["COMMAND"] == "WE":
                        player.continv["Weapons"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "AR":
                        player.continv["Armor"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "AM":
                        player.continv["Ammo"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "CS":
                        player.continv["Consumables"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "MI":
                        player.continv["Misc"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "PWE":
                        player.inventory["Weapons"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "PAR":
                        player.inventory["Armor"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "PAM":
                        player.inventory["Ammo"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "PCS":
                        player.inventory["Consumables"] = json.loads(msg["I"])
                    if msg["COMMAND"] == "PMI":
                        player.inventory["Misc"] = json.loads(msg["I"])
                        load_equipped(player)
                    if msg["COMMAND"] == "REWARD":
                        item = msg["ITEM"]
                        amount = msg["A"]
                        sender = msg["SNDR"]
                        screentext.quest(item,amount,sender)
                    if msg["COMMAND"] == "LCK":
                        lockedcontainers.append(int(msg["ID"]))
                    if msg["COMMAND"] == "SULK":
                        try:
                            lockedcontainers.remove(int(msg["ID"]))
                        except IndexError:
                            pass #cotnainer has alrdy been delcared as unlocked
                    if msg["COMMAND"] == "PNG":
                        s.send((json.dumps(PING) + "#").encode())


        except Exception as e:
            print(e) #prints any errors and attempts to continue
            pass

threading.Thread(target=recv_server, args=()).start() #begin the autosave thread
def drawotherplayers(sid,RECTX,RECTY):
    '''
    simply a function to take info recieved from a packet and add the otherplayer to a class instance an store the id in a list
    :param sid:
    :param RECTX:
    :param RECTY:
    :param MAPID:
    :return:
    '''
    for sprite in otherplayers:
        if sid in sprite_ids:
            sprite.rect.x = RECTX
            sprite.rect.y = RECTY
        else:
            sprite_ids.append(sid)
            sid = OTHERPLAYER(sid, RECTX, RECTY, "walk 1.png")
            otherplayers.add(sid)
def get_object_rects(filename):
    '''
    Gathers all objects from a specified tmx file and returns them for the map class.
    :param filename:
    :return: object_rects
    '''
    tmx_data = pytmx.util_pygame.load_pygame(filename)
    object_rects = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledObjectGroup):
            for obj in layer:
                object_rects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    return object_rects
def get_interactable_rects(filename):
    '''
    similar to onject rects but only returns interactable ones
    :param filename:
    :return: interactable_rects
    '''
    tmx_data = pytmx.util_pygame.load_pygame(filename)
    interactable_rects = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledObjectGroup):
            for obj in layer:
                if obj.properties.get('interactable', False):
                    interType = obj.properties.get('intertype')
                    interID = obj.properties.get('interactable')
                    interRect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    interactable_rects.append((interType,interRect,interID))
    return interactable_rects
def draw_health_bar(screen, player):
    """
    draws the healthbar on a specified layer using the player as a paramater
    :param screen:
    :param player:
    :return:
    """

    # Define sizes and positions
    bar_width = 100
    bar_height = 20
    bar_padding = 2
    health_ratio = player.hp / player.max_hp

    # Calculate position of health bar
    health_bar_x = screen.get_width() - bar_width - bar_padding
    health_bar_y = bar_padding

    # Load the image
    image_path = constants.assetpath + "dmgreduc.png"
    image = pygame.image.load(image_path)

    # Scale the image up by 2x
    image = pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2))

    # Calculate image position
    image_x = health_bar_x + (bar_width - image.get_width()) / 2
    image_y = health_bar_y + bar_height + bar_padding

    # Draw the scaled image
    screen.blit(image, (image_x, image_y))

    # Draw background of the health bar
    pygame.draw.rect(screen, constants.WHITE, (health_bar_x, health_bar_y, bar_width, bar_height))

    # Draw current health
    health_bar_width = health_ratio * bar_width
    health_bar_rect = pygame.Rect(health_bar_x, health_bar_y, health_bar_width, bar_height)
    pygame.draw.rect(screen, constants.GREEN, health_bar_rect)

    # Create a text surface
    text_surface = font.render(str(player.damage_reduc), True, constants.WHITE)
    hptext_surface = font.render(("HP:"+str(player.hp)), True, constants.BLUE)

    # Calculate text position
    text_x = image_x + 30
    text_y = image_y *2.8

    # Draw the text surface
    screen.blit(text_surface, (text_x, text_y))
    screen.blit(hptext_surface, (health_bar_rect))
def draw_equipped_items(screen, player):
    '''
    Draws the equipped items in 4 black squares utilizing the player instances class variables.
    :param screen:
    :param player:
    :return:
    '''
    equipped_slots = player.equipped.keys()

    for i, slot in enumerate(equipped_slots): #Enumerates the slots uses contant values to seperate each square slightly
        item_name = player.equipped[slot]

        # Draw black square
        rect_x = constants.equipped_x
        rect_y = constants.equipped_y + (i * (constants.equipped_size + constants.equipped_spacing))
        rect = pygame.Rect(rect_x, rect_y, constants.equipped_size, constants.equipped_size)
        pygame.draw.rect(screen, constants.WHITE, rect)

        if item_name != {}: # Ensures the item isn't blank.
            if item_name in player.equipped_images:
                img = player.equipped_images[item_name]
                img = pygame.transform.scale(img, (constants.equipped_size, constants.equipped_size))
                imgrect = img.get_rect(topleft=(rect_x, rect_y)) #uses topleft function to get the position for the squares.
                screen.blit(img, imgrect) #blits the image
def spawn_NPCS(map):
    '''
    Returns nothing, simply creates the NPC instances upon changing maps
    :param map:
    :return None:
    '''
    with open(constants.configpath+'spawn.csv', 'r') as file:
        reader = csv.DictReader(file)
        # Loop through each row in the file
        for row in reader:
            # Check if the name in the row matches the name of the enemy we're looking for
            if row['mapID'] == map:
                mapid = str(row["mapID"])
                name = str(row["name"])
                rectx = int(row['rectx'])
                recty = int(row['recty'])
                image = (constants.assetpath+ str(row["image"]))

                npc = NPC(image,mapid,rectx,recty,name)

    # Return None if we couldn't find an enemy with the given name
    return None
def cleanup():
    '''
    Cleans up enemys that are either dead or exist on a different layer
    Removes other players from being diplayed that aren't on the layer you're on.
    :return:
    '''
    for enemy in enemysprites:
        if enemy.health <= 0:
            enemies.remove(enemy.ID)
            enemy.alive = False
            enemysprites.remove(enemy)
def openCont(ID):
    '''
    Opens a container using the specified ID, it checks it isnt locked and then creates the transfer class
    :param ID:
    :return:
    '''
    global lockedcontainers
    """
    :param ID:
    :return:
    """
    ID = int(ID)
    if ID in lockedcontainers:
        if "Lockpick" in player.inventory.get("Misc"):
            player.inventory["Misc"]["Lockpick"] -= 1
            RMV["AMMO"] = ("Lockpick")
            RMV["AMOUNT"] = 1
            s.send((json.dumps(RMV) + "#").encode())
            if player.inventory["Misc"]["Lockpick"] <= 0:
                del player.inventory["Misc"]["Lockpick"]
            l = LockpickingGame()
            l.run(ID)
        else:
            screentext.changetext("LOCKED")
    else:
        CONT["ID"] = ID
        s.send((json.dumps(CONT) + "#").encode())
        player.contID = ID
        transfer = Transfer(player)
        transfer.run()
def changemaps(id):
    '''
    Doesnt return anything in particular but essentially redefines the map class with the new maps vlaues and instances
    :param id:
    :return:
    '''
    """
    :param id:
    :return:
    """
    player.map = id
    tmx = map_dict[id][0]
    csv = map_dict[id][1]
    global map
    map = Map(tmx, csv)
    map.changemap(id)
    spawn_NPCS(id)
    time.sleep(0.7)
    for i in otherplayers:
        if i.sid != -1:
            i.kill()
            sprite_ids.remove(i.sid)

    print("CHANGED MAPS TO MAP ID",id,"\n","NPCS ON THIS LEVEL:",len(NPCS),"\n","INTERACTABLES ON THIS LEVEL:",len(map.interactables),"total enemies",len(enemysprites))
def update_camera(player):
    '''
    Render function essentially applys camera offsets fot the x.y values
    :param player:
    :return X and Y offsets for camera rendering:
    '''

    # adjust camera offset to keep player centered
    x = (screen_width // 2 - player.rect.centerx)
    y = (screen_height // 2 - player.rect.centery)

    # apply camera limits
    x = min(0, x)
    x = max(-(map.map_width - screen_width), x)
    y = min(0, y)
    y = max(-(map.map_height - screen_height), y)

    return x, y
def render(screen, map_surface, camera_x, camera_y,player):
    """
    Renders the screen using the map surface and camera offsets as well as the player instance
    Also handles drawing the onscreen set as well as drawing the equipped items.
    :param screen:
    :param map_surface:
    :param camera_x:
    :param camera_y:
    :param player:
    :return:
    """
    # Adjust player position relative to camera
    player.rect.x += camera_x
    player.rect.y += camera_y

    # Draw map surface and player
    screen.blit(map_surface, (camera_x, camera_y))
    screen.blit(player.image, player.rect)


    player.rect.x -= camera_x
    player.rect.y -= camera_y
    screentext.draw(time.time())
    screentext.changetext("")

    draw_equipped_items(screen,player)
def load_equipped(player):
    '''
    Loads the equipped items from the stored JSON file if it exists
    :param player:
    :return:
    '''
    try:
        with open("equipped_items.json", "r") as json_file:
            equipped_data = json.load(json_file)

        for slot, item in equipped_data.items():
            if slot in ["H", "C", "F"]:
                if item != {}:
                    armor_data = items.Armor.get(item)
                    if armor_data:
                        if item in player.inventory["Armor"]:
                            player.equipped[slot] = item
                            player.equipped_images[item] = pygame.image.load(constants.assetpath+armor_data[0])
                            player.statupdate()
            elif slot == "Hand":
                if item != {}:
                    weapon_data = items.Weapons.get(item)
                    if weapon_data:
                        if item in player.inventory["Weapons"]:
                            player.equipped["Hand"] = item
                            player.equipped_images[item] = pygame.image.load(constants.assetpath+weapon_data[0])
            elif slot == "Offhand":
                if item != {}:
                    consumable_data = items.Consumables.get(item)
                    if consumable_data:
                        if item in player.inventory["Consumables"]:
                            player.equipped["Offhand"] = item
                            player.equipped_images[item] = pygame.image.load(constants.assetpath+consumable_data[0])

    except FileNotFoundError:
        with open("equipped_items.json", "w") as equippeditemfile:
            equippeditemfile.write("""""{"H":"","C":"","F": "","Hand": "", "Offhand": ""}""""")
            print("Equipped items file created")
            equippeditemfile.close()
        pass

    except Exception as e:
        print(e)
        pass
def save():
    '''
    Self explanatory this is the infinite loop called by the autosave thread that simply pakcages and sends the server data on a 0.5s delay
    :return Returns nothing but coudl argue it returns a DATA pakcet to be sent to the server:
    '''
    while True:
        DATA["COMMAND"] = "GENERAL"
        DATA["X"] = (str(player.rect.x // 32))
        DATA["Y"] = (str(player.rect.y // 64))
        DATA["HP"] = str(player.hp)
        DATA["RECTX"] = str((player.rect.x))
        DATA["RECTY"] = str((player.rect.y))
        DATA["Map"] = player.map
        s.send((json.dumps(DATA) + "#").encode())
        time.sleep(0.5)

map = Map('PYGAME.tmx','test_PATHING.csv')
map_id = 0
time_factor = 1

def playerinit():
    '''
    Inital function called to create the player instance once recv server has recieved the correct info required
    Also changes maps to the correct one and calls the intro menu
    :return:
    '''
    global pmap
    global player
    try:
        time.sleep(0.3)
        player = Player(xpos * 32, ypos * 64, pmap)
        player.hp = hp
    except Exception as e:
        menu = Menu(screen)
        menu.run()
        # intro()
        player = Player(0 * 32, 0 * 64, 0)
        menu = Menu(screen)
        menu.run()
    s.send((json.dumps(INIT) + "#").encode())
    threading.Thread(target=save).start()
    changemaps(str(player.map))
    menu = Menu(screen)
    menu.run()
    main(player)

def main(player):
    '''
    Main function loop
    Handles all the main function logic and handles all of the game aspect
    :param player:
    :return Doesnt return anything its a loop:
    '''
    global fpressed
    global camera_x
    global camera_y
    pygame.init()
    """
    This is the main loop of the game
    :param player:
    :return:
    """
    running = True
    try:
        mixer.music.load('music.mp3')
        mixer.music.play()
    except:
        pass
    while running:
        cleanup()
        clock.tick(60 * time_factor)
        keys = pygame.key.get_pressed()
        player.update(keys)
        projectiles.update()
        enemysprites.update()
        otherplayers.draw(map.map_surface)
        for enemy in enemysprites.sprites():
            enemy.check_collision(player)
        for enemy in enemysprites:
            enemy.draw_health_bar(map.map_surface)
            if enemy.map != map.map_id:
                enemies.remove(enemy.ID)
                enemy.kill()
            else:
                map.map_surface.blit(enemy.image, enemy.rect)
        for npc in NPCS:
            if npc.map_id == map.map_id:
                NPCS.draw(map.map_surface)
            npc.check_collision(player,keys)
        camera_x, camera_y = update_camera(player)
        screen.fill((255, 255, 255))
        #Render The Screen At The End OF Each Run LOOP
        render(screen, map.map_surface, camera_x, camera_y,player)
        draw_health_bar(screen, player)


        #Picks up any events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                DATA["COMMAND"] = "GENERAL"
                DATA["X"] = (str(player.rect.x // 32))
                DATA["Y"] = (str(player.rect.y // 64))
                DATA["HP"] = player.hp
                DATA["RECTX"] = (player.rect.x)
                DATA["RECTY"] = (player.rect.y)
                s.send((json.dumps(DATA) + "#").encode())
                print("SAFELEY CLOSED")
                s.close()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP and event.key == pygame.K_f:
                fpressed = False



        #Draws The Map Without the Pathing Layer
        for layer in map.tmx_data.visible_layers:
            if layer.name not in ["PATHING","Objects"]:  # Skip the PATHING and object layer
                for x, y, image in layer.tiles():
                    map.map_surface.blit(image, (x * map.tmx_data.tilewidth, y * map.tmx_data.tileheight))

        pygame.display.update()
    pygame.quit()

time.sleep(2)
playerinit()


#SPRITE AND CHARACTER CREDITS TO Bethesda Softworks/Bethesda Game Studios
#INTRO VIDO SEQUENCE CREDITS TO FALLOUT 2
#SOUNDTRACK (GENERAL WASTELAND)- FALLOUT 3
#MADE BY BAILIE-PEIRCE BYRNE (5328)
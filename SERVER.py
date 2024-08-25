import socket
from imports.items import Weapons, Armor, Ammo, Consumables, Misc
import threading
import time
import json
import sqlite3
import pygame
import random
import csv
import math
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from imports import constants

#Defines the enemies as a sprite group for later reference
enemies = pygame.sprite.Group()
CLIENTLIST = []
CLIENTHISTORY = []
connected_clients = []
clientdict = {}
player_positions = {}
playermap = {}
maps = {}
conn = sqlite3.connect('database.db')

pingpacket = {"COMMAND":"PNG"}
initpacket = {"HP": '0',"X": '0',"Y": '0',"COMMAND":"INIT","map": '0'}
playerpacket = {"RECTX": "0","RECTY": "0","COMMAND":"DRAW","ID": "0"}
killplayerpacket = {"COMMAND":"KILL","ID":"-2"}
enemypacket = {"ID":"0","HP":"1","RECTX":"0","RECTY":"0","NAME":"","COMMAND":"EU","MAP":"-1"}

weaponspacket = {"COMMAND" : "WE","I":""}
armorpacket = {"COMMAND" : "AR","I":""}
ammopacket = {"COMMAND" : "AM","I":""}
consumablespacket = {"COMMAND" : "CS","I":""}
miscpacket = {"COMMAND" : "MI","I":""}

Pweaponspacket = {"COMMAND" : "PWE","I":""}
Parmorpacket = {"COMMAND" : "PAR","I":""}
Pammopacket = {"COMMAND" : "PAM","I":""}
Pconsumablespacket = {"COMMAND" : "PCS","I":""}
Pmiscpacket = {"COMMAND" : "PMI","I":""}

ContainerLocked = {"COMMAND":"LCK","ID":0}
ServerUnlock = {"COMMAND":"SULK","ID":0}
QPACKET = {"COMMAND":"QUEST","Q":0,"V":0}
QREWARD = {"COMMAND":"REWARD","ITEM":"","SNDR":"","A":0}

def read_csv_file(csv_file):
    with open(constants.mappath + csv_file, 'r') as file:
        reader = csv.reader(file)
        grid = []
        for row in reader:
            grid.append([int(cell) for cell in row])
        maps[csv_file] = grid
    return grid

read_csv_file("test_PATHING.csv")
read_csv_file("map2_PATHING.csv")
def sendenemys(id, name, rectx, recty, hp, map):
    '''
    Sends all the enemy packets to the clients to accuratley draw the enemies
    :param id:
    :param name:
    :param rectx:
    :param recty:
    :param hp:
    :param map:
    :return:
    '''
    for client in CLIENTLIST:
        client_ip = client.getpeername()[0]
        if playermap[client_ip] == map:
            enemypacket["ID"] = id
            enemypacket["NAME"] = name
            enemypacket["RECTX"] = rectx
            enemypacket["RECTY"] = recty
            enemypacket["HP"] = hp
            enemypacket["MAP"] = map
            try:
                client.send((json.dumps(enemypacket) + "#").encode())
            except ConnectionResetError: #client disconnected
                pass

class Enemy(pygame.sprite.Sprite):
    global player_positions
    def __init__(self, name, health, speed, damage, x, y, map, id,range):
        super().__init__()
        self.id = id
        self.name = name
        self.health = health
        self.speed = speed
        self.damage = damage
        self.path = []
        self.x = int(x)
        self.y = int(y)
        self.map = map
        self.mapdict = {}
        self.rect = pygame.Rect(self.x, self.y, 32, 32)
        self.dict = {}
        self.lastupd = 0
        self.alive = True
        self.grid = Grid(matrix=maps["test_PATHING.csv"])
        enemies.add(self)
        self.rect.x = x
        self.rect.y = y
        self.range = range
        self.fleeing = 0

    def check_nearest(self):
        try:
            if self.alive:
                closest_player = None
                closest_distance = None
                enemy_x = int(self.rect.x)
                enemy_y = int(self.rect.y)

                for player, position in self.dict.items():
                    px, py = map(int, position)
                    distance_squared = (enemy_x - px) ** 2 + (enemy_y - py) ** 2

                    if closest_distance is None or distance_squared < closest_distance:
                        if str(self.mapdict[player]) == str(self.map):
                            closest_player = player
                            closest_distance = distance_squared

            if closest_player is None:
                self.target = None
                self.distance = None

            if closest_player is not None:
                self.target = closest_player
                self.distance = math.sqrt(closest_distance)
                self.targetx, self.targety = map(int, self.dict[closest_player])


                if self.distance <= (350*self.range):
                    start = self.grid.node(self.rect.x // 32, self.rect.y // 32)
                    end = self.grid.node(int(self.targetx // 32), int(self.targety // 32))
                    finder = AStarFinder()
                    self.path, _ = finder.find_path(start, end, self.grid)
                    self.grid.cleanup()


                    while len(self.path) > 0:
                        self.move()
        except RuntimeError:
            pass
    def move(self):
        if time.time() - self.lastupd >= 0.05:
            next_pos = self.path[0]
            if self.rect.x // 32 < next_pos[0]:
                    self.rect.x += self.speed
                    sendenemys(self.id, self.name, self.rect.x, self.rect.y, self.health, self.map)
            elif self.rect.x // 32 > next_pos[0]:
                    self.rect.x -= self.speed
                    sendenemys(self.id, self.name, self.rect.x, self.rect.y, self.health, self.map)
            if self.rect.y // 32 < next_pos[1]:
                    self.rect.y += self.speed
                    sendenemys(self.id, self.name, self.rect.x, self.rect.y, self.health, self.map)
            elif self.rect.y // 32 > next_pos[1]:
                    self.rect.y -= self.speed
                    sendenemys(self.id, self.name, self.rect.x, self.rect.y, self.health, self.map)

            try:
                self.path.pop(0)
            except IndexError:
                pass
            self.lastupd = time.time()
    @classmethod
    def from_csv(cls, name, x, y, map):
        """
        :param name:
        :param x:
        :param y:
        :param map:
        :return: enemy
        """
        try:
            with open(constants.configpath + 'enemies.csv', 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['name'] == name:
                        max_id = max([e.id for e in enemies], default=0)
                        enemy = cls(
                            name=row['name'],
                            health=int(row['health']),
                            speed=int(row['speed']),
                            damage=int(row['damage']),
                            x=x,
                            y=y,
                            map=map,
                            id=max_id + 1,
                            range= int(row['range'])
                        )
                        print("CREATED")
                        return enemy
            return None
        except Exception as e:
            print(e)
def send_to_client(ip, client):
    '''
    Sends the inital data to the client
    :param ip:
    :param client:
    :return:
    '''
    cursor = conn.cursor()

    # Check if the IP is not present with QID = 0 and insert with COMPLETION set to 0 if not present
    cursor.execute(
        """INSERT INTO Player_Quest_Data (IP, QUEST, COMPLETION) 
           SELECT ?, Quests.QID, 0 
           FROM Quests 
           WHERE NOT EXISTS (SELECT 1 FROM Player_Quest_Data WHERE IP = ? AND QUEST = Quests.QID)""",
        (ip, ip))
    # Commit the transaction and close the database connection
    conn.commit()
    cursor.execute("SELECT * FROM Players WHERE IP=?", (ip,))
    result = cursor.fetchone()

    if result is None:
        initpacket["X"] = 0
        initpacket["Y"] = 0
        initpacket["HP"] = 100
        initpacket["map"] = 0
    else:
        initpacket["X"] = result[1]
        initpacket["Y"] = result[2]
        initpacket["HP"] = result[3]
        initpacket["map"] = result[6]

    client.send((json.dumps(initpacket) + "#").encode())
def draw_other_entities():
    """
    Draws other players on other clients
    :return:
    """
    global playerpacket
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    while True:
        for c in CLIENTLIST:
            client = c.getpeername()[0]
            cursor.execute("SELECT * FROM Players WHERE IP=?", (client,))
            result = cursor.fetchone()
            if result is None:
                pass
            else:
                try:
                    x = result[4]  # PLAYERRECTX column
                    y = result[5]  # PLAYERRECTY column
                    player_packet = playerpacket.copy()
                    player_packet["RECTX"] = x
                    player_packet["RECTY"] = y
                    if client in playermap.keys():
                        pass
                        #map_key = next(key for key, value in playermap.items() if value == client)
                except StopIteration:
                    pass

                    if client in clientdict.values():
                        client_id = next(key for key, value in clientdict.items() if value == client)
                        player_packet["ID"] = str(client_id)


                for c in CLIENTLIST:
                        targetip = c.getpeername()[0]
                        try:
                            if targetip != client and playermap[targetip] == playermap[client]:
                                c.send((json.dumps(player_packet) + "#").encode())
                        except KeyError: #player ip doesnt exist
                            pass
                        except ConnectionResetError: #player disconnected
                            pass
def null_check():
    '''
    Advanced function utilizing aggreagte and concatenating the entirity of the database and scraping through and rectifying null values
    :return:
    '''
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch all column names in the Players table
    cursor.execute("PRAGMA table_info(Players)")
    columns = [column[1] for column in cursor.fetchall()]

    # Iterate through each column and update null values with {}
    for column_name in columns:
        update_query = f"""
            UPDATE Players
            SET {column_name} = '{{}}'
            WHERE {column_name} IS NULL
        """
        cursor.execute(update_query)

    cursor.execute("PRAGMA table_info(Quests)")
    columns = [column[1] for column in cursor.fetchall()]
    for column_name in columns:
        update_query = f"""
                    UPDATE Quests
                    SET {column_name} = '{0}'
                    WHERE {column_name} IS NULL
                """
        cursor.execute(update_query)
    # Commit the changes and close the database connection
    conn.commit()
    conn.close()
def quest_update(ip, QID, stage):
    '''
    Updated the database with the new completion stage of quests when a player acheieves one.
    :param ip:
    :param QID:
    :param stage:
    :return:
    '''
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

            # Use placeholders (?) for the values to be updated
        cursor.execute('UPDATE Player_Quest_Data SET IP = ?, QUEST = ?, COMPLETION = ? WHERE IP = ? AND QUEST = ?',
                           (ip, QID, stage, ip,QID))

            # Commit the changes
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error:", e)
def updateinventory(client):
    '''
    Resends all clients their inventorys to update the clients as much as possible without exausting the server connection.
    :param client:
    :return:
    '''
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Players WHERE IP=?", (client.getpeername()[0],))
    result = cursor.fetchone()
    try:
        Pweaponspacket["I"] = result[7]
        Parmorpacket["I"] = result[8]
        Pammopacket["I"] = result[9]
        Pconsumablespacket["I"] = result[10]
        Pmiscpacket["I"] = result[11]

        client.send((json.dumps(Pweaponspacket) + "#").encode())
        client.send((json.dumps(Parmorpacket) + "#").encode())
        client.send((json.dumps(Pammopacket) + "#").encode())
        client.send((json.dumps(Pconsumablespacket) + "#").encode())
        client.send((json.dumps(Pmiscpacket) + "#").encode())

        cursor.execute('SELECT QUEST, COMPLETION FROM Player_Quest_Data WHERE IP = ?', (client.getpeername()[0],))
        records = cursor.fetchall()

        for record in records:
            QPACKET["Q"] = record[0]
            QPACKET["V"] = record[1]
            client.send((json.dumps(QPACKET) + "#").encode())

        cursor.execute('SELECT ID FROM Containers WHERE Locked = 1')
        records = cursor.fetchall()

        for record in records:
            ContainerLocked["ID"] = record[0]
            client.send((json.dumps(ContainerLocked) + "#").encode())


    except:
        pass
    conn.close()
def remove_item(ip, item_name, amount_to_remove):
    '''
    Removes items from inventorys
    :param ip:
    :param item_name:
    :param amount_to_remove:
    :return:
    '''
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve the current row for the specified IP
        cursor.execute("SELECT Weapons, Armor, Ammo, Consumables, Misc FROM Players WHERE IP = ?", (ip,))
        player_data = cursor.fetchone()

        if player_data is not None:
            weapons, armor, ammo, consumables, misc = player_data

            # Convert the fields from JSON to Python dictionaries
            weapons = json.loads(weapons) if weapons else {}
            armor = json.loads(armor) if armor else {}
            ammo = json.loads(ammo) if ammo else {}
            consumables = json.loads(consumables) if consumables else {}
            misc = json.loads(misc) if misc else {}

            # Check if the item exists in any of the fields and update its amount
            fields = {'Weapons': weapons, 'Armor': armor, 'Ammo': ammo, 'Consumables': consumables, 'Misc': misc}
            for field_name, field_data in fields.items():
                if item_name in field_data:
                    current_amount = field_data[item_name]
                    if current_amount >= amount_to_remove:
                        field_data[item_name] -= amount_to_remove
                        if field_data[item_name] == 0:
                            del field_data[item_name]  # Delete the key if the new value is 0
                    else:
                        print(f"Insufficient {item_name} in {field_name} for IP '{ip}'.")
                        remove_item(ip,item_name,current_amount)
                        return

                        # Stop checking other fields once the item is found and updated

            # Convert the modified dictionaries back to JSON
            weapons_json = json.dumps(weapons)
            armor_json = json.dumps(armor)
            ammo_json = json.dumps(ammo)
            consumables_json = json.dumps(consumables)
            misc_json = json.dumps(misc)

            # Update the database with the new field values
            cursor.execute("UPDATE Players SET Weapons = ?, Armor = ?, Ammo = ?, Consumables = ?, Misc = ? WHERE IP = ?",
                           (weapons_json, armor_json, ammo_json, consumables_json, misc_json, ip))
            conn.commit()
            print(f"Removed {amount_to_remove} {item_name}(s) from the player's inventory for IP '{ip}'.")

        else:
            print(f"Player with IP '{ip}' not found in the database.")

    except sqlite3.Error as e:
        print("SQLite error:", e)

    finally:
        # Close the database connection
        if conn:
            conn.close()
def add_item(ip, item_name, amount_to_add, field_name):
    '''
    Opposite of remove , instead adds items to speicidied fields
    :param ip:
    :param item_name:
    :param amount_to_add:
    :param field_name:
    :return:
    '''
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve the current row for the specified IP
        cursor.execute("SELECT " + field_name + " FROM Players WHERE IP = ?", (ip,))
        player_data = cursor.fetchone()

        if player_data is not None:
            field_data = player_data[0]
            item_dictionary = json.loads(field_data) if field_data else {}

            if item_name in item_dictionary:
                item_dictionary[item_name] += amount_to_add
            else:
                item_dictionary[item_name] = amount_to_add

            # Convert the modified dictionary back to JSON
            updated_field_json = json.dumps(item_dictionary)

            # Update the database with the new field value
            cursor.execute("UPDATE Players SET " + field_name + " = ? WHERE IP = ?", (updated_field_json, ip))
            conn.commit()
            print(f"Added {amount_to_add} {item_name}(s) to the player's inventory for IP '{ip}' in the {field_name} field.")

        else:
            print(f"Player with IP '{ip}' not found in the database.")

    except sqlite3.Error as e:
        print("SQLite error:", e)

    finally:
        # Close the database connection
        if conn:
            conn.close()
def update_db(client):
    #main packet handler
    """
    Major function handling all of the packets into the server, these are threads created for each client so each client has their own function stack for improved efficiency.
    :param client:
    :return:
    """
    global player_positions
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    while True:
        try:
            data = client.recv(2048)
        except ConnectionResetError:
            ping_client(client)
            return
        if not data:
            continue
        data_list = data.decode().split("#")
        for msg_str in data_list:
            if msg_str != "":
                try:
                    msg = json.loads(msg_str)
                except:
                    pass
                try:
                    if msg["COMMAND"] == "INITINV":
                        updateinventory(client)
                    if msg["COMMAND"] == "GENERAL":
                        ip = msg["IP"]
                        x = msg["X"]
                        y = msg["Y"]
                        hp = msg["HP"]
                        rectx = msg["RECTX"]
                        recty = msg["RECTY"]
                        map = msg["Map"]
                        cursor.execute("SELECT * FROM Players WHERE IP=?", (ip,))
                        result = cursor.fetchone()
                        player_positions[ip] = (rectx, recty)
                        playermap[ip] = map
                        if result is None:
                            cursor.execute("INSERT INTO Players (IP, X, Y, HP, PLAYERRECTX, PLAYERRECTY, 'Map') VALUES (?, ?, ?, ?, ?, ?, ?)", (ip, x, y, hp, rectx, recty, map))
                            conn.commit()
                            null_check()
                        else:
                            cursor.execute("UPDATE Players SET X=?, Y=?, HP=?, PLAYERRECTX=?, PLAYERRECTY=? , 'Map'=? WHERE IP=?", (x, y, hp, rectx, recty, map ,ip))
                            conn.commit()

                        #for client in client list - if client != conn then send the packet to client
                    if msg["COMMAND"] == "RMV":
                        remove_item(client.getpeername()[0],msg["AMMO"],msg["AMOUNT"])
                    if msg["COMMAND"] == "EH": #Enemy Hit
                        eid = msg["ID"]
                        dmg = msg["DMG"]
                        for enemy in enemies:
                            if enemy.id == eid:
                                enemy.health -= dmg
                                try:
                                     enemy.targetx = int(player_positions[(client.getpeername()[0])][0])
                                     enemy.targety = int(player_positions[(client.getpeername()[0])][1])
                                     enemy.distance = 0
                                except Exception as e:
                                    print (e)
                                if enemy.health <= 0:
                                    enemy.alive = False
                                    sendenemys(enemy.id,enemy.name, enemy.rect.x,enemy.rect.y, enemy.health,enemy.map)
                                    enemies.remove(enemy)
                                    amount = random.randint(5,100)
                                    add_item(client.getpeername()[0],"Cap(s)",amount,"Misc")
                                    QREWARD["ITEM"] = "Cap(s)"
                                    QREWARD["A"] = amount
                                    QREWARD["SNDR"] = enemy.name
                                    client.send((json.dumps(QREWARD) + "#").encode())
                                    updateinventory(client)
                        if eid not in enemies:
                            sendenemys(eid, 0, 0, 0, 0, 0)
                    if msg["COMMAND"] == "OC":# OPEN CONTAINER
                        ContID = msg["ID"]#GET CONTAINER ID FROM REQUEST
                        locked = False
                        cursor.execute("SELECT ID FROM Containers WHERE ID = ? AND Locked = 1",(ContID,))

                        if cursor.fetchone() != None: #Checks if container is locked
                            locked = True

                        query = "SELECT Weapons, Armor, Ammo, Consumables, Misc FROM Containers WHERE ID = ?" #GET CONTENT FROM DB
                        cursor.execute(query, (ContID,))
                        container_data = cursor.fetchone()

                        #SERIALIZE THE DATA INTO JSON DICTIONARIES FOR SENDING

                        weapons = container_data[0]
                        armor = container_data[1]
                        ammo = container_data[2]
                        consumables = container_data[3]
                        misc = container_data[4]

                        weaponspacket["I"] = weapons
                        armorpacket["I"] = armor
                        ammopacket["I"] = ammo
                        consumablespacket["I"] = consumables
                        miscpacket["I"] = misc

                            #SEND PACKETS INDIVIDUALLY TO REDUCE CHANCE OF BUFFER OVERFLOW ON CLIENT
                        client.send((json.dumps(weaponspacket) + "#").encode())
                        client.send((json.dumps(armorpacket) + "#").encode())
                        client.send((json.dumps(ammopacket) + "#").encode())
                        client.send((json.dumps(consumablespacket) + "#").encode())
                        client.send((json.dumps(miscpacket) + "#").encode())
# ADD THE SQL NULL CHECKS HERE AT THE START OF THE FC AND TC CHECKS.
                    if msg["COMMAND"] == "TC":
                        ContID = msg["ID"]
                        Tab = msg["TAB"]
                        Item = msg["Item"]
                        Amount = int(msg["A"])  # Convert amount to an integer
                        client_ip = client.getpeername()[0]
                        # Fetch container data
                        container_query = f"SELECT {Tab} FROM Containers WHERE ID = ?"
                        cursor.execute(container_query, (ContID,))
                        container_data = json.loads(cursor.fetchone()[0])

                        # Fetch player's inventory data
                        player_query = f"SELECT {Tab} FROM Players WHERE IP = ?"
                        cursor.execute(player_query, (client_ip,))
                        fetch_result = cursor.fetchone()
                        if fetch_result is not None:
                            player_data = json.loads(fetch_result[0])
                        else:
                            player_data = {}

                        # Check if the item exists in player's inventory and if there's enough
                        if Item in player_data and player_data[Item] >= Amount:
                            # Update container data
                            if Item in container_data:
                                container_data[Item] += Amount
                            else:
                                container_data[Item] = Amount

                            # Update player's inventory data
                            player_data[Item] -= Amount

                            # Remove item from player's inventory and container if its amount becomes zero
                            if container_data[Item] <= 0:
                                del container_data[Item]

                            if player_data[Item] <= 0:
                                del player_data[Item]

                            # Update container data in the database
                            container_query = f"UPDATE Containers SET {Tab} = ? WHERE ID = ?"
                            updated_container = json.dumps(container_data)
                            cursor.execute(container_query, (updated_container, ContID))

                            # Update player's inventory data in the database
                            player_query = f"UPDATE Players SET {Tab} = ? WHERE IP = ?"
                            updated_inventory = json.dumps(player_data)
                            cursor.execute(player_query, (updated_inventory, client_ip))

                            # Commit changes
                            conn.commit()
                        else:
                            print("Item not found in player's inventory or insufficient amount.")
                    if msg["COMMAND"] == "FC":
                        ContID = msg["ID"]
                        Tab = msg["TAB"]
                        Item = msg["Item"]
                        Amount = int(msg["A"])  # Convert amount to an integer
                        client_ip = client.getpeername()[0]

                        # Fetch container data
                        container_query = f"SELECT {Tab} FROM Containers WHERE ID = ?"
                        cursor.execute(container_query, (ContID,))
                        container_data = json.loads(cursor.fetchone()[0])

                        # Fetch player's inventory data
                        player_query = f"SELECT {Tab} FROM Players WHERE IP = ?"
                        cursor.execute(player_query, (client_ip,))
                        fetch_result = cursor.fetchone()
                        if fetch_result is not None:
                            player_data = json.loads(fetch_result[0])
                        else:
                            player_data = {}

                        # Check if the item exists in container and if there's enough
                        if Item in container_data and container_data[Item] >= Amount:
                            # Update player's inventory data
                            if Item in player_data:
                                player_data[Item] += Amount
                            else:
                                player_data[Item] = Amount

                            # Update container data
                            container_data[Item] -= Amount

                            # Remove item from player's inventory and container if its amount becomes zero
                            if container_data[Item] <= 0:
                                del container_data[Item]

                            if player_data[Item] <= 0:
                                del player_data[Item]

                            # Update player's inventory data in the database
                            player_query = f"UPDATE Players SET {Tab} = ? WHERE IP = ?"
                            updated_inventory = json.dumps(player_data)
                            cursor.execute(player_query, (updated_inventory, client_ip))

                            # Update container data in the database
                            container_query = f"UPDATE Containers SET {Tab} = ? WHERE ID = ?"
                            updated_container = json.dumps(container_data)
                            cursor.execute(container_query, (updated_container, ContID))

                            # Commit changes
                            conn.commit()
                        else:
                            print("Item not found in container or insufficient amount.")
                    if msg["COMMAND"] == "QU":
                        print("TRYING QUEST UPDATE")
                        quest_update(client.getpeername()[0],int(msg["ID"]),int(msg["VALUE"]))
                        if int(msg["ID"]) == 0 and int(msg["VALUE"]) == 1:
                            remove_item(client.getpeername()[0],"Key",1)
                            print("Item Removed")
                            add_item(client.getpeername()[0],"Medkit",3,"Consumables")
                            QREWARD["ITEM"] = "Medkit"
                            QREWARD["A"] = 3
                            QREWARD["SNDR"] = "Tony"
                            client.send((json.dumps(QREWARD) + "#").encode())
                            updateinventory(client)
                        if int(msg["ID"]) == 999 and int(msg["VALUE"]) == 1:
                            add_item(client.getpeername()[0],"Trophy",1,"Misc")
                            QREWARD["ITEM"] = "Trophy"
                            QREWARD["A"] = 1
                            QREWARD["SNDR"] = "Shade"
                            client.send((json.dumps(QREWARD) + "#").encode())
                            updateinventory(client)
                        if int(msg["ID"]) == 1 and int(msg["VALUE"]) == 1:
                            remove_item(client.getpeername()[0], "Machete", 1)
                            add_item(client.getpeername()[0], "Shotgun", 1, "Weapons")
                            add_item(client.getpeername()[0], "Shotgun Shells", 25, "Ammo")
                            QREWARD["ITEM"] = "Shotgun and Shells"
                            QREWARD["A"] = 1
                            QREWARD["SNDR"] = "Wrangler"
                            client.send((json.dumps(QREWARD) + "#").encode())
                            updateinventory(client)
                    if msg["COMMAND"] == "ULK":
                        cursor.execute("UPDATE Containers SET Locked = 0 WHERE ID = ?", (int(msg["ID"]),))
                        conn.commit()
                        updateinventory(client)
                        for client in CLIENTLIST:
                            client.send((json.dumps(ServerUnlock) + "#").encode())
                except ConnectionResetError:
                    ping_client(client)
                    return
def ping_client(client):
    """
    Attempts to send ping packet to client if unsuccsesful removes client from connected clients and kills their player sprite
    :param client,, type is socket connection:
    :return:
    """
    try:
        client.send((json.dumps(pingpacket)+"#").encode())
    except:
        print(client.getpeername()[0]," Disconnected")
        try:
            CLIENTLIST.remove(client)
            player_positions.pop(client.getpeername()[0])
            connected_clients.remove(client.getpeername()[0])
        except ValueError:
            #client has already been removed from conneections lists
            pass
        except KeyError:
            pass
        killplayerpacket["ID"] = (list(clientdict.keys())[list(clientdict.values()).index(client.getpeername()[0])])
        print("KILLING SPRITE ", (list(clientdict.keys())[list(clientdict.values()).index(client.getpeername()[0])]))
        try:
            for client in CLIENTLIST:
                client.send((json.dumps(killplayerpacket)+"#").encode())
            killplayerpacket["ID"] = "-2"
        except:
            pass
    return
def manage_connections():
    """
    Calls the ping_client string
    Handles Pinging connected socket connections to ensure their availbility if not removes them from the Connected client string
    :return:
    """
    while True:
        global CLIENTLIST
        for client in CLIENTLIST:
            ping_client(client)
        time.sleep(5)
def enemyhandler():
    '''
    Thread used to continously update and handle all enemy instances
    :return:
    '''
    ForceEnemyUpdate = 0
    while True:
        global enemies
        for e in enemies:
            if e.alive:
                e.dict = player_positions
                e.mapdict = playermap
                if time.time() - ForceEnemyUpdate >= 0.5:
                    try:
                        sendenemys(e.id, e.name, e.rect.x, e.rect.y, e.health, e.map)
                    except KeyError:
                        pass
                    ForceEnemyUpdate = time.time()
                e.check_nearest()
            else:
                pass
def spawn_enemies():
    '''
    Spawns all enemies
    :return:
    '''
    with open(constants.configpath + 'enemyspawns.csv', 'r') as file:
        reader = csv.DictReader(file)
        # Loop through each row in the file
        for row in reader:
            mapid = str(row["mapID"])
            name = str(row["name"])
            rectx = int(row['rectx'])
            recty = int(row['recty'])
            Enemy.from_csv(name,rectx,recty,mapid)
            print("active threads ", threading.active_count())


        # Return None if we couldn't find an enemy with the given name
        return None
def saturatecontainers():
    '''
    Saturates containers using hardcoded values and random spontaneity
    Some items are black listed
    :return:
    '''
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Access the Containers table
    cursor.execute("SELECT ID, Weapons, Armor, Ammo, Consumables, Misc FROM Containers")
    containers_data = cursor.fetchall()

    # Create a dictionary to map category names to the corresponding item dictionaries
    categories = {
        "Weapons": Weapons,
        "Armor": Armor,
        "Ammo": Ammo,
        "Consumables": Consumables,
        "Misc": Misc
    }

    # Customize the quantity ranges for different item categories
    def get_quantity_range(category, container_id):
        range = quantity_ranges.get(category)
        if container_id == 0:
            return range
        else:
            return (range[0], range[1] * container_id)

    quantity_ranges = {
        "Weapons": (1, 1),
        "Ammo": (5, 15),
        "Armor": (1,1),
        "Consumables": (1, 2),
        "Misc": (1, 2)
    }

    # Iterate through container data and update the item dictionary
    for container_data in containers_data:
        container_id = container_data[0]
        category_data = container_data[1:]

        for category, item_data_json in zip(categories.keys(), category_data):
            if item_data_json:
                item_data = json.loads(item_data_json)

                item_dict = categories.get(category)

                if item_dict is not None: #Black list items from occuring naturally here
                    if category == "Ammo" and None in item_dict:
                        item_dict.pop(None)
                    if category == "Misc" and "Trophy" in item_dict:
                        item_dict.pop("Trophy")

                    # Choose a random item from the category
                    random_item = random.choice([item for item in item_dict.keys() if item != "None"])

                    # Randomly select a quantity based on the customized range
                    min_quantity, max_quantity = get_quantity_range(category, container_id)
                    random_quantity = random.randint(min_quantity, max_quantity)

                    # Check if the item exists in the container's item dictionary
                    if random_item in item_data:
                        item_data[random_item] += random_quantity
                    else:
                        item_data[random_item] = random_quantity

                    # Update the container's corresponding column with the updated item dictionary
                    updated_item_data_json = json.dumps(item_data)
                    cursor.execute(f"UPDATE Containers SET {category} = ? WHERE ID = ?",
                                   (updated_item_data_json, container_id))


    # Commit the changes and close the connection
    conn.commit()
    conn.close()
def lockcontainers():
    '''
    Randomly locks containers based on their ID so earlier containers are less likeley to be locked
    :return:
    '''
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Access the Containers table
    cursor.execute("SELECT ID FROM Containers WHERE ID != 0")
    container_ids = [row[0] for row in cursor.fetchall()]

    for container_id in container_ids:
        # Determine the lock status based on the container ID
        lock_chance = container_id * 10  # ID0 is always unlocked, ID1 is 10% chance

        if lock_chance > 75 :
            lock_chance = 75

        # Generate a random number between 1 and 100
        random_number = random.randint(1, 100)

        if random_number <= lock_chance:
            # Set the container as locked (1) if the random number is less than or equal to the lock chance
            cursor.execute("UPDATE Containers SET Locked = 1 WHERE ID = ?", (container_id,))
        else:
            # Set the container as unlocked (0) otherwise
            cursor.execute("UPDATE Containers SET Locked = 0 WHERE ID = ?", (container_id,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

saturatecontainers()
lockcontainers()
#MAin block to accept connections and add IPs and CONN_SOCKS to the correct lists.
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.bind((constants.IP_ADDRESS,constants.PORT))
    s.listen()
    print("Server is listening....")
    lock = threading.Lock()
    threading.Thread(target=manage_connections, args=()).start()
    threading.Thread(target=draw_other_entities, args=()).start()
    spawn_enemies()
    threading.Thread(target=enemyhandler, args=()).start()

    while True:
        conn_sock, address = s.accept()
        print(f"Client {address[0]} connected")
        send_to_client(address[0],conn_sock)
        null_check()
        if address[0] not in connected_clients:
            CLIENTLIST.append(conn_sock)
            connected_clients.append(address[0])
            CLIENTHISTORY.append(address[0])
            for c, key in enumerate(CLIENTHISTORY):
                clientdict[c] = key
            null_check()
        threading.Thread(target=update_db, args=(conn_sock,)).start()

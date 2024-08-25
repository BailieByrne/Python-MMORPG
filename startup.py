import os
import sqlite3
import pip
pip.main(['install', 'pytmx==3.31'])


def create_tables():
    # Check if the database file exists
    if os.path.isfile("database.db"):
        print("Database file exists.")
        # Connect to the database
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()

            # Check if the Players table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Players'")
            if cursor.fetchone():
                print("Players table successfully verified.")
            else:
                # Create the Players table
                cursor.execute("""
                    CREATE TABLE Players (
                        IP TEXT,
                        X INT,
                        Y INT,
                        HP INT,
                        PLAYERRECTX INT,
                        PLAYERRECTY INT,
                        Map TEXT,
                        Weapons TEXT,
                        Armor TEXT,
                        Ammo TEXT,
                        Consumables TEXT,
                        Misc TEXT
                    )
                """)
                print("Players table created.")

            # Check if the Containers table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Containers'")
            if cursor.fetchone():
                print("Containers table successfully verified.")
            else:
                # Create the Containers table
                cursor.execute("""
                    CREATE TABLE Containers (
                        ID INTEGER PRIMARY KEY,
                        Weapons TEXT NOT NULL,
                        Armor TEXT NOT NULL,
                        Ammo TEXT NOT NULL,
                        Consumables TEXT NOT NULL,
                        Misc TEXT NOT NULL,
                        Locked INTEGER
                    )
                """)
                print("Containers table created.")

                # Insert 10 entries with IDs from 0 to 10 with blank inventory spaces.
                entries = [(i,"{}","{}","{}","{}","{}", 0) for i in range(11)]
                cursor.executemany("INSERT INTO Containers (ID, Weapons, Armor, Ammo, Consumables, Misc, Locked) VALUES (?, ?, ?, ?, ?, ?, ?)",entries)
                print("Inserted 10 entries with IDs from 0 to 10 and default values.")

            # Check if the Quests table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Quests'")
            if cursor.fetchone():
                print("Quests table successfully verified.")
            else:
                # Create the Quests table
                cursor.execute("""
                    CREATE TABLE Quests (
                        QID INTEGER,
                        MAX INTEGER
                    )
                """)
                entries = [(i,0) for i in range(5)]
                cursor.executemany("INSERT INTO Quests (QID, MAX) VALUES (?, ?)",entries) # add all the quests ids
                cursor.execute("INSERT INTO Quests (QID, MAX) VALUES (999, 1)") #add the final quest

                print("Quests table created.")

            # Check if the Player_Quest_Data table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Player_Quest_Data'")
            if cursor.fetchone():
                print("Player_Quest_Data table successfully verified.")
            else:
                # Create the Player_Quest_Data table
                cursor.execute("""
                    CREATE TABLE Player_Quest_Data (
                        IP INTEGER NOT NULL,
                        QUEST INTEGER,
                        COMPLETION INTEGER
                    )
                """)
                print("Player_Quest_Data table created.")

            # Check if the login_info table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login_info'")
            if cursor.fetchone():
                print("login_info table successfully verified.")
            else:
                # Create the login_info table
                cursor.execute("""
                    CREATE TABLE login_info (
                        IP INTEGER,
                        Username TEXT,
                        Password TEXT
                    )
                """)
                print("login_info table created.")

            print("Tables checked and created if necessary.")
            print("Database Operational.")

    else:
        print("Database file does not exist.")
        with open("database.db", "w") as database_file:
            print("Database file created.")
            database_file.close()
        create_tables()


create_tables()

#Self explanatory try except catch to attempt to host a server and provide an error to the user.
try:
    exec(open('SERVER.py').read())
except:
    print("Server File not found and or is damaged please ensure SERVER.py is present in the same directory as this file")
    print("Or try Reinstalling the SERVER.py")
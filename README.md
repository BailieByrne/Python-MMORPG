# Wild Wasteland

A Python multiplayer MMORPG built as my College NEA project to push my skills in object-oriented programming, threading, networking, and algorithms.

## Overview

Wild Wasteland is a top-down multiplayer RPG set in a wasteland survival world. Players can explore maps, fight enemies, interact with NPCs, open containers, complete quests, and manage inventories through a client-server architecture.

The project was originally developed as part of my AQA Computer Science NEA and achieved 90%.

## Features

- Multiplayer client-server architecture using Python sockets.
- Real-time player, enemy, and quest state synchronisation.
- Threaded server logic for handling connections, enemies, and updates concurrently.
- Pathfinding-based enemy movement using A* search.
- Inventory system with weapons, armour, ammo, consumables, and misc items.
- Quest progression and reward handling.
- Locked and unlockable containers with loot tables.
- TMX map support for tiled world layouts.
- Pygame-based 2D rendering and UI.

## Tech Stack

- Python
- Pygame
- Socket programming
- SQLite
- CSV / JSON data handling
- A* pathfinding
- Object-oriented programming
- Multithreading

## What I Learned

This project helped me strengthen my understanding of:

- Networking and packet-based communication.
- Concurrent programming with threads.
- Game state synchronisation.
- Data persistence with SQLite.
- Algorithm implementation and systems thinking.
- Structuring a larger codebase across client/server components.

## Project Status

This is a completed school project and is no longer actively developed, but I still view it as an important early project that taught me a lot about building and debugging non-trivial software systems.

## Screenshots

![alt text](https://github.com/BailieByrne/Python-MMORPG/blob/main/SS1.png "Collision Boxes")


![alt text](https://github.com/BailieByrne/Python-MMORPG/blob/main/SS2.png "Environment")

## Requirements

### Python packages
- pygame
- pathfinding
- pytmx

### Standard library modules
The rest of the imports are included with Python.

## Running the Project

1. Install dependencies.
2. Configure the server IP / constants in the constants file.
3. Start the server.
4. Launch the client.

## Notes

This project was written during college and the codebase reflects that. While the structure is rough in places, it was a valuable learning experience and a strong step toward larger software projects.

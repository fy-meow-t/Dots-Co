# Dots-Co
Puzzle game Dots &amp; Co: first-year python assignment

# Run the game
Version 1.9.3 of pygame has been used. Install the pygame module with pip using the
command:
pip3 install pygame
(may need to set "export DISPLAY=:0.0" first)
Run the game with "python3 main.py"

# Basic Instructions

Connect horizontally or vertically adjacent same-colour dots to gain scores until reaching the objectives at the top right corner. Note that there are limited moves - remaining moves are shown at the top left corner.

You may enter your player name upon starting the game. Simple login and score ranking data are stored in the local text file.

Connect dots in a loop (i.e. connect back to the first dot) to delete all dots with the same colour.

Two play modes:
1. With Companion (Eskimo avatar): 
  Throw swirl dots every time an interval is reached. Swirl dots can change adjacent dots' colours.
  Turtle hurdle: cannot be connected. Disappear after a few adjacent dots are connected.
2. Without companion: no special dots

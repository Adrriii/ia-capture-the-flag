from domain.Map import Map
from domain.GameObject.Block import *
from domain.GameObject.Flag import Flag
from random import *

class RegularMap(Map):

    def __init__(self, mapData):
        self.blockHeight = mapData["blockHeight"]
        self.blockWidth = mapData["blockWidth"]
        self.height = mapData["height"]
        self.width = mapData["width"]
        self.blocks = mapData["blocks"]
        self._flags = mapData["flags"]
        self._spawns = mapData["spawns"]
        self._bots = list()

    @staticmethod
    def loadMapData(filename):

        # To use for the 'mapData' parameter in constructor
        data = {
            "height": None,         # Real height (set by model)
            "width": None,          # Real width (set by model)
            "blockHeight": None,    # The height of the map in blocks
            "blockWidth": None,     # The width of the map in blocks
            "blocks": None,         # A two dimensionnal array for storing blocks
            "flags": None,          # The flags for each team to obtain
            "spawns": None,         # Remember the spawn locations for each team
        }

        # The format character for each tile and it's constructor call
        blocks = {
            '#': 'Wall()',
            '-': 'WallTransparent()',
            ' ': 'Empty()',
            '1': 'Spawn(1)',
            '2': 'Spawn(2)'
        }

        data["spawns"] = { 1: [], 2: [] } # Spawn blocks for each team

        with open(filename, "r") as file:
            lines = file.readlines()

            mapDefinitionLines = 2 # The amount of lines before the map tiling

            data["blockWidth"] = int(lines[0].split(":")[1])
            data["blockHeight"] = int(lines[1].split(":")[1])

            data["height"] = data["blockHeight"] * Map.BLOCKSIZE
            data["width"] = data["blockWidth"] * Map.BLOCKSIZE

            # The file lines that contains the map tiling
            # Used to fill 'data["blocks"]' according to 'blocks'
            mapLines = lines[mapDefinitionLines : data["blockHeight"] + mapDefinitionLines]

            data["blocks"] = [[None for i in range(data["blockHeight"])] for i in range(data["blockWidth"])]

            for y in range(data["blockHeight"]):
                for x in range(data["blockWidth"]):
                    if mapLines[y][x] not in blocks.keys():
                        continue

                    # See definition of 'blocks' for explanation
                    data["blocks"][x][y] = eval(blocks[mapLines[y][x]])

                    # Game Objects know their location
                    data["blocks"][x][y].x = x * Map.BLOCKSIZE # Position is top-left
                    data["blocks"][x][y].y = y * Map.BLOCKSIZE

                    if(type(data["blocks"][x][y]).__name__ == "Spawn"):
                        # If this is a spawn block, add it to it's team's spawn blocks
                        data["spawns"][data["blocks"][x][y].team].append(data["blocks"][x][y]) 

            data["flags"] = list()

            # Read the remaining info in the file
            # starts after the map tiling
            for line in lines[data["blockHeight"] + mapDefinitionLines :]:
                # Get the attribute and it's value without '\n' (:-1)
                attributes = line[:-1].split(':')

                # flag: team, blockX, blockY
                if attributes[0] == "flag":
                    info = attributes[1].split(',')

                    # Create the new flag while converting the block X and Y to real coordinates
                    data["flags"].append(Flag(int(info[0]), int(info[1] * Map.BLOCKSIZE), int(info[2] * Map.BLOCKSIZE)))

                    continue

        return data

    def GetRandomPositionInSpawn(self, team):
        return Map.GetRandomPositionInBlock(choice(self._spawns[team]))
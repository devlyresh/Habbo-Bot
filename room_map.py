# room_map.py
import struct

class RoomMap:
    """
    Represents the logical grid of a Habbo Room.
    
    This class combines data from two specific packets to build a complete picture
    of where a bot can walk:
    1. FloorHeightMap (Packet 590): Provides visual walls ('x') and room dimensions.
    2. HeightMap (Packet 3055): Provides furniture collision (blocking) and exact heights.
    
    The coordinate system is (X, Y) where (0,0) is usually the door or corner.
    """
    
    def __init__(self):
        # Grid dimensions
        self.width: int = 0
        self.height: int = 0
        
        # Derived from Packet 590 (FloorHeightMap)
        # A 2D grid of characters. 'x' = Wall/Void, Numbers/Letters = Floor Height.
        self.floor_map: list[list[str]] = []
        
        # Derived from Packet 3055 (HeightMap)
        # Exact height of the tile including furniture stack.
        self.tile_heights: list[list[float]] = []
        
        # Derived from Packet 3055 (HeightMap)
        # True if a furniture item (e.g., a plant or divider) is blocking this tile.
        self.stacking_blocked: list[list[bool]] = []
        
        # Derived from Packet 3055
        # Boolean flag indicating if this is a valid tile for the room engine.
        self.is_room_tile: list[list[bool]] = []
        
        # Legacy/Unused
        self.map = []
        
        # The calculated entry point (found by scanning for gaps in the walls)
        self.door_x: int = -1
        self.door_y: int = -1

    def is_walkable(self, x: int, y: int) -> bool:
        """
        Determines if the bot can move to the target (x, y) coordinate.
        
        Checks:
        1. Boundary Check: Is (x,y) inside the grid?
        2. Wall Check: Is the tile marked as 'x' (Void)?
        3. Furniture Check: Is there an object blocking movement?
        """
        # 1. Boundary Check
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False 
        
        # 2. Wall/Void Check (From floor_map string)
        # 'x' represents a wall or empty space in Habbo's map format.
        if self.floor_map[y][x].lower() == 'x':
            return False
        
        # 3. Furniture Collision Check
        # If a furni is placed here and is not walkable/sittable, this flag is True.
        if self.stacking_blocked[y][x]:
            return False
            
        return True

    def is_valid(self) -> bool:
        """
        Helper to check if the map has been successfully initialized/parsed.
        Used to prevent pathfinding logic from running before the room loads.
        """
        return self.width > 0 and self.height > 0

    def get_tile_height(self, x: int, y: int) -> float:
        """
        Returns the absolute Z-height of a tile.
        This includes the floor base height + any furniture stacked on top.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0.0
        return self.tile_heights[y][x]

    def get_walkable_tiles(self) -> list[tuple[int, int]]:
        """
        Scans the entire room and returns a list of all valid (X, Y) coordinates.
        
        Used primarily by the 'Random Walk' feature to ensure the bot 
        picks a valid destination.
        """
        walkable_tiles = []
        
        # Safety check: ensure maps are loaded to avoid IndexErrors
        if not self.floor_map or not self.stacking_blocked:
            return []

        for y in range(self.height):
            for x in range(self.width):
                if self.is_walkable(x, y):
                    walkable_tiles.append((x, y))
                    
        return walkable_tiles

    def __str__(self) -> str:
        """
        Debug Utility: Prints a visual ASCII representation of the room.
        Useful for debugging parser errors or verifying door location.
        """
        if not self.floor_map:
            return "Room map is not initialized."
        
        map_str = "--- Room Map ---\n"
        for y, row in enumerate(self.floor_map):
            row_str = ""
            for x, tile in enumerate(row):
                # Mark the Door location with 'D' for visibility
                char = 'D' if x == self.door_x and y == self.door_y else tile
                # Format to align grid visually
                row_str += f"{char: >3}"
            map_str += row_str + "\n"
        
        map_str += f"Dimensions: {self.width}x{self.height}, Door at ({self.door_x}, {self.door_y})"
        return map_str
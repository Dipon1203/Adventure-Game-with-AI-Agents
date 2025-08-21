from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime


search = DuckDuckGoSearchRun()
search_tool = Tool(
    name ="search",
    func=search.run,
    description="Search the web for information. Use this when asked for \
        recent information like game result, weather, game information \
        and recent releases."
)


def get_neighbor_information(query: str) -> str:
    npc_database = {
        "nancy": {
            "name": "Nancy",
            "role": "Diamond Seller",
            "location": "Mid Forest",
            "character_details": "Sells diamonds."
        },
        "albert": {
            "name": "Albert",
            "role": "Axe Seller",
            "location": "West Forest",
            "character_details": "Sells Axe."
        },
        "bob": {
            "name": "Bob - the eye",
            "role": "Know it all",
            "location": "East Forest",
            "character_details": "Knows about everything"
        },
        "amy": {
            "name": "Amy",
            "role": "Crazy physicist",
            "location": "East Forest",
            "character_details": "A mad person who talks about physics all the time"
        },
    }

    query_lower = query.lower()
    
    for npc_id, info in npc_database.items():
        if info["name"].lower() in query_lower:
            return f"Information about {info['name']}:\nRole: {info['role']}\nLocation: {info['location']}\nDetails: {info['character_details']}"
    
    if any(word in query_lower for word in ["where", "location", "find", "located"]):
        results = []
        for _, info in npc_database.items():
            results.append(f"{info['name']} ({info['role']}) is located at {info['location']}.")
        return "\n".join(results)
    
    if any(word in query_lower for word in ["sell", "buy", "shop", "merchant", "role", "job"]):
        results = []
        for _, info in npc_database.items():
            results.append(f"{info['name']} is a {info['role']} - {info['character_details']}")
        return "\n".join(results)
    
    if "diamond" in query_lower:
        for _, info in npc_database.items():
            if "diamond" in info["character_details"].lower():
                return f"{info['name']} sells diamonds. Location: {info['location']}"
                
    if "axe" in query_lower:
        for _, info in npc_database.items():
            if "axe" in info["character_details"].lower():
                return f"{info['name']} sells axes. Location: {info['location']}"
    
    if "neighbors" in query_lower:
        return f"There are {len(npc_database)} NPCs available in the forest. "


    paragraph = f"There are {len(npc_database)} NPCs available in the forest. "
    

    paragraph += f"{npc_database['nancy']['name']} is a {npc_database['nancy']['role']} located in \
        {npc_database['nancy']['location']}. Her character details indicate she \
            {npc_database['nancy']['character_details']} "
    
    paragraph += f"{npc_database['albert']['name']} is a {npc_database['albert']['role']} who can be \
        found in {npc_database['albert']['location']}. His character details show he \
            {npc_database['albert']['character_details']}"
    
    paragraph += f"{npc_database['bob']['name']} has the role of {npc_database['bob']['role']} and \
        is located in {npc_database['bob']['location']}. His character details state he \
            {npc_database['bob']['character_details']}" 
    
    paragraph += f"{npc_database['amy']['name']} is a {npc_database['amy']['role']} situated in {npc_database['amy']['location']}. \
                Her character details describe her as {npc_database['amy']['character_details']}"

    return paragraph

neighbor_tool = Tool(
    name = "get_neighbor_info",
    func = get_neighbor_information,
    description= """Provides details about other NPCs, including their names, roles, position\
                    in map, and whether they can sell things or what they sell. Use this tool when asked about \
                    nearby characters, neighbors, or if the player is looking to buy something or looking for something.
                    """
)


def get_forest_tree_information(query: str = "") -> str:
    """
    Provides information about tree distribution across all quadrants of the forest
    in a single paragraph, using actual map boundaries from the loaded area.
    """
    from core.area import area
    from components.usable import Choppable

    
    # Find all trees in the current map using the provided logic
    chopped_trees = []
    unchopped_trees = []
    
    for entity in area.entities:
        for component in entity.components:
            if isinstance(component, Choppable) and component.obj_name == "Pine Tree":
                position = (int(entity.x / 32), int(entity.y / 32)+1)  # Convert to tile coordinates
                
                if component.is_chopped:
                    chopped_trees.append(position)
                else:
                    unchopped_trees.append(position)
    

    map_width = len(area.map.tiles[0])-6  # Number of tiles horizontally
    map_height = len(area.map.tiles)-3   # Number of tiles vertically
    
    # Calculate mid-points based on actual map dimensions
    mid_x = map_width // 2
    mid_y = map_height // 2

    print(f"the map height is {map_height}")
    print(f"the map width is {map_width}")
    #print(f"Unchopped trees {unchopped_trees}") 
        
    
    # Count trees in each quadrant (both unchopped and chopped)
    ne_unchopped = sum(1 for pos in unchopped_trees if pos[0] >= mid_x and pos[1] < mid_y)
    se_unchopped = sum(1 for pos in unchopped_trees if pos[0] >= mid_x and pos[1] >= mid_y)
    nw_unchopped = sum(1 for pos in unchopped_trees if pos[0] < mid_x and pos[1] < mid_y)
    sw_unchopped = sum(1 for pos in unchopped_trees if pos[0] < mid_x and pos[1] >= mid_y)
    
    ne_chopped = sum(1 for pos in chopped_trees if pos[0] >= mid_x and pos[1] < mid_y)
    se_chopped = sum(1 for pos in chopped_trees if pos[0] >= mid_x and pos[1] >= mid_y)
    nw_chopped = sum(1 for pos in chopped_trees if pos[0] < mid_x and pos[1] < mid_y)
    sw_chopped = sum(1 for pos in chopped_trees if pos[0] < mid_x and pos[1] >= mid_y)
    
    # Calculate totals
    total_unchopped = ne_unchopped + se_unchopped + nw_unchopped + sw_unchopped
    total_chopped = ne_chopped + se_chopped + nw_chopped + sw_chopped
    
    # Find which quadrant has the most unchopped trees
    quadrant_unchopped = {
        "north-east": ne_unchopped,
        "south-east": se_unchopped,
        "north-west": nw_unchopped,
        "south-west": sw_unchopped
    }
    
    best_quadrant = max(quadrant_unchopped.items(), key=lambda x: x[1])
    
    # Create a single paragraph response with information about all quadrants
    paragraph = f"There are {total_unchopped} unchopped Pine Trees and {total_chopped} chopped Pine Trees in the forest. "
    
    # Add details about each quadrant
    paragraph += f"The northeast has {ne_unchopped} unchopped and {ne_chopped} chopped trees. "
    paragraph += f"The southeast has {se_unchopped} unchopped and {se_chopped} chopped trees. "
    paragraph += f"The northwest has {nw_unchopped} unchopped and {nw_chopped} chopped trees. "
    paragraph += f"The southwest has {sw_unchopped} unchopped and {sw_chopped} chopped trees. "
    
    # Add a recommendation based on the best quadrant
    
    if best_quadrant[1] > 0:
        paragraph += f"The {best_quadrant[0]} quadrant has the most trees with {best_quadrant[1]} unchopped trees available."
    else:
        paragraph += "There are no unchopped trees available in any quadrant."
    

    
    return paragraph


forest_tree_tool = Tool(
    name = "get_forest_tree_info",
    func = get_forest_tree_information,
    description= """Provides details about available choppable trees. Use this tool when asked about \
                    forest trees or available choppable trees.
                    """
)

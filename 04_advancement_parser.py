import json

def parse_key(key):
    """
    Parses key format: <origin>:<path>
    
    Supports both flat paths and nested paths:
      - fabric:item        → origin='fabric', item='item'
      - fabric:folder/item → origin='fabric', folder='folder', item='item'

    Returns (origin, folder, final_item, is_recipe), or None if invalid.
    """
    parts = key.split(':')
    
    # Must have exactly two parts
    if len(parts) != 2:
        print(f"❌ Invalid key format: '{key}'. Expected <origin>:<item>.")
        return None, None, None, False
    
    origin, raw_item = parts[0], parts[1]
    
    # Check for recipes vs advancements — actually based on the path, not a string check
    if "recipes/" in raw_item:
        item_path = raw_item.replace("recipes/", "").strip()
        
        if "/" not in item_path:
            folder = None
            final_item = item_path
        else:
            try:
                folder, final_item = item_path.split('/', 1)  # Only split once to avoid over-splitting
            except ValueError as e:
                print(f"❌ Failed to parse recipe path '{raw_item}': {e}")
                return None, None, None, False
        
        return origin, folder, final_item, True
    
    else:
        # Not a recipe — treat it like any advancement or item
        if "/" in raw_item:
            try:
                folder, final_item = raw_item.split('/', 1)
            except ValueError as e:
                print(f"❌ Failed to parse advancement path '{raw_item}': {e}")
                return None, None, None, False
        
        else:
            folder = None
            final_item = raw_item
            
        return origin, folder, final_item, False

# Main execution
try:
    with open('advancement_stuff/8f96643c-c1f8-4f43-b62c-58ba38b634d2.json', 'r') as file:
        data = json.load(file)
        
        datapack_recipes = {}
        datapack_advancements = {}

        for key in data.keys():
            origin, folder, item_name, is_recipe = parse_key(key)

            if origin is None or not isinstance(origin, str):
                print(f"❌ Failed to extract origin from '{key}'")
                continue

            # Store into correct container using same structure
            if is_recipe:
                # Recipe logic — same as before
                if not origin in datapack_recipes:
                    datapack_recipes[origin] = {}
                
                if folder is None:
                    datapack_recipes[origin][item_name] = data[key]
                else:
                    if not (folder in datapack_recipes[origin]):
                        datapack_recipes[origin][folder] = {}
                    datapack_recipes[origin][folder][item_name] = data[key]

            else:
                # Advancement logic — now uses same folder/item splitting as recipes
                if not origin in datapack_advancements:
                    datapack_advancements[origin] = {}
                
                if folder is None:
                    datapack_advancements[origin][item_name] = data[key]
                else:
                    if not (folder in datapack_advancements[origin]):
                        datapack_advancements[origin][folder] = {}
                    datapack_advancements[origin][folder][item_name] = data[key]

        print(f"\n✅ Datapack Recipes:\n{datapack_recipes}")
        # print(f"\n✅ Datapack Advancements:\n{datapack_advancements}")

except FileNotFoundError:
    print("❌ Error: File not found at advancement_stuff/8f96643c-c1f8-4f43-b62c-58ba38b634d2.json")
except json.JSONDecodeError as e:
    print(f"❌ JSON decoding failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error occurred: {str(e)}")


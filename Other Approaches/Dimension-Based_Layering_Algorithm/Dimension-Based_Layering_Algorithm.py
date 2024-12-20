from itertools import product
import json
import time
from datetime import datetime
from itertools import permutations, islice
from greedypacker.greedypacker import BinManager, Item

def get_valid_rotations(pkg, y_used, uld_length, max_min_dim):
    """
    Get all valid rotations that respect the max_min_dim constraint
    """
    rotations = [
        {"y": pkg['length'], "x": pkg['width'], "z": pkg['height'], "id": pkg['id']},
        {"y": pkg['length'], "x": pkg['height'], "z": pkg['width'], "id": pkg['id']},
        {"y": pkg['width'], "x": pkg['length'], "z": pkg['height'], "id": pkg['id']},
        {"y": pkg['width'], "x": pkg['height'], "z": pkg['length'], "id": pkg['id']},
        {"y": pkg['height'], "x": pkg['length'], "z": pkg['width'], "id": pkg['id']},
        {"y": pkg['height'], "x": pkg['width'], "z": pkg['length'], "id": pkg['id']}
    ]
    
    return [
        r for r in rotations
        if r['x'] + y_used <= uld_length and r['x'] <= max_min_dim
    ]


from collections import Counter

def get_dimension_frequency(packages):
    """
    Calculate the frequency of dimensions (width, height) across all packages.
    """
    dimension_freq = Counter()
    for pkg in packages:
        if pkg['height']!=pkg['length']and pkg['length']!=pkg['width']:
            dimension_freq[pkg['height']]+=1
            dimension_freq[pkg['length']]+=1
            dimension_freq[pkg['width']]+=1
        elif pkg['height']==pkg['length']and pkg['length']!=pkg['width']:
             dimension_freq[pkg['height']]+=1
             dimension_freq[pkg['width']]+=1
        else: 
            dimension_freq[pkg['width']]+=1

    return dimension_freq
 
def try_area_based_layering(packages, bin_width,bin_length):
    """Try to create a layer based on the most frequent dimensions, split into smaller layers if needed.
    """
    # Get the dimension frequency of all packages
    dimension_freq = get_dimension_frequency(packages)
    
    # Sort dimensions by frequency (highest frequency first)
    sorted_dimensions = sorted(dimension_freq.items(), key=lambda x: x[1],reverse=True )
    
    
    total_area = 0
    packed_ids = []
    
    layer_height, freq = sorted_dimensions[0]
        # Filter packages with the current dimension (width, height)
    matching_packages = [pkg for pkg in packages if pkg['width'] == layer_height or pkg['height'] == layer_height or pkg['length']==layer_height]
    matching_packages.sort(key=lambda pkg: pkg['cost'],reverse=True)
    to_packed=[]    
    for pkg in matching_packages:
            if pkg['width']==layer_height:
                pkg['width']=pkg['height']
                pkg['height']=layer_height
            if pkg['length'] ==layer_height:
                pkg['length']=pkg['height']
                pkg['height'] =layer_height
            
            total_area += pkg['width'] * pkg['length']
            to_packed.append(pkg)
             
            
    layer=[]
    item_list=[]
    if total_area >= bin_width * bin_length: 
        M = BinManager(bin_width, bin_length, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
    elif total_area >= (bin_width * bin_length)/2:
       
        M = BinManager(bin_width/2, bin_length, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
          
    elif total_area >= (bin_width * bin_length)/4:
        M = BinManager(bin_width/2, bin_length/2, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
    else:  return False, None, 0, 0, [],0,0
    # If no valid layer can be created, return False
    n=len(to_packed)
    total_max_area=0
    max_cost=0
    for i in range(0,n): 
        item_list=[]
        
        # if total_area >= bin_width * bin_length: 
        
        M = BinManager(bin_width, bin_length, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
        # elif total_area >= (bin_width * bin_length)/2:
        
        #     M = BinManager(bin_width/2, bin_length, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
            
        # elif total_area >= (bin_width * bin_length)/4:
        #     M = BinManager(bin_width/2, bin_length/2, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
        for j in range(0,i+1):
            pkg =to_packed[j]
            item_list.append(Item(pkg['length'], pkg['width'], pkg['id'],pkg['height'],pkg['cost'])) 
        M.add_items(*item_list)
        M.execute()
        area=0
        for item in M.bins[0].items:
            area+= item.width*item.height
        if area>total_max_area: 
            total_max_area= area
            packed_bin=M.bins[0]
    
    layer = [{"id": item.id, "width": item.width, "height": item.length,"length":item.height,
                "x":item.y , "y": item.x, "z":0,"cost":item.cost} for item in packed_bin.items]
    # If full layer is not created, try smaller layers
    
    packed_ids=[]
    weight =0
    cost=0
    for item in layer:
        cost+=item['cost']
        packed_ids.append(item['id'])
    count =0
    for pkg in packages:
        if pkg['id'] in packed_ids:
            if pkg['type']=='P':
                count+=1
            weight+=pkg['weight']
     
    return True,layer,weight,layer_height,packed_ids,count,cost
    
    
   

def find_Layer(packages, width, length):
    """
    Find optimal layer by layering based on the frequency of dimensions.
    """
     
    success, layer, weight, height, packed_ids,count,cost= try_area_based_layering(
        packages, width, length
    )
    
    
    if success:
        return layer, weight, height, packed_ids,count,cost
    else:
        return None,0,0,[],0,0
    



def pack_items(ULDs, Packages, K):
    packed_ULDs = {}
    
    total_cost = 0
    economy_cost = 0

    # Separate Priority and Economy Packages
    Priority_Packages = [pkg for pkg in Packages if pkg['type'] == 'P']
    Economy_Packages = [pkg for pkg in Packages if pkg['type'] == 'E']
    remaining_packages= [pkg for pkg in Packages]
    width=ULDs[0]['width']
    length= ULDs[0]['length']
    layers=[]
    while remaining_packages:
        layer, weight, height, packed_ids, count,cost = find_Layer(remaining_packages, width, length)
        if layer is None:
            break
        remaining_packages = [pkg for pkg in remaining_packages if pkg['id'] not in packed_ids]
        layers.append([layer, weight, height, packed_ids, count,cost])
    layers.sort(key=lambda layer:layer[5],reverse=True)
    def knapsack_layers(uld, layers, K):
        max_height = uld['height']
        max_weight = uld['weight_limit']
        n = len(layers)

        # DP table to track maximum packed cost for given weight and height
        dp = [[[0] * (max_weight + 1) for _ in range(max_height + 1)] for _ in range(n + 1)]
        selected_layers = [[[[] for _ in range(max_weight + 1)] for _ in range(max_height + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            layer, weight, height, packed_ids, count, cost = layers[i - 1]
            for h in range(max_height + 1):
                for w in range(max_weight + 1):
                    if height <= h and weight <= w:
                        # Include current layer if it improves the total cost
                        if dp[i - 1][h][w] <= dp[i - 1][h - height][w - weight] + cost:
                            dp[i][h][w] = dp[i - 1][h - height][w - weight] + cost
                            selected_layers[i][h][w] = selected_layers[i - 1][h - height][w - weight] + [layers[i - 1]]
                        else:
                            # Skip the layer
                            dp[i][h][w] = dp[i - 1][h][w]
                            selected_layers[i][h][w] = selected_layers[i - 1][h][w]
                    else:
                        # Skip the layer if it exceeds height or weight limits
                        dp[i][h][w] = dp[i - 1][h][w]
                        selected_layers[i][h][w] = selected_layers[i - 1][h][w]

        # Backtrack to determine the selected layers
        h, w = max_height, max_weight
        used_layers = []
        for i in range(n, 0, -1):
            if selected_layers[i][h][w] != selected_layers[i - 1][h][w]:
                used_layers.append(layers[i - 1])
                layer, weight, height, packed_ids, count, cost = layers[i - 1]
                h -= height
                w -= weight

        # Calculate total cost and assign `z` coordinate
        total_cost = 0
        current_height = 0
        for layer in used_layers:
            layer_cost = layer[5]
            total_cost += layer_cost
            for item in layer[0]:
                item['z'] = current_height
            current_height += layer[2]

        # Return the used layers, updated total cost, and remaining layers
        unused_layers = [layer for layer in layers if layer not in used_layers]
        return used_layers, total_cost, unused_layers

    
    
    # Main loop over ULDs
    for uld in ULDs:
        if uld['id'] in ["U1", "U2"]:
            continue
        
        # Solve the knapsack problem for the current ULD
        used_layers, total_cost, layers = knapsack_layers(uld, layers, K)
# Sorting the used layers based on the area (width * length) in reverse order
        used_layers.sort(key=lambda layer: sum(item['width'] *item['length'] for item in layer[0]),reverse=True)
        current_height=0
        for layer in used_layers:
            for item in layer[0]:
                item['z'] = current_height
            current_height += layer[2]

        # Assign the used layers to the current ULD
        packed_ULDs[uld['id']] = [layer[0] for layer in used_layers]

    r_ulds= [ULDs[4],ULDs[5]]
    r_packages=[]
    r_ids=[]
    for layer in layers:
        for item in layer[0]:
            r_ids.append(item['id'])
    for pkg in remaining_packages:
        r_ids.append(pkg['id'])       
    remaining_packages=[]
    for pkg in Packages:
        if pkg['id'] in r_ids and pkg['type']=='E':
            remaining_packages.append(pkg)
    
    
    layers = []
    width = ULDs[4]['width']
    length = ULDs[4]['length']
     
    # Process Priority Packages
    while remaining_packages:
        layer, weight, height, packed_ids, count,cost = find_Layer(remaining_packages, width, length)
        if layer is None:
            break
        remaining_packages = [pkg for pkg in remaining_packages if pkg['id'] not in packed_ids]
        layers.append([layer, weight, height, packed_ids, count,cost])
    layers.sort(key=lambda layer:layer[5],reverse=True)
    for uld in r_ulds:
         used_layers, total_cost, layers = knapsack_layers(uld, layers, K)
         # Sorting the used layers based on the area (width * length) in reverse order
         used_layers.sort(key=lambda layer: sum(item['width']*item['height'] for item in layer[0]),reverse=True)
         current_height=0
         for layer in used_layers:
            for item in layer[0]:
                item['z'] = current_height
            current_height += layer[2]
         
        # Assign the used layers to the current ULD
         packed_ULDs[uld['id']] = [layer[0] for layer in used_layers]
    



    # Calculate Economy Cost for Remaining Packages
    r_ids=[]
    for layer in layers:
        for item in layer[0]:
            r_ids.append(item['id'])
    for pkg in remaining_packages:
        r_ids.append(pkg['id'])       
    remaining_packages=[]
    for pkg in Packages:
        if pkg['id'] in r_ids:
            remaining_packages.append(pkg)  
    total_cost=0
    for pkg in remaining_packages:
        economy_cost += pkg['cost']
     
    total_cost += economy_cost

    return packed_ULDs, total_cost, []
  
 
def parse_input_file(file_path):
    """
    Parse input file and return structured data.
    Records parsing details in parsing_log.txt
    """
    try:
        # Initialize data structures
        ULDs = []
        Packages = []
        parsing_log = []
        
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Parse first line
        try:
            first_line = lines[0].strip()
            total_ULDs, total_packages, cost_multiplier = map(int, first_line.split(','))
            K = cost_multiplier
            parsing_log.append(f"Successfully parsed header: {total_ULDs} ULDs, {total_packages} packages, K={K}")
        except Exception as e:
            raise ValueError(f"Error parsing first line: {e}")

        # Parse ULDs
        for i in range(1, total_ULDs + 1):
            try:
                uld_line = lines[i].strip()
                uld_id, length, width, height, weight_limit = uld_line.split(',')
                ULD = {
                    "id": uld_id,
                    "length": int(length),
                    "width": int(width),
                    "height": int(height),
                    "weight_limit": int(weight_limit),
                    "volume": int(length) * int(width) * int(height)
                }
                ULDs.append(ULD)
                parsing_log.append(f"Parsed ULD {uld_id}: {length}x{width}x{height}, limit={weight_limit}")
            except Exception as e:
                raise ValueError(f"Error parsing ULD at line {i+1}: {e}")

        # Parse Packages
        for i in range(total_ULDs + 1, len(lines)):
            try:
                package_line = lines[i].strip()
                parts = package_line.split(',')
                if len(parts) < 7:
                    raise ValueError(f"Invalid package data format at line {i+1}")
                
                package_id = parts[0]
                length, width, height, weight = map(int, parts[1:5])
                pkg_type = parts[5]
                cost = int(parts[6]) if parts[6] != '-' else 0
                
                package = {
                    "id": package_id,
                    "length": length,
                    "width": width,
                    "height": height,
                    "weight": weight,
                    "type": pkg_type,
                    "cost": cost,
                    "volume": length * width * height
                }
                Packages.append(package)
                parsing_log.append(f"Parsed Package {package_id}: {length}x{width}x{height}, type={pkg_type}")
            except Exception as e:
                raise ValueError(f"Error parsing package at line {i+1}: {e}")

        # Validate counts
        if len(ULDs) != total_ULDs:
            raise ValueError(f"Expected {total_ULDs} ULDs, but found {len(ULDs)}")
        if len(Packages) != total_packages:
            raise ValueError(f"Expected {total_packages} packages, but found {len(Packages)}")

        # Save parsing log
        with open('parsing_log.txt', 'w') as f:
            f.write("\n".join(parsing_log))
            f.write(f"\nSuccessfully parsed {len(ULDs)} ULDs and {len(Packages)} packages")

        return ULDs, Packages, K

    except Exception as e:
        # Log error and re-raise
        with open('parsing_log.txt', 'w') as f:
            f.write(f"ERROR: {str(e)}")
        raise

def generate_output(K,packed_ULDs,newpacked, total_cost, ULDs, Packages, output_file="mid_output.txt", generate_summary=True):
    """
    Generate output files with detailed packing solution and summary
    """
    try:
        # Calculate statistics
        total_packages = sum(len(layer) for uld_layers in packed_ULDs.values() for layer in uld_layers) +len(newpacked)
        priority_ULD_count = sum(
            1 for uld_id, layers in packed_ULDs.items()
            if any(
                any(pkg['id'] in [item['id'] for item in layer] for pkg in Packages if pkg['type'] == 'P')
                for layer in layers
            )
        )
        
        # Prepare output lines
        output_lines = [f"{total_cost+priority_ULD_count*K},{total_packages},{priority_ULD_count}"]
        
        # Track packed packages
        packed_package_ids = set()
        
        # Generate packing details
        

        for uld_id, layers in packed_ULDs.items():
            for layer in layers:
                for item in layer:
                    # Find the corresponding package details
                    package = next(pkg for pkg in Packages if pkg['id'] == item['id'])
                    package_id = package['id']  # Remove "P-" from package ID
                    uld_id_clean = uld_id   # Remove "U" from ULD ID

                    x0, y0, z0 = item['x'], item['y'], item['z']
                    x1 = x0 + item['length']
                    y1 = y0 + item['width']
                    z1 = z0 + item['height']

                    # Format and append the output line
                    output_lines.append(
                        f"{package_id},{uld_id_clean},"
                        f"{x0},{y0},{z0},"
                        f"{x1},{y1},{z1}"
                    )
                    packed_package_ids.add(package['id'])

        # Handle newly packed packages not yet output
        for pkg in newpacked:
            if pkg['id'] not in packed_package_ids:
                package_id = pkg['id']  # Remove "P-" from package ID
                uld_id_clean = pkg['uld_id']# Remove "U" from ULD ID

                output_lines.append(
                    f"{package_id},{uld_id_clean},"
                    f"{pkg['position']['x0']},{pkg['position']['y0']},{pkg['position']['z0']},"
                    f"{pkg['position']['x1']},{pkg['position']['y1']},{pkg['position']['z1']}"
                )
                packed_package_ids.add(pkg['id'])

        # Add unpacked packages with "NONE"
        for pkg in Packages:
            if pkg['id'] not in packed_package_ids:
                package_id = pkg['id']   # Remove "P-" from package ID

                output_lines.append(f"{package_id},NONE,-1,-1,-1,-1,-1,-1")

 
        # Write main output file
        with open(output_file, "w") as f:
            f.write("\n".join(output_lines))

        # Generate summary if requested
        if generate_summary:
            summary_lines = [
                "Packing Solution Summary",
                "=" * 50,
                f"Total Cost: {total_cost+K*priority_ULD_count}",
                f"Total Packages Packed: {total_packages}",
                f"Priority ULDs Used: {priority_ULD_count}",
                f"Total ULDs Used: {len(packed_ULDs)}",
                f"Unpacked Packages: {len(Packages) - total_packages}",
                "\nPacking Details by ULD:",
                "=" * 50
            ]

            for uld_id, layers in packed_ULDs.items():
                uld = next(u for u in ULDs if u['id'] == uld_id)
                packages_in_uld = sum(len(layer) for layer in layers)
                priority_packages = sum(
                    1 for layer in layers
                    for item in layer
                    for pkg in Packages
                    if pkg['id'] == item['id'] and pkg['type'] == 'P'
                )
                
                summary_lines.extend([
                    f"\nULD {uld_id}:",
                    f"  Total Packages: {packages_in_uld}",
                    f"  Priority Packages: {priority_packages}",
                    f"  Number of Layers: {len(layers)}"
                ])

            # Write summary file
            with open("packing_summary.txt", "w") as f:
                f.write("\n".join(summary_lines))

        return True

    except Exception as e:
        # Log error
        with open("output_error.txt", "w") as f:
            f.write(f"Error generating output: {str(e)}")
        raise
 
 
 
def main():
    try:
        # Parse input
        input_file = "input.txt"
        ULDs, Packages, K = parse_input_file(input_file)
        
        # Optimize with reduced permutations
        ulds_copy = [uld.copy() for uld in ULDs]
        for uld in ulds_copy:
           volume = uld['length'] * uld['width'] * uld['height']
           uld['efficiency'] = volume #/ uld['weight_limit'] if uld['weight_limit'] > 0 else 0
        ulds_copy.sort(key=lambda x: x['efficiency'], reverse=True)
     
        # Generate output files
        packed_ULDs, total_cost, newpacked = pack_items(ulds_copy, Packages, K)
        generate_output(K,packed_ULDs,newpacked, total_cost, ulds_copy, Packages,
                        output_file="output.txt", generate_summary=True)

        print(f"\nOptimization complete. Check:")
        print("1. output.txt - for the required output format")
        print("2. packing_summary.txt - for packing statistics and analysis")
        print("3. parsing_log.txt - for input parsing details")
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        with open("error_log.txt", "w") as f:
            f.write(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    start_time =time.time()
    main()
    end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"Total execution time: {elapsed_time:.2f} seconds")

# if __name__ == "__main__":
#     main()

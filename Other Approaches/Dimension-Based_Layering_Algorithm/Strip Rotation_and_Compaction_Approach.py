from itertools import product
import json
import time
from datetime import datetime
from itertools import permutations, islice
from greedypacker.greedypacker import BinManager, Item
def get_max_min_dimension(packages, window_size):
    """
    Find the maximum of minimum dimensions among all packages in the window
    """
    max_min = 0
    for pkg in packages[:window_size]:
        min_dim = min(pkg['length'], pkg['width'], pkg['height'])
        max_min = max(max_min, min_dim)
    return max_min

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


def try_window_packing(packages, window_size, bin_width, bin_height, y_used, uld_length, current_weight, weight_limit):
    """
    Try to pack a window of packages starting from index 0
    """
    if window_size > len(packages):
        return False, None, 0, 0, []

    window_weight = sum(pkg['weight'] for pkg in packages[:window_size])
    if current_weight + window_weight > weight_limit:
        return False, None, 0, 0, []

    max_min_dim = get_max_min_dimension(packages, window_size)
    if max_min_dim + y_used > uld_length:
        return False, None, 0, 0, []
    M = BinManager(bin_width, bin_height, pack_algo='maximal_rectangle', heuristic='best_area', rotation=True)
    item_list = []
    for pkg in packages[:window_size]:
        valid_rotations = get_valid_rotations(pkg, y_used, uld_length, max_min_dim)
        if not valid_rotations:
            return False, None, 0, 0, []

        best_rotation = max(valid_rotations, key=lambda r: r['x'])
        item_list.append(Item(best_rotation['y'], best_rotation['z'], pkg['id'],best_rotation['x'],pkg['cost']))

    M.add_items(*item_list)
    M.execute()

    if len(M.bins) == 1:
        packed_bin = M.bins[0]
        layer = [{"id": item.id, "width": item.width, "height": item.height,"length":item.length,
                  "x": y_used, "y": item.x, "z": item.y} for item in packed_bin.items]
        layer_height = max_min_dim
        
        packed_ids = [item.id for item in packed_bin.items]
        return True, layer, window_weight, layer_height, packed_ids

    return False, None, 0, 0, []


def find_optimal_layer(packages, bin_width, bin_height, y_used, uld_length, current_weight, weight_limit):
    """
    Find optimal layer by trying all possible window sizes starting from index 0
    """
    best_layer = None
    best_weight = 0
    best_height = 0
    best_packed_ids = []

    for window_size in range(len(packages), 0, -1):
        success, layer, weight, height, packed_ids = try_window_packing(
            packages, window_size, bin_width, bin_height,
            y_used, uld_length, current_weight, weight_limit
        )
        if success:
            best_layer = layer
            best_weight = weight
            best_height = height
            best_packed_ids = packed_ids
            break

    return best_layer, best_weight, best_height, best_packed_ids
 


# def pack_items(ULDs, Packages, K):
#     packed_ULDs = {}
#     total_cost = 0
#     economy_cost = 0

#     Priority_Packages = [pkg for pkg in Packages if pkg['type'] == 'P']
#     Economy_Packages = [pkg for pkg in Packages if pkg['type'] == 'E']

#     remaining_packages = Packages.copy()
#     for uld in ULDs:
#         current_weight = 0
#         layers = []
#         y_used = 0
#         contains_priority = False

#         while remaining_packages:
#             layer, layer_weight, layer_height, packed_ids = find_optimal_layer(
#                 remaining_packages, uld['width'], uld['height'],
#                 y_used, uld['length'], current_weight, uld['weight_limit']
#             )

#             if not layer:
#                 break

#             layers.append(layer)
#             y_used += layer_height
            
#             current_weight += layer_weight

#             if any(pkg['id'] in packed_ids for pkg in Priority_Packages):
#                 contains_priority = True

            

#             remaining_packages = [pkg for pkg in remaining_packages if pkg['id'] not in packed_ids]

#         packed_ULDs[uld['id']] = layers
#         if contains_priority:
#             total_cost += K
#     for pkg in remaining_packages:
#         economy_cost += pkg['cost']
#     total_cost += economy_cost
#     return packed_ULDs, total_cost
def pack_items(ULDs, Packages, K):
    packed_ULDs = {}
    total_cost = 0
    economy_cost = 0

    Priority_Packages = [pkg for pkg in Packages if pkg['type'] == 'P']
    Economy_Packages = [pkg for pkg in Packages if pkg['type'] == 'E']

    remaining_packages = Packages.copy()

    # Create 3D space representation for each ULD
    for uld in ULDs:
        uld['space'] = [
            [[False for _ in range(int(uld['height']))] for _ in range(int(uld['width']))]
            for _ in range(int(uld['length']))
        ]
    
    for uld in ULDs:
        current_weight = 0
        layers = []
        y_used = 0
        contains_priority = False

        while remaining_packages:
            layer, layer_weight, layer_height, packed_ids = find_optimal_layer(
                remaining_packages, uld['width'], uld['height'],
                y_used, uld['length'], current_weight, uld['weight_limit']
            )

            if not layer:
                break

            # Update 3D space for packed packages
            for item in layer:
                for x in range(int(item['x']), int(item['x'] + item['length'])):
                    for y in range(int(item['y']), int(item['y'] + item['width'])):
                        for z in range(int(item['z']), int(item['z'] + item['height'])):
                            uld['space'][x][y][z] = True
             
            layers.append(layer)
            y_used += layer_height
            current_weight += layer_weight

            if any(pkg['id'] in packed_ids for pkg in Priority_Packages):
                contains_priority = True

            remaining_packages = [
                {**pkg, 'is_packed': False} for pkg in remaining_packages
                if pkg['id'] not in packed_ids
            ]

        packed_ULDs[uld['id']] = layers
        if contains_priority:
            total_cost += K

    # Handle remaining packages with updated space
  
    uld_data = []
    for uld in ULDs:
         
            
        uld_data.append({
            'id': uld['id'],
            'length': uld['length'],
            'width': uld['width'],
            'height': uld['height'],
            'max_weight': uld['weight_limit'],
            'current_weight': current_weight,
            'volume_left': uld['length'] * uld['width'] * uld['height'] - current_weight,
            'space': uld['space'],
            'pkg_positions': [
                {
                    'x0': item['x'],
                    'x1': item['x'] + item['length'],
                    'y0': item['y'],
                    'y1': item['y'] + item['width'],
                    'z0': item['z'],
                    'z1': item['z'] + item['height'],
                }
                for layer in packed_ULDs[uld['id']] for item in layer
            ]
        })
    print("Here")
    # Add 'is_packed' attribute to all remaining packages
    remaining_packages = [{**pkg, 'is_packed': False} for pkg in remaining_packages]
     
    # Call fit_packages_to_uld for remaining packages
    newpacked=[]
    # updated_uld_data, updated_package_data = fit_packages_to_uld(uld_data, remaining_packages)
    # print("Here")
    # # Update ULDs and remaining packages after fitting
    # for uld, updated_uld in zip(ULDs, updated_uld_data):
    #     uld['space'] = updated_uld['space']

    # remaining_packages = [
    #     pkg for pkg in updated_package_data if not pkg['is_packed']
    # ]
    # newpacked = [
    #     pkg for pkg in updated_package_data if pkg['is_packed']
    # ]


    # Calculate economy cost for remaining packages
    for pkg in remaining_packages:
        economy_cost += pkg['cost']
     
    total_cost += economy_cost
    return packed_ULDs, total_cost, newpacked

class PackingParameters:
    def __init__(self, priority_multiplier, density_weight, cost_weight, volume_weight, weight_factor):
        self.priority_multiplier = priority_multiplier
        self.density_weight = density_weight
        self.cost_weight = cost_weight
        self.volume_weight = volume_weight
        self.weight_factor = weight_factor
    
    def __str__(self):
        return (f"Priority Mult: {self.priority_multiplier}, Density Weight: {self.density_weight}, "
                f"Cost Weight: {self.cost_weight}, Volume Weight: {self.volume_weight}, "
                f"Weight Factor: {self.weight_factor}")

def calculate_package_score(package, params):
    """
    Calculate package score using variable parameters, including weight factor.
    """
    
    volume = package['length'] * package['width'] * package['height']
    if volume == 0:
        return 0
    
    # Density score
    density = (package['weight'] / volume) * params.density_weight
    
    # Priority multiplier
    priority_multiplier = params.priority_multiplier if package['type'] == 'P' else 1.0
    
    # Volume score
    volume_score = volume * params.volume_weight
    
    # Weight score
    weight_score = package['weight'] * params.weight_factor
    
    # Cost efficiency score
    cost_score = 0
    if package['type'] == 'E' and package['cost'] > 0:
        cost_per_volume = package['cost'] / volume
        cost_score = (1.0 / (1.0 + cost_per_volume)) * params.cost_weight
    
    return min(package['length'] , package['width'] , package['height']) * priority_multiplier
    return (density + volume_score + weight_score + cost_score) * priority_multiplier

def optimize_with_parameters(ULDs, Packages, K, params):
    """
    Run packing optimization with specific parameters
    """
    # Create copies of input data
    ulds_copy = [uld.copy() for uld in ULDs]
    
    packages_copy = [pkg.copy() for pkg in Packages]
    
    # Calculate scores and sort packages
    for package in packages_copy:
        package['score'] = calculate_package_score(package, params)
    
    packages_copy.sort(key=lambda x: x['score'], reverse=True)
    
    # Sort ULDs by efficiency
    for uld in ulds_copy:
        volume = uld['length'] * uld['width'] * uld['height']
        uld['efficiency'] = volume #/ uld['weight_limit'] if uld['weight_limit'] > 0 else 0
    ulds_copy.sort(key=lambda x: x['efficiency'], reverse=True)
    
    # Pack items
    return pack_items(ulds_copy, packages_copy, K)
def try_all_parameters_with_min_cost(ULDs, Packages, K):
    """
    Try different weight parameters to find the combination that minimizes cost,
    including package weight as a factor.
    """
    # Define parameter ranges
    priority_multipliers = [1000]
    density_weights = [0.5, 1.0, 1.5, 2.0]
    cost_weights = [10, 12, 15, 20,500]
    volume_weights = [0.001, 0.01, 0.1, 0.5]
    weight_factors = [0.5, 1.0, 1.5, 2.0]  # New range for package weight impact

    results = []
    best_cost = float('inf')
    best_result = None
    best_params = None

    # Iterate through all combinations of weights
    for pm in priority_multipliers:
        for dw in density_weights:
            for cw in cost_weights:
                for vw in volume_weights:
                    for wf in weight_factors:
                        # Create parameters instance
                        params = PackingParameters(pm, dw, cw, vw, wf)

                        # Optimize with current parameters
                        packed_ULDs, total_cost,newpacked = optimize_with_parameters(ULDs, Packages, K, params)

                        # Store results for evaluation
                        result = {
                            'parameters': str(params),
                            'total_cost': total_cost,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        results.append(result)

                        # Update the best result if the cost is minimized
                        if total_cost < best_cost:
                            best_cost = total_cost
                            best_result = packed_ULDs
                            best_params = params

    # Save results to a log file
    with open('optimization_results_min_cost_with_weight.txt', 'w') as f:
        f.write("Optimization Results (Minimizing Cost with Weight Consideration):\n")
        f.write("=" * 80 + "\n")
        for result in sorted(results, key=lambda x: x['total_cost']):
            f.write(f"Cost: {result['total_cost']}\n")
            f.write(f"Parameters: {result['parameters']}\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write("-" * 80 + "\n")

    print(f"Best Parameters Found for Minimizing Cost with Weight Consideration:")
    print(f"Priority Multiplier: {best_params.priority_multiplier}")
    print(f"Density Weight: {best_params.density_weight}")
    print(f"Cost Weight: {best_params.cost_weight}")
    print(f"Volume Weight: {best_params.volume_weight}")
    print(f"Weight Factor: {best_params.weight_factor}")
    print(f"Total Cost: {best_cost}")

    return best_result, best_cost

def try_all_parameters(ULDs, Packages, K):
    """
    Try different parameter combinations and record results
    """
    # Define parameter ranges
    priority_multipliers = [5.0, 10.0, 15.0]
    density_weights = [0.5, 1.0, 1.5]
    cost_weights = [0.3, 0.6, 0.9]
    volume_weights = [0.001, 0.01, 0.1]
    
    results = []
    best_cost = float('inf')
    best_result = None
    best_params = None
    best_newpacked=None
    # Try all combinations
    param_combinations = product(priority_multipliers, density_weights, cost_weights, volume_weights)
    
    for pm, dw, cw, vw in param_combinations:
        params = PackingParameters(pm, dw, cw, vw)
        packed_ULDs, total_cost, newpacked = optimize_with_parameters(ULDs, Packages, K, params)
        
        result = {
            'parameters': str(params),
            'total_cost': total_cost,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        results.append(result)
        
        if total_cost < best_cost:
            best_cost = total_cost
            best_result = packed_ULDs
            best_params = params
            best_newpacked=newpacked
    
    # Save all results to a separate file
    with open('optimization_results.txt', 'w') as f:
        f.write("Parameter Optimization Results:\n")
        f.write("-" * 80 + "\n")
        for result in sorted(results, key=lambda x: x['total_cost']):
            f.write(f"Cost: {result['total_cost']}\n")
            f.write(f"Parameters: {result['parameters']}\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write("-" * 80 + "\n")
    
    print(f"\nBest Parameters Found:")
    print(f"Priority Multiplier: {best_params.priority_multiplier}")
    print(f"Density Weight: {best_params.density_weight}")
    print(f"Cost Weight: {best_params.cost_weight}")
    print(f"Volume Weight: {best_params.volume_weight}")
    print(f"Total Cost: {best_cost}")
    
    return best_result, best_cost,best_newpacked
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

def generate_output(packed_ULDs,newpacked, total_cost, ULDs, Packages, output_file="output.txt", generate_summary=True):
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
        print(total_packages)
        # Prepare output lines
        output_lines = [f"{total_cost},{total_packages},{priority_ULD_count}"]
        
        # Track packed packages
        packed_package_ids = set()
        
        # Generate packing details
        for uld_id, layers in packed_ULDs.items():
            for layer in layers:
                for item in layer:
                    package = next(pkg for pkg in Packages if pkg['id'] == item['id'])
                    x0, y0, z0 = item['x'], item['y'], item['z']
                    x1 = x0 + item['length']
                    y1 = y0 + item['width']
                    z1 = z0 + item['height']
                    
                    output_lines.append(
                        f"{package['id']},{uld_id},"
                        f"{x0},{y0},{z0},"
                        f"{x1},{y1},{z1}"
                    )
                    packed_package_ids.add(package['id'])
        
        # Add unpacked packages
        
        for pkg in Packages:
            if pkg['id'] not in packed_package_ids:
                output_lines.append(f"{pkg['id']},NONE,-1,-1,-1,-1,-1,-1")
 
        # Write main output file
        with open(output_file, "w") as f:
            f.write("\n".join(output_lines))

        # Generate summary if requested
        if generate_summary:
            summary_lines = [
                "Packing Solution Summary",
                "=" * 50,
                f"Total Cost: {total_cost}",
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
       
        # Optimize for minimum cost by varying weight parameters
        best_packed_ULDs, best_cost = try_all_parameters_with_min_cost(ULDs, Packages, K)
        
        # Generate output files
        generate_output(best_packed_ULDs, best_cost, ULDs, Packages, 
                       output_file="output.txt", generate_summary=True)

        print(f"\nOptimization complete. Check:")
        print("1. output.txt - for the required output format")
        print("2. optimization_results_min_cost.txt - for detailed parameter testing results")
        print("3. packing_summary.txt - for packing statistics and analysis")
        print("4. parsing_log.txt - for input parsing details")
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        with open("error_log.txt", "w") as f:
            f.write(f"Error in main execution: {str(e)}")

from itertools import permutations, islice

def limited_permutations(lst, max_perms):
    """
    Generate a limited number of permutations from a list.
    """
    return islice(permutations(lst), max_perms)

def optimize_with_reduced_permutations(ULDs, Packages, K, max_perms=5):
    """
    Optimize packing using reduced permutations.
    """
    # Separate priority and economy packages
    priority_packages = [pkg for pkg in Packages if pkg['type'] == 'P']
    economy_packages = [pkg for pkg in Packages if pkg['type'] == 'E']
    
    # Generate limited permutations for each type
    priority_perms = list(limited_permutations(priority_packages, 1))
    economy_perms = list(limited_permutations(economy_packages, 1))
    
    best_cost = float('inf')
    best_packed_ULDs = None
    packed_ULs= list(limited_permutations(ULDs, 1))
    # Iterate over combined permutations
    ulds_copy = [uld.copy() for uld in ULDs]
    for uld in ulds_copy:
        volume = uld['length'] * uld['width'] * uld['height']
        uld['efficiency'] = volume #/ uld['weight_limit'] if uld['weight_limit'] > 0 else 0
    ulds_copy.sort(key=lambda x: x['efficiency'], reverse=True)
     
    
    for priority_perm in priority_perms:
        for economy_perm in economy_perms:
            # Combine permutations
            combined_packages = list(priority_perm) + list(economy_perm)
            
            # Optimize with current combination
            packed_ULDs, total_cost, newpacked = pack_items(ulds_copy, combined_packages, K)
            print("Done\n")
            print(total_cost)
            # Update best solution
            if total_cost < best_cost:
                best_cost = total_cost
                best_packed_ULDs = packed_ULDs
                best_newpacked= newpacked
    
    return best_packed_ULDs, best_cost, best_newpacked

def main_with_reduced_permutations():
    try:
        # Parse input
        input_file = "input.txt"
        ULDs, Packages, K = parse_input_file(input_file)
        
        # Optimize with reduced permutations
        best_packed_ULDs, best_cost,best_newpacked = optimize_with_reduced_permutations(ULDs, Packages, K, max_perms=100)
        
        # Generate output files
        generate_output(best_packed_ULDs,best_newpacked, best_cost, ULDs, Packages,
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
    main_with_reduced_permutations()
    end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"Total execution time: {elapsed_time:.2f} seconds")

# if __name__ == "__main__":
#     main()

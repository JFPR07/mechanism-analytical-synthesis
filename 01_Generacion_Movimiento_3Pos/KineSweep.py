import cmath
import math
import os
import numpy as np

# ==========================================
# 1. AUXILIARY AND UTILITY FUNCTIONS
# ==========================================

def multiplicative_factor(input_list):
    decimal_counts = list()
    for value in input_list:
        sub_list = value.split('.')
        if len(sub_list) > 1:
            decimal_count = len(sub_list[1])
        else:
            decimal_count = 0
        decimal_counts.append(decimal_count)
    max_decimals = max(decimal_counts) if decimal_counts else 0
    factor = pow(10, max_decimals)
    return factor


def transmission_angle(angular_difference):
    if angular_difference > 180:
        mu_raw = 360 - angular_difference
    else:
        mu_raw = angular_difference

    if mu_raw > 90:
        mu = 180 - mu_raw
    else:
        mu = mu_raw

    return mu


def generate_beta_3_values(beta_2, range_dict):
    if beta_2 not in range_dict:
        # If there is no configuration for that beta_2, return empty (skip)
        return []

    config = range_dict[beta_2]
    step = config['Step']
    beta_3_values = []

    if step == 0:
        # invalid step
        return []

    for subint in config['Subintervals']:
        lower_lim = subint['Lower limit']
        upper_lim = subint['Upper limit']
        stop_lim = upper_lim + 1 if step > 0 else upper_lim - 1
        for val in range(lower_lim, stop_lim, step):
            beta_3_values.append(val)

    return beta_3_values


# === BRANCH FILTER (NEW AUXILIARY FUNCTION) ===
def evaluate_branch_defect(V_rect, U_rect, alpha2_deg, alpha3_deg, beta2_right_deg, beta3_right_deg):
    """
    Evaluates whether the 4-bar mechanism presents a branch defect between the 3 positions.
    Determines the sign of orientation (cross product between the coupler vector V and crank/rocker U)
    at positions 1, 2 and 3.
    Returns True if all positions belong to the same branch (valid), False if branch changes.
    """
    # Position 1
    V1 = V_rect
    U1 = U_rect

    # Position 2
    V2 = V1 * cmath.exp(1j * math.radians(alpha2_deg))
    U2 = U1 * cmath.exp(1j * math.radians(beta2_right_deg))

    # Position 3
    V3 = V1 * cmath.exp(1j * math.radians(alpha3_deg))
    U3 = U1 * cmath.exp(1j * math.radians(beta3_right_deg))

    # Z-component of the 2D cross product (V_x * U_y - V_y * U_x) that defines the branch
    cross1 = V1.real * U1.imag - V1.imag * U1.real
    cross2 = V2.real * U2.imag - V2.imag * U2.real
    cross3 = V3.real * U3.imag - V3.imag * U3.real

    sign1 = np.sign(cross1)
    sign2 = np.sign(cross2)
    sign3 = np.sign(cross3)

    # If any position falls in singularity/dead point (cross == 0), discard
    if sign1 == 0 or sign2 == 0 or sign3 == 0:
        return False

    # Validate that the 3 positions keep the same orientation sign
    return (sign1 == sign2 == sign3)
# ========================================================


# === BETA_3 FILTER (NEW AUXILIARY FUNCTION) ===
def is_valid_beta3(beta3_left_deg, beta3_right_deg, limit=100):
    """
    Evaluates the discard filter by beta_3: if the beta_3 of the left dyad AND the beta_3
    of the right dyad are both greater than 'limit' in absolute value, the mechanism is discarded.
    Returns True if the mechanism should be kept, False if it should be discarded.
    """
    return not (abs(beta3_left_deg) > limit and abs(beta3_right_deg) > limit)
# ==============================================================


# ==========================================
# 2. SCIENTIFIC AND MATRIX CALCULATION FUNCTIONS
# ==========================================

def cramers_rule(prescribed_values, created_matrices):
    size = len(prescribed_values)
    matrix_A = np.array(prescribed_values[0:size - 1]).transpose()
    created_matrices.append(matrix_A)
    for i in range(size - 1):
        matrix_copy = matrix_A.copy()
        matrix_copy[:, i] = prescribed_values[size - 1]
        created_matrices.append(matrix_copy)

    determinant_values = list()
    for matrix in created_matrices:
        determinant_values.append(np.linalg.det(matrix))

    unknown_values = list()
    for i in range(1, len(determinant_values)):
        if determinant_values[0] == 0:
            print("\n[!] Error: The main determinant is zero. The system does not have a unique solution.")
            break
        div = determinant_values[i] / determinant_values[0]
        # cmath.polar(div) returns (magnitude, phase in radians)
        unknown_values.append(cmath.polar(div))

    return unknown_values


def solve_mechanism(free_options, prescribed_data):
    """
    free_options: [[beta2_left_deg, beta3_left_deg], [beta2_right_deg, beta3_right_deg]]
    prescribed_data: [[alpha2_deg, alpha3_deg], [delta2_complex, delta3_complex]]
    ---
    IMPORTANT: The deltas are used as-is (rectangular complex form),
    without passing through exp(1j*delta)-1. The beta and alpha continue to be transformed with exp(1j*rad)-1.
    """
    sides = ['left', 'right']
    iterations = len(sides)
    results = list()

    for i in range(iterations):
        prescribed_values = [free_options[i]] + prescribed_data
        values_by_side = list()

        # Process beta and alpha (convert degrees to radians and apply e^(i*rad) - 1)
        for elements in prescribed_values[:-1]:
            temp_list = list()
            for number in elements:
                rad = math.radians(float(number))
                formatted_data = cmath.exp(1j * rad) - 1
                temp_list.append(formatted_data)
            values_by_side.append(temp_list)

        # Process delta: NOW we use the rectangular form as-is (complex),
        # we DO NOT apply exp(1j*delta)-1 here.
        # We assume prescribed_values[-1] already contains complex objects.
        rectangular_deltas = []
        for delta in prescribed_values[-1]:
            # If for some reason delta comes as string (e.g. "3+2j"), convert to complex
            if isinstance(delta, str):
                delta_complex = complex(delta.replace(" ", "").replace("*", ""))
            else:
                delta_complex = complex(delta)
            # Use the rectangular representation directly (not exponential)
            rectangular_deltas.append(delta_complex)
        values_by_side.append(rectangular_deltas)

        created_matrices = list()
        unknown_values = cramers_rule(values_by_side, created_matrices)
        results.append(unknown_values)

    return results


# ==========================================
# 3. INTERFACE, READING AND STORAGE FUNCTIONS
# ==========================================

def get_prescribed_data(unknowns_count):
    prescribed_data = list()

    print(f"\n============================================\n   ENTERING PRESCRIBED DATA \n============================================")

    # 1. Validation for 'alpha'
    alphas = list()
    print("\n--- Entering Alpha Angles (in degrees) ---")
    for i in range(unknowns_count):
        while True:
            try:
                user_input = input(f"  • Enter alpha {i + 2}: ")
                value = float(user_input)
                alphas.append(value)
                break
            except ValueError:
                print("  [!] Error: Enter a valid numeric value (e.g. 30 or 45.5).")
    prescribed_data.append(alphas)

    # 2. Validation for 'delta' (we transform them to complex here)
    deltas = list()
    print("\n--- Entering Delta Displacements (in a+bj form) ---")
    for i in range(unknowns_count):
        while True:
            try:
                user_input = input(f"  • Enter delta {i + 2} (e.g. 3+2j or 5-1j): ").replace(" ", "").replace("*", "")
                value = complex(user_input)   # now we store as complex (rectangular)
                deltas.append(value)
                break
            except ValueError:
                print("  [!] Error: Invalid format. Correct examples: 2+3j, -1.5+4j or 3j.")
    prescribed_data.append(deltas)

    return prescribed_data


def save_mechanism(file_name, data):
    # === SORT BY BEST TRANSMISSION ANGLE ===
    # Each row carries 4 angles (already bounded to [0°,90°] by transmission_angle, where
    # closer to 90° = better): row[12]=mu1_left, row[13]=mu3_left, row[14]=mu1_right, row[15]=mu3_right.
    # For each side we take the worst of its two extreme positions (min), and between the
    # two sides we take the best available (max), since it's enough that one side works
    # to handle the mechanism. We sort that value from highest to lowest.
    data = sorted(
        data,
        key=lambda row: max(min(row[12], row[13]), min(row[14], row[15])),
        reverse=True
    )
    # ===========================================================
    # Grouped headers with wide visual formatting
    top_line = f"{'LEFT DYAD':^60}{'RIGHT DYAD':^60}{'LEFT CRANK':^20}{'RIGHT CRANK':^20}\n"

    sub_headers = (
        f"{'β_2 (°)':>10}{'β_3 (°)':>10}{'w (mm)':>10}{'θ_w (°)':>10}{'z (mm)':>10}{'θ_z (°)':>10}"
        f"{'β_2 (°)':>10}{'β_3 (°)':>10}{'w (mm)':>10}{'θ_w (°)':>10}{'z (mm)':>10}{'θ_z (°)':>10}"
        f"{'μ_1 (°)':>10}{'μ_3 (°)':>10}{'μ_1 (°)':>10}{'μ_3 (°)':>10}\n"
    )

    separator = "═" * 160 + "\n"
    thin_line = "─" * 160 + "\n"

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(separator)
        file.write(top_line)
        file.write(thin_line)
        file.write(sub_headers)
        file.write(separator)

        for row in data:
            # Convert angles that are in radians to degrees before printing.
            # Expected structure of 'row' (indices, 0-based):
            # 0: beta2_left (deg)
            # 1: beta3_left (deg)
            # 2: w_left (magnitude)
            # 3: theta_w_left (radians)  <-- convert to degrees
            # 4: z_left (magnitude)
            # 5: theta_z_left (radians)  <-- convert to degrees
            # 6: beta2_right (deg)
            # 7: beta3_right (deg)
            # 8: w_right (magnitude)
            # 9: theta_w_right (radians)  <-- convert to degrees
            #10: z_right (magnitude)
            #11: theta_z_right (radians)  <-- convert to degrees
            #12..: transmission angles (already in degrees)

            converted_row = []
            for idx, datum in enumerate(row):
                if idx in (3, 5, 9, 11):
                    # Convert radians -> degrees before formatting
                    value_in_degrees = math.degrees(datum)
                    converted_row.append(value_in_degrees)
                else:
                    converted_row.append(datum)

            line = "".join([f"{value:>10.3f}" for value in converted_row]) + "\n"
            file.write(line)


# ==========================================
# 4. MAIN EXECUTION FLOW
# ==========================================

def main():

    UNKNOWNS_COUNT = 2

    prescribed_data_list = get_prescribed_data(UNKNOWNS_COUNT)

    beta_2_ranges = {}
    range_parameters = ['Lower limit', 'Upper limit', 'Step']
    beta_2_strings = list()

    print("\n--- Range Configuration for Beta 2 ---")
    for parameter in range_parameters:
        while True:
            try:
                entered_value = input(f"  • {parameter} for beta 2: ")
                val_float = float(entered_value)

                # Validation so that the step is not zero
                if parameter == 'Step' and val_float == 0:
                    print("  [!] Error: Step cannot be 0.")
                    continue

                beta_2_strings.append(entered_value)
                entered_value = val_float
                break
            except ValueError:
                print("  [!] Error: Not a valid numeric value. Try again.")
        beta_2_ranges[parameter] = entered_value

    beta_2_factor = multiplicative_factor(beta_2_strings)

    for parameter in beta_2_ranges:
        beta_2_ranges[parameter] = round(beta_2_ranges[parameter] * beta_2_factor)

    # Adjust the Beta 2 tuple by adding the step to the upper limit to include it
    b2_step = beta_2_ranges['Step']
    beta_2_range = (
        beta_2_ranges['Lower limit'],
        beta_2_ranges['Upper limit'] + (1 if b2_step > 0 else -1),
        b2_step
    )

    beta_3_ranges_by_beta_2 = {}
    beta_3_strings = list()

    print("\n--- Range Configuration for Beta 3 ---")
    for beta_2 in range(*beta_2_range):
        beta_2_real = beta_2 / beta_2_factor
        print(f"\n Configuration for Beta 2 = {beta_2_real}:")

        while True:
            try:
                intervals_count = int(input(f"  • Number of subintervals for Beta 3: "))
                if intervals_count > 0:
                    break
                print("  [!] Enter an integer greater than 0.")
            except ValueError:
                print("  [!] Error: You must enter an integer.")

        subintervals = []
        for i in range(intervals_count):
            print(f"    Subinterval {i + 1}:")
            limits = {}
            for lim in ['Lower limit', 'Upper limit']:
                while True:
                    try:
                        val_str = input(f"      - {lim}: ")
                        float(val_str)
                        beta_3_strings.append(val_str)
                        limits[lim] = float(val_str)
                        break
                    except ValueError:
                        print("      [!] Error: Not a valid numeric value.")

            subintervals.append(limits)

        while True:
            try:
                step_str = input(f"  • Step for Beta 3: ")
                step_val = float(step_str)

                if step_val == 0:
                    print("  [!] Error: Step must be different from 0.")
                    continue

                beta_3_strings.append(step_str)
                break
            except ValueError:
                print("  [!] Error: You must enter a valid number.")

        beta_3_ranges_by_beta_2[beta_2] = {'Step': step_val, 'Subintervals': subintervals}

    beta_3_factor = multiplicative_factor(beta_3_strings)

    # Scale Beta 3 values
    for beta_2 in beta_3_ranges_by_beta_2:
        beta_3_ranges_by_beta_2[beta_2]['Step'] = round(beta_3_ranges_by_beta_2[beta_2]['Step'] * beta_3_factor)

        for subint in beta_3_ranges_by_beta_2[beta_2]['Subintervals']:
            subint['Lower limit'] = round(subint['Lower limit'] * beta_3_factor)
            subint['Upper limit'] = round(subint['Upper limit'] * beta_3_factor)

    data = list()

    # Mechanism iterations
    for beta_2_left in range(*beta_2_range):
        left_beta_3_list = generate_beta_3_values(beta_2_left, beta_3_ranges_by_beta_2)

        for beta_3_left in left_beta_3_list:
            left_side = [(beta_2_left / beta_2_factor), (beta_3_left / beta_3_factor)]

            for beta_2_right in range(*beta_2_range):
                right_beta_3_list = generate_beta_3_values(beta_2_right, beta_3_ranges_by_beta_2)

                for beta_3_right in right_beta_3_list:
                    right_side = [(beta_2_right / beta_2_factor), (beta_3_right / beta_3_factor)]

                    # === BETA_3 FILTER (EARLY DISCARD, BEFORE SOLVING THE DYAD) ===
                    if not is_valid_beta3(left_side[1], right_side[1]):
                        continue  # Discard if beta_3 left and beta_3 right exceed 100° in absolute value
                    # =====================================================================================

                    free_options = [left_side, right_side]
                    results = solve_mechanism(free_options, prescribed_data_list)

                    # Get coupler vectors
                    coupler_vector_names = ['Z', 'S']
                    coupler_vectors = dict()
                    for i, sides in enumerate(results):
                        coupler_vectors[coupler_vector_names[i]] = cmath.rect(sides[1][0], sides[1][1])

                    coupler = coupler_vectors["Z"] - coupler_vectors["S"]

                    # Get dyad vectors
                    dyad_vector_names = ['W', 'U']
                    vectors = dict()
                    for i, sides in enumerate(results):
                        vectors[dyad_vector_names[i]] = sides[0]
                    vectors['V'] = cmath.polar(coupler)


                    # === APPLY BRANCH FILTER IN THE SYNTHESIS LOOP ===
                    U_rect = cmath.rect(results[1][0][0], results[1][0][1])
                    alpha2_deg = prescribed_data_list[0][0]
                    alpha3_deg = prescribed_data_list[0][1]
                    beta2_right_real = beta_2_right / beta_2_factor
                    beta3_right_real = beta_3_right / beta_3_factor

                    if not evaluate_branch_defect(coupler, U_rect, alpha2_deg, alpha3_deg, beta2_right_real, beta3_right_real):
                        continue  # Discard the mechanism if it presents a branch defect
                    # =======================================================================

                    prescribed_values = free_options + prescribed_data_list

                    transmission_angles = list()
                    size = len(prescribed_values)

                    for i, name in enumerate(reversed(dyad_vector_names)):
                        # Position 1
                        angular_difference = math.fabs(math.degrees(vectors[name][1]) - math.degrees(vectors['V'][1]))
                        mu = transmission_angle(angular_difference)
                        transmission_angles.append(mu)

                        # Position 3
                        angular_difference = math.fabs(
                            math.degrees(vectors[name][1]) + float(prescribed_values[size - 3 - i][1]) -
                            (math.degrees(vectors['V'][1]) + float(prescribed_values[2][1]))
                        )
                        mu = transmission_angle(angular_difference)
                        transmission_angles.append(mu)

                    row_data = list()
                    for lst, side in zip(results, free_options):
                        row_data += side
                        for i in range(len(lst)):
                            row_data += [*lst[i]]

                    row_data += transmission_angles
                    data.append(row_data)

    save_mechanism("synthesized_mechanisms.txt", data)
    print("\n[✓] Calculation completed successfully and data saved in 'synthesized_mechanisms.txt'.")


# ==========================================
# QUICK TEST FUNCTION (run_test)
# ==========================================
def run_test():
    """
    Runs a single synthesis with the control data provided,
    without interaction. Prints a CSV row comparable with previous versions.
    """
    # Control data provided
    beta_2_left = -11.4
    beta_3_left = -96.0
    beta_2_right = -11.6
    beta_3_right = -88.0

    alpha2 = 2.0
    alpha3 = 20.0
    # Here the deltas in rectangular form (complex)
    delta2 = 0.16221483 + 0.83457915j
    delta3 = 4.48839208 + 3.85019818j

    free_options = [[beta_2_left, beta_3_left], [beta_2_right, beta_3_right]]
    prescribed_data = [[alpha2, alpha3], [delta2, delta3]]

    results = solve_mechanism(free_options, prescribed_data)

    # Rebuild the CSV row (same order as save_mechanism/simple CSV)
    row = []
    # left: beta2, beta3
    row += [beta_2_left, beta_3_left]
    # w and theta_w (from the left side) -> come from results[0][0] = (mag, phase)
    row += [results[0][0][0], math.degrees(results[0][0][1])]
    # z and theta_z (from the left side) -> results[0][1]
    row += [results[0][1][0], math.degrees(results[0][1][1])]
    # right
    row += [beta_2_right, beta_3_right]
    row += [results[1][0][0], math.degrees(results[1][0][1])]
    row += [results[1][1][0], math.degrees(results[1][1][1])]

    # Calculate V (coupler) for transmission angles
    Z = cmath.rect(results[0][1][0], results[0][1][1])
    S = cmath.rect(results[1][1][0], results[1][1][1])
    coupler = Z - S
    V = cmath.polar(coupler)
    V_ang_deg = math.degrees(V[1])

    # === BRANCH EVALUATION IN QUICK TEST ===
    U_rect = cmath.rect(results[1][0][0], results[1][0][1])
    passes_branch_filter = evaluate_branch_defect(coupler, U_rect, alpha2, alpha3, beta_2_right, beta_3_right)
    print(f"[Branch Filter] Is the mechanism free of branch defect?: {passes_branch_filter}")
    # ====================================================

    # === BETA_3 FILTER EVALUATION IN QUICK TEST ===
    passes_beta3_filter = is_valid_beta3(beta_3_left, beta_3_right)
    print(f"[Beta_3 Filter] Does the mechanism pass the beta_3 filter (not both >100° abs)?: {passes_beta3_filter}")
    # ================================================================

    # vectors for mu: W = results[0][0], U = results[1][0]
    vectors = {'W': results[0][0], 'U': results[1][0], 'V': V}
    full_prescribed_values = free_options + prescribed_data
    size = len(full_prescribed_values)

    transmission_angles = []
    vector_names = ['W', 'U']
    for i, name in enumerate(reversed(vector_names)):
        angular_difference = abs(math.degrees(vectors[name][1]) - V_ang_deg)
        mu = transmission_angle(angular_difference)
        transmission_angles.append(mu)
        angular_difference = abs(math.degrees(vectors[name][1]) + float(full_prescribed_values[size - 3 - i][1]) - (V_ang_deg + float(full_prescribed_values[2][1])))
        mu = transmission_angle(angular_difference)
        transmission_angles.append(mu)

    row += transmission_angles

    # Print in CSV format (3 decimals)
    header = "beta2_left_deg,beta3_left_deg,w_left_mm,theta_w_left_deg,z_left_mm,theta_z_left_deg,beta2_right_deg,beta3_right_deg,w_right_mm,theta_w_right_deg,z_right_mm,theta_z_right_deg,mu1_left_deg,mu3_left_deg,mu1_right_deg,mu3_right_deg"
    row_3dec = [f"{x:.3f}" for x in row]
    print(header)
    print(",".join(row_3dec))
    # Return the row (useful if captured programmatically)
    return row

# ===========================
# OPTIONAL EXECUTION:
# ===========================
if __name__ == "__main__":
    main()   # uncomment for full interactive execution
    # For quick test without interaction, run run_test()
    # run_test()
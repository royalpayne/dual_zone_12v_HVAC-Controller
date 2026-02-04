# Save the working power code to ir_codes.json
import json

# Working power code captured from Whynter remote
power_code = [9000, 4603, 525, 629, 548, 628, 526, 650, 527, 1759, 541, 655, 521, 681,
              523, 1755, 572, 631, 528, 648, 522, 634, 519, 655, 544, 1757, 546, 634,
              545, 1782, 522, 732, 445, 658, 544, 1755, 549, 628, 522, 635, 541, 634,
              520, 658, 545, 1782, 519, 657, 547, 1757, 520, 658, 519, 657, 520, 1783,
              518, 637, 542, 636, 541, 659, 519, 1782, 656, 523, 520]

codes = {"power": power_code}

with open("ir_codes.json", "w") as f:
    json.dump(codes, f)

print("Saved power code to ir_codes.json")
print(f"Code length: {len(power_code)} timings")

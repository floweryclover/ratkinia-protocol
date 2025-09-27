import re
import os

api_macro = "RATKINIAPROTOCOL_API"

def client_api_patch(client_output_include_dir: str):
    for filename in os.listdir(client_output_include_dir):
        if not filename.endswith(".pb.h"):
            continue
        with open(f"{client_output_include_dir}\\{filename}", 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        class_pattern = re.compile(r"^(class\s+)(\w+)(.*)$")

        for line in lines:
            if api_macro in line:
                new_lines.append(line)
                continue

            match = class_pattern.match(line)
            if match:
                new_line = f"{match.group(1)}{api_macro} {match.group(2)}{match.group(3)}\n"
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        with open(f"{client_output_include_dir}\\{filename}", 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
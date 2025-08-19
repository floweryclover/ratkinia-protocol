import os
import google.protobuf
from protocol_types import ProtocolTypes

def generate_message_type(output_dir: str,
                          top_comment: str,
                          types: dict,
                          name: str,
                          messages):
    with open(f"{output_dir}\\{name}MessageType.gen.h", "w", encoding="utf-8") as out:
        out.write(f"{top_comment}")
        out.write(f"#ifndef RATKINIAPROTOCOL_{name.upper()}MESSAGETYPES_GEN_H\n")
        out.write(f"#define RATKINIAPROTOCOL_{name.upper()}MESSAGETYPES_GEN_H\n\n")

        if types[ProtocolTypes.TYPE_UINT16] == "uint16_t":
            out.write("#include <cstdint>\n\n")

        out.write(f"namespace RatkiniaProtocol \n")
        out.write(f"{{\n")
        out.write(f"    enum class {name}MessageType : {types[ProtocolTypes.TYPE_UINT16]}\n")
        out.write("    {\n")
        for idx, msg in enumerate(messages):
            out.write(f"        {msg.name} = {idx},\n")
        out.write("    };\n")
        out.write(f"}}\n")
        out.write(f"#endif")
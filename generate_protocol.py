from protocol_types import ProtocolTypes

def generate_protocol(version: str, output_dir: str, top_comment: str, types: dict, for_client: bool):
    message_header_name = "FMessageHeader" if for_client else "MessageHeader"
    with open(f"{output_dir}\\RatkiniaProtocol.gen.h", "w", encoding="utf-8") as out:
        out.write(f"{top_comment}")
        out.write("#ifndef RATKINIAPROTOCOL_H\n#define RATKINIA_PROTOCOL_H\n\n")
        out.write("#include <cstdint>\n\n")
        out.write("namespace RatkiniaProtocol\n")
        out.write("{\n")
        out.write(f"#pragma pack(push, 1)\n")
        out.write(f"    struct {message_header_name} final\n")
        out.write(f"    {{\n")
        out.write(f"        {types[ProtocolTypes.TYPE_UINT16]} MessageType;\n")
        out.write(f"        {types[ProtocolTypes.TYPE_UINT16]} BodySize;\n")
        out.write(f"    }};\n")
        out.write(f"#pragma pack(pop)\n\n")
        out.write(f"    constexpr {types[ProtocolTypes.TYPE_SIZE]} MessageMaxSize = 1024 + sizeof({message_header_name});\n")
        out.write(f"    constexpr {types[ProtocolTypes.TYPE_SIZE]} MessageHeaderSize = sizeof({message_header_name});\n")
        out.write(f"    constexpr const char* const Version = \"{version}\";\n")
        out.write(f"}}\n\n")
        out.write(f"#endif")
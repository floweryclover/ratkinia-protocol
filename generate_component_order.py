# from In.components import components

def generate_component_order(output_dir: str, top_comment: str, for_client: bool, component_messages):
    component_order_type_name = ("E" if for_client else "") + "ComponentOrder"
    enum_type = "uint16" + ("_t" if not for_client else "")

    with open(f"{output_dir}\\ComponentOrder.gen.h", "w", encoding="utf-8") as out:
        out.write(f"{top_comment}")
        out.write("#ifndef RATKINIAPROTOCOL_COMPONENTORDER_H\n#define RATKINIAPROTOCOL_COMPONENTORDER_H\n\n")
        if not for_client:
            out.write("#include <cstdint>\n\n")
        out.write("namespace RatkiniaProtocol\n")
        out.write("{\n")
        out.write(f"    enum class {component_order_type_name} : {enum_type}\n")
        out.write(f"    {{\n")
        out.write(f"        Invalid, // OneOf 필드는 1부터 시작함.\n")
        for component_message_fd in component_messages.file:
            for component_message in component_message_fd.message_type:
                out.write(f"        {component_message.name},\n")
        out.write(f"    }};\n")
        out.write(f"}}\n\n")
        out.write(f"#endif")
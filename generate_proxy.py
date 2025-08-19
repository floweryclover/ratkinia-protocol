import os
from utils import *
from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

def generate_proxy(output_dir: str,
                  top_comment: str,
                  types: dict,
                  for_client: bool,
                  name: str,
                  messages):
    proxy_class_name = f"{'T' if for_client else ''}{name}Proxy"
    with open(f"{output_dir}\\{name}Proxy.gen.h", "w", encoding="utf-8") as out:
        out.write(f"{top_comment}")
        out.write(f"#ifndef RATKINIAPROTOCOL_{name.upper()}PROXY_GEN_H\n")
        out.write(f"#define RATKINIAPROTOCOL_{name.upper()}PROXY_GEN_H\n\n")
        out.write(f"#include \"{name}.pb.h\"\n")
        out.write(f"#include \"{name}MessageType.gen.h\"\n\n")

        out.write(f"namespace RatkiniaProtocol \n")
        out.write(f"{{\n")
        out.write(f"    template<typename TDerivedProxy>\n")
        out.write(f"    class {proxy_class_name}\n")
        out.write(f"    {{\n")
        out.write(f"    public:")
        for msg in messages:
            params_string = ""
            params = []

            for field in msg.field:
                type_name = field_type_to_string(field, types)
                param_name = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)

                if is_trivial_type(field) or is_array(field):
                    type_name = f"const {type_name}"
                elif for_client and field.type == FieldDescriptorProto.TYPE_STRING:
                    type_name = f"const FString&"

                # 언리얼 bool b 접두사 붙이기
                if for_client and field.type == FieldDescriptorProto.TYPE_BOOL and not is_array(field):
                    param_name = "b" + param_name

                params.append(f"{type_name} {param_name}")
            params_string = ", ".join(params)
            out.write(f"\n        void {msg.name}({make_context_parameter(not for_client and len(params) > 0)}")
            out.write(f"{params_string}")
            out.write(")\n")
            out.write(f"        {{\n")
            out.write(f"            class {msg.name} {msg.name}Message;\n")
            for field in msg.field:
                arg = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)
                if is_array(field):
                    field_type = parse_only_type_name(field)
                    out.write(f"            for ({field_type}& {arg}Element : {arg})\n")
                    out.write(f"            {{\n")
                    out.write(f"                {field_type}* const {arg}ArrayAdd = {msg.name}Message.add_{field.name}();\n")
                    out.write(f"                *{arg}ArrayAdd = std::move({arg}Element);\n")
                    out.write(f"            }}\n")
                else:
                    if for_client and field.type == FieldDescriptorProto.TYPE_BOOL:
                        arg = "b" + arg
                    if for_client and field.type == FieldDescriptorProto.TYPE_STRING:
                        arg = "std::string{TCHAR_TO_UTF8(*" + arg + ")}"
                    out.write(f"            {msg.name}Message.set_{field.name}({arg});\n")
            out.write(f"            static_cast<TDerivedProxy*>(this)->WriteMessage({make_context_argument(not for_client and len(params) > 0)}{name}MessageType::{msg.name}, {msg.name}Message);\n")
            out.write(f"        }}\n")
        out.write(f"    }};\n")
        out.write("}\n\n")
        out.write(f"#endif")
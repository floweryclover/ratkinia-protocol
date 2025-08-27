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
        out.write(f"#include \"{name}MessageType.gen.h\"\n")
        out.write(f"#include \"Components/ComponentMessage.gen.pb.h\"\n\n")

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
                field_name = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)

                if is_array(field):
                    original_range_parameter = f"auto&& {camel_to_pascal_if('original', for_client)}{snake_to_pascal(field.name)}Range"
                    setter = f"auto&& {field_name}Setter"
                    params.append(f"{original_range_parameter}, {setter}")
                    continue
                elif is_trivial_type(field):
                    type_name = f"const {type_name}"
                elif for_client and field.type == FieldDescriptorProto.TYPE_STRING:
                    type_name = f"const FString&"

                # 언리얼 bool b 접두사 붙이기
                if for_client and field.type == FieldDescriptorProto.TYPE_BOOL and not is_array(field):
                    field_name = "b" + field_name

                params.append(f"{type_name} {field_name}")
            params_string = ", ".join(params)
            out.write(f"\n        void {msg.name}({make_context_parameter(not for_client, len(params) > 0)}")
            out.write(f"{params_string}")
            out.write(")\n")
            out.write(f"        {{\n")
            out.write(f"            class {msg.name}* {msg.name}Message = google::protobuf::Arena::CreateMessage<class {msg.name}>(static_cast<TDerivedProxy*>(this)->GetArena());\n")
            for field in msg.field:
                arg = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)
                if is_array(field):
                    field_type = parse_only_type_name(field)
                    field_name = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)
                    loop_variable_name = f"{camel_to_pascal_if(f'original', for_client)}{snake_to_pascal(field.name)}Element"
                    out.write(f"            for (auto&& {loop_variable_name} : {camel_to_pascal_if('original', for_client)}{snake_to_pascal(field.name)}Range)\n")
                    out.write(f"            {{\n")
                    out.write(f"                {field_type}* const New{arg}Element = {msg.name}Message->add_{field.name}();\n")
                    out.write(f"                {field_name}Setter(std::forward<decltype({loop_variable_name})>({loop_variable_name}), *New{arg}Element);\n")
                    out.write(f"            }}\n")
                else:
                    if for_client and field.type == FieldDescriptorProto.TYPE_BOOL:
                        arg = "b" + arg
                    if for_client and field.type == FieldDescriptorProto.TYPE_STRING:
                        arg = "std::string{TCHAR_TO_UTF8(*" + arg + ")}"
                    out.write(f"            {msg.name}Message->set_{field.name}({arg});\n")
            out.write(f"            static_cast<TDerivedProxy*>(this)->WriteMessage({make_context_argument(not for_client)}{name}MessageType::{msg.name}, *{msg.name}Message);\n")
            out.write(f"        }}\n")
        out.write(f"    }};\n")
        out.write("}\n\n")
        out.write(f"#endif")
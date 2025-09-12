from utils import *
from protocol_types import *

def generate_stub(output_dir: str,
                  top_comment: str,
                  types: dict,
                  for_client: bool,
                  name: str,
                  messages):
    stub_class_name = f"{'T' if for_client else ''}{name}Stub"
    with open(f"{output_dir}\\{name}Stub.gen.h", "w", encoding="utf-8") as out:
        out.write(f"{top_comment}")
        out.write(f"#ifndef RATKINIAPROTOCOL_{name.upper()}STUB_GEN_H\n")
        out.write(f"#define RATKINIAPROTOCOL_{name.upper()}STUB_GEN_H\n\n")
        out.write(f"#include \"{name}MessageType.gen.h\"\n")
        out.write(f"#include \"{name}.pb.h\"\n")
        out.write(f"#include \"Components/ComponentMessage.gen.pb.h\"\n\n")

        out.write(f"namespace RatkiniaProtocol \n")
        out.write(f"{{\n")
        out.write(f"    template<typename TDerivedStub>\n")
        out.write(f"    class {stub_class_name}\n")
        out.write(f"    {{\n")
        out.write(f"    public:\n")
        out.write(f"        virtual ~{stub_class_name}() = default;\n\n")
        out.write(f"        virtual void OnUnknownMessageType({make_context_parameter(not for_client)}{name}MessageType {camel_to_pascal_if('messageType', for_client)}) = 0;\n\n")
        out.write(f"        virtual void OnParseMessageFailed({make_context_parameter(not for_client)}{name}MessageType {camel_to_pascal_if('messageType', for_client)}) = 0;\n\n")
        if for_client:
            out.write(f"        virtual void OnUnhandledMessageType({name}MessageType {camel_to_pascal_if('messageType', for_client)}) = 0;\n\n")

        for msg in messages:
            params = []
            for field in msg.field:
                type_name = field_type_to_string(field, types)
                param_name = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)

                # 언리얼 bool b 접두사 붙이기
                if for_client and field.type == FieldDescriptorProto.TYPE_BOOL and not is_array(field):
                    param_name = "b" + param_name

                if is_array(field):
                    if for_client:
                        type_name = f"TArrayView<const {parse_only_type_name(field)}* const>"
                    else:
                        type_name = f"std::span<const {parse_only_type_name(field)}*>"
                elif not is_trivial_type(field) and not (for_client and field.type == FieldDescriptorProto.TYPE_STRING):
                    type_name = f"const {type_name}&"

                params.append(f"{type_name} {param_name}")
            out.write(f"        virtual void On{msg.name}({make_context_parameter(not for_client, len(params) > 0)}")
            out.write(", ".join(params))
            if not for_client:
                out.write(f") = 0;\n\n")
            else:
                out.write(f") {{ static_cast<TDerivedStub*>(this)->OnUnhandledMessageType({name}MessageType::{msg.name}); }}\n\n")

        out.write(f"        void Handle{name}({make_context_parameter(not for_client)}const {types[ProtocolTypes.TYPE_UINT16]} {camel_to_pascal_if('messageType', for_client)}, const {types[ProtocolTypes.TYPE_UINT16]} {camel_to_pascal_if('bodySize', for_client)}, const char* const {camel_to_pascal_if('body', for_client)})\n")
        out.write(f"        {{\n")
        out.write(f"            switch (static_cast<int32_t>({camel_to_pascal_if('messageType', for_client)}))\n")
        out.write(f"            {{\n")

        for msg in messages:
            out.write(f"                case static_cast<int32_t>({name}MessageType::{msg.name}):\n")
            out.write(f"                {{\n")
            out.write(f"                    {msg.name} {msg.name}Message;\n")
            out.write(f"                    if (!{msg.name}Message.ParseFromArray({camel_to_pascal_if('body', for_client)}, {camel_to_pascal_if('bodySize', for_client)}))\n")
            out.write(f"                    {{\n")
            out.write(f"                        static_cast<TDerivedStub*>(this)->OnParseMessageFailed({make_context_argument(not for_client and True)}static_cast<{name}MessageType>({camel_to_pascal_if('messageType', for_client)}));\n")
            out.write(f"                        return;\n")
            out.write(f"                    }}\n")
            args = []
            for field in msg.field:
                if is_array(field):
                    if for_client:
                        arg_type = f"TArrayView<const {parse_only_type_name(field)}* const>"
                    else:
                        arg_type = f"std::span<const {parse_only_type_name(field)}*>"
                    args.append(f"{arg_type}{{ {msg.name}Message.{field.name}().data(), {msg.name}Message.{field.name}().size()}}")
                elif for_client and field.type == FieldDescriptorProto.TYPE_STRING:
                    args.append(f"FString{{UTF8_TO_TCHAR({msg.name}Message.{field.name}().c_str())}}")
                else:
                    args.append(f"{msg.name}Message.{field.name}()")
            out.write(f"                    static_cast<TDerivedStub*>(this)->On{msg.name}({make_context_argument(not for_client, len(args) > 0)}")
            out.write(", ".join(a for a in args))
            out.write(");\n")
            out.write(f"                    return;\n")
            out.write(f"                }}\n")

        out.write(f"                default:\n")
        out.write(f"                {{\n")
        out.write(f"                    static_cast<TDerivedStub*>(this)->OnUnknownMessageType({make_context_argument(not for_client)}static_cast<{name}MessageType>({camel_to_pascal_if('messageType', for_client)}));\n")
        out.write(f"                    return;\n")
        out.write(f"                }}\n")
        out.write(f"            }}\n\n")
        out.write(f"        }}\n")
        out.write(f"    }};\n")
        out.write(f"}}\n")
        out.write(f"#endif")
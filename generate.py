import os
import subprocess
import glob
import re
from google.protobuf import descriptor_pb2

import sys

class ParsedMessage:
    def __init__(self, proto_msg):
        self.fields = [f for f in proto_msg.field]
        self.name = proto_msg.name

        if len(self.fields) == 0:
            self.fields = None


for_client = False
if 'for_client' in sys.argv:
    for_client = True

uint16_type = "uint16" if for_client else "uint16_t"
size_type = "SIZE_T" if for_client else "size_t"
int32_type = "int32" if for_client else "int32_t"
uint32_type = "uint32" if for_client else "uint32_t"
int64_type = "int64" if for_client else "int64_t"
uint64_type = "uint64" if for_client else "uint64_t"
string_type = "FString" if for_client else "std::string"
bool_type = "bool"
context_parameter = "uint32_t context, " if not for_client else ""
context_parameter_definition = "const uint32_t context,\n" if not for_client else ""
context_argument = "context, " if not for_client else ""
message_type_name = "MessageType" if for_client else "messageType"
body_size_name = "BodySize" if for_client else "bodySize"
body_name = "Body" if for_client else "body"

proto_input_dir = "In"
proto_output_dir = "Out"
proto_files = []

def snake_to_camel(snake_case_string):
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), snake_case_string)

def snake_to_pascal(snake_case_string):
    words = snake_case_string.split('_')
    pascal_words = [word.capitalize() for word in words]
    return ''.join(pascal_words)

def run_protoc():
    if os.path.exists(proto_output_dir):
        print(f"출력 폴더 비우는 중: {proto_output_dir}")
        for filename in os.listdir(proto_output_dir):
            file_path = os.path.join(proto_output_dir, filename)
            if os.path.isdir(file_path):
                os.rmdir(file_path)
            else:
                os.remove(file_path)
    else:
        print(f"출력 폴더 생성: {proto_output_dir}")
        os.makedirs(proto_output_dir)

    print(".proto 컴파일 중...")
    subprocess.run(["protoc", f'--cpp_out={proto_output_dir}', f'--proto_path={proto_input_dir}', f'--descriptor_set_out={proto_output_dir}\\all.desc', f'In\\*.proto'])

def parameter_type(field):
    t = field.type
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_INT32:
        return int32_type
    elif t == descriptor_pb2.FieldDescriptorProto.TYPE_UINT32:
        return uint32_type
    elif t == descriptor_pb2.FieldDescriptorProto.TYPE_INT64:
        return int64_type
    elif t == descriptor_pb2.FieldDescriptorProto.TYPE_UINT64:
        return uint64_type
    elif t == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
        return string_type # 언리얼의 경우 const를 떼어야 하므로 대입함
    elif t == descriptor_pb2.FieldDescriptorProto.TYPE_BOOL:
        return bool_type
    elif t == descriptor_pb2.FieldDescriptorProto.TYPE_ENUM:
        full_enum_path = field.type_name.lstrip('.')
        cpp_enum_name = full_enum_path.replace('.', '::') 
        parts = field.type_name.split('.')
        if len(parts) >= 2:
            if parts[-2] and parts[-1]:
                cpp_enum_name = f"{parts[-2]}_{parts[-1]}"
            else:
                cpp_enum_name = parts[-1]
        else:
            cpp_enum_name = parts[-1]
        return cpp_enum_name

    return "UNKNOWN_TYPE"

def generate_protocol():
    # RatkiniaProtocol
    with open("Out\\RatkiniaProtocol.gen.h", "w", encoding="utf-8") as out:
        fds = descriptor_pb2.FileDescriptorSet()
        with open(f"{proto_output_dir}\\all.desc", 'rb') as f:
            fds.ParseFromString(f.read())

        out.write("// Auto-generated from Ratkinia Protocol Generator.\n\n")
        out.write("#ifndef RATKINIA_PROTOCOL_H\n#define RATKINIA_PROTOCOL_H\n\n")
        out.write("#include <cstdint>\n\n")
        out.write("namespace RatkiniaProtocol\n")
        out.write("{\n")
        out.write("    struct MessageHeader final\n")
        out.write("    {\n")
        out.write("        " + uint16_type + " MessageType;\n")
        out.write("        " + uint16_type + " BodySize;\n")
        out.write("    };\n\n")
        out.write("    constexpr " + size_type + " MessageMaxSize = 1024 + sizeof(MessageHeader);\n")
        out.write("    constexpr " + size_type + " MessageHeaderSize = sizeof(MessageHeader);\n")

        # 메시지 enum 정의 
        for file_proto in fds.file:
            out.write(f"\n    enum class {os.path.splitext(os.path.basename(file_proto.name))[0]}MessageType : uint16_t\n")
            out.write("    {\n")
            for idx, msg in enumerate(file_proto.message_type):
                out.write(f"        {msg.name} = {idx},\n")
            out.write("    };\n")
        out.write("}\n\n")
        out.write(f"#endif")

    # proto별 Stub, Proxy
    for file_proto in fds.file:
        parsed_messages = []
        for msg in file_proto.message_type:
            parsed_messages.append(ParsedMessage(msg))

        # 네임스페이스 이름: 파일명 (확장자 제외)
        ns = os.path.splitext(os.path.basename(file_proto.name))[0]

        # Stub
        with open(f"Out\\{ns}Stub.gen.h", "w", encoding="utf-8") as out:
            out.write("// Auto-generated from Ratkinia Protocol Generator.\n\n")
            out.write(f"#ifndef {ns.upper()}STUB_GEN_H\n")
            out.write(f"#define {ns.upper()}STUB_GEN_H\n\n")
            out.write("#include \"RatkiniaProtocol.gen.h\"\n")
            out.write(f"#include \"{ns}.pb.h\"\n\n")

            out.write(f"namespace RatkiniaProtocol \n")
            out.write(f"{{\n")
            out.write(f"    template<typename TDerivedStub>\n")
            out.write(f"    class {ns}Stub\n")
            out.write(f"    {{\n")
            out.write(f"    public:\n")
            out.write(f"        virtual ~{ns}Stub() = default;\n\n")
            out.write(f"        virtual void OnUnknownMessageType(" + context_parameter + f"{ns}MessageType " + message_type_name + ") = 0;\n\n")
            out.write(f"        virtual void OnParseMessageFailed(" + context_parameter + f"{ns}MessageType " + message_type_name + ") = 0;\n\n")
            if for_client:
                out.write(f"        virtual void OnUnhandledMessageType({ns}MessageType " + message_type_name + ") = 0;\n\n")

            for msg in parsed_messages:
                out.write(f"        virtual void On{msg.name}(" + context_parameter)
                if msg.fields:
                    params = []
                    for field in msg.fields:
                        type_name = parameter_type(field)
                        param_name = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)

                        # const 붙이기
                        if not for_client or field.type != descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
                            type_name = "const " + type_name

                        # & 붙이기
                        if not for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
                            type_name += "&"

                        # 언리얼 bool b 접두사 붙이기
                        if for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_BOOL:
                            param_name = "b" + param_name

                        params.append(f"{type_name} {param_name}")
                    out.write(", ".join(params))
                if not for_client:
                    out.write(f") = 0;\n\n")
                else:
                    out.write(f") {{ static_cast<TDerivedStub*>(this)->OnUnhandledMessageType({ns}MessageType::{msg.name}); }}\n\n")

            out.write(f"        void Handle{ns}(\n")
            out.write(f"{context_parameter_definition}")
            out.write(f"            const " + uint16_type + " " + message_type_name + ",\n")
            out.write(f"            const " + uint16_type + " " + body_size_name + ",\n")
            out.write(f"            const char* const " + body_name + ")\n")
            out.write(f"        {{\n")
            out.write(f"            switch (static_cast<int32_t>(" + message_type_name + "))\n")
            out.write(f"            {{\n")

            for msg in parsed_messages:
                # args = []
                # for field in msg.field:
                #     pname = field.name
                #     if for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
                #         args.append("FString{UTF8_TO_TCHAR(" + field.name + ".c_str())}")
                #     else:
                #         args.append(pname)

                out.write(f"                case static_cast<int32_t>({ns}MessageType::{msg.name}):\n")
                out.write(f"                {{\n")
                out.write(f"                    {msg.name} {msg.name}Message;\n")
                out.write(f"                    if (!{msg.name}Message.ParseFromArray(" + body_name + ", " + body_size_name + "))\n")
                out.write(f"                    {{\n")
                out.write(f"                        static_cast<TDerivedStub*>(this)->OnParseMessageFailed(" + context_argument + f"static_cast<{ns}MessageType>(" + message_type_name + "));\n")
                out.write(f"                        return;\n")
                out.write(f"                    }}\n")
                out.write(f"                    static_cast<TDerivedStub*>(this)->On{msg.name}(" + context_argument)
                if msg.fields:
                    args = []
                    for field in msg.fields:
                        if for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
                            args.append(f"FString{{UTF8_TO_TCHAR({msg.name}Message.{field.name}().c_str())}}")
                        else:
                            args.append(f"{msg.name}Message.{field.name}()")
                    out.write(", ".join(a for a in args))
                out.write(");\n")
                out.write(f"                    return;\n")
                out.write(f"                }}\n")

            out.write(f"                default:\n")
            out.write(f"                {{\n")
            out.write(f"                    static_cast<TDerivedStub*>(this)->OnUnknownMessageType(" + context_argument + f"static_cast<{ns}MessageType>(" + message_type_name + "));\n")
            out.write(f"                    return;\n")
            out.write(f"                }}\n")
            out.write(f"            }}\n\n")
            out.write(f"        }}\n")
            out.write(f"    }};\n")
            out.write(f"}}\n")
            out.write(f"#endif")

        # Proxy
        with open(f"Out\\{ns}Proxy.gen.h", "w", encoding="utf-8") as out:
            out.write("// Auto-generated from all.desc.\n\n")
            out.write(f"#ifndef {ns.upper()}PROXY_GEN_H\n")
            out.write(f"#define {ns.upper()}PROXY_GEN_H\n\n")
            out.write(f"#include \"{ns}.pb.h\"\n")
            out.write("#include \"RatkiniaProtocol.gen.h\"\n\n")

            out.write(f"namespace RatkiniaProtocol \n")
            out.write(f"{{\n")
            out.write(f"    template<typename TDerivedProxy>\n")
            out.write(f"    class {ns}Proxy\n")
            out.write(f"    {{\n")
            out.write(f"    public:")
            # for msg in file_proto.message_type:
            #     params = []
            #     for field in msg.field:
            #         ptype = parameter_type(field)
            #         pname = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)
            #         params.append(f"{ptype} {pname}")
            #     param_list = ", ".join(params)
            for msg in parsed_messages:
                if msg.fields:
                    params = []
                    for field in msg.fields:
                        type_name = "const " + parameter_type(field)
                        param_name = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)

                        # & 붙이기
                        if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
                            type_name += "&"

                        # 언리얼 bool b 접두사 붙이기
                        if for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_BOOL:
                            param_name = "b" + param_name
                            
                        params.append(f"{type_name} {param_name}")
                out.write(f"\n        void {msg.name}(" + context_parameter)
                out.write(f"{', '.join(params)}")
                out.write(")\n")
                out.write(f"        {{\n")
                out.write(f"            class {msg.name} {msg.name}Message;\n")
                for field in msg.fields:
                    arg = snake_to_pascal(field.name) if for_client else snake_to_camel(field.name)
                    if for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_BOOL:
                        arg = "b" + arg
                    if for_client and field.type == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
                        arg = "std::string{TCHAR_TO_UTF8(*" + arg + ")}"
                    out.write(f"            {msg.name}Message.set_{field.name}({arg});\n")
                out.write(f"            static_cast<TDerivedProxy*>(this)->WriteMessage(" + context_argument + f"{ns}MessageType::{msg.name}, {msg.name}Message);\n")
                out.write(f"        }}\n")
            out.write(f"    }};\n")
            out.write("}\n\n")
            out.write(f"#endif")

# .proto 파일들을 찾기
proto_files = glob.glob(os.path.join(proto_input_dir, "*.proto"))
run_protoc()
generate_protocol()


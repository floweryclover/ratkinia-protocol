import os
import subprocess
import glob
import re
from google.protobuf import descriptor_pb2

import sys

force_override = False
if 'force_override' in sys.argv:
    force_override = True

# 경로 설정
proto_input_dir = "In"
proto_output_dir = "Out"
proto_files = []
# .proto 파일들을 찾기

def run_protoc():
    # 출력 폴더가 이미 존재하면 내용 지우기
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

# FieldDescriptorProto.type → C++ 타입 매핑 함수
def cpp_type(field):
    t = field.type
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_INT32:
        return "const int32_t"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_UINT32:
        return "const uint32_t"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_INT64:
        return "const int64_t"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_UINT64:
        return "const uint64_t"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_STRING:
        return "const std::string&"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_BOOL:
        return "const bool"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_ENUM:
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
        return f"const {cpp_enum_name}"
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE:
        return f"const {field.type_name.split('.')[-1]}&"
    # 필요에 따라 나머지 타입도 매핑
    return "/* unknown_type */"

def generate_protocol():
    # RatkiniaProtocol
    with open("Out\\RatkiniaProtocol.gen.h", "w", encoding="utf-8") as out:
        fds = descriptor_pb2.FileDescriptorSet()
        with open(f"{proto_output_dir}\\all.desc", 'rb') as f:
            fds.ParseFromString(f.read())

        out.write("// Auto-generated from all.desc.\n\n")
        out.write("#ifndef RATKINIA_PROTOCOL_H\n#define RATKINIA_PROTOCOL_H\n\n")
        out.write("#include <cstdint>\n\n")
        out.write("namespace RatkiniaProtocol\n")
        out.write("{\n")
        out.write("    struct MessageHeader final\n")
        out.write("    {\n")
        out.write("        uint16_t MessageType;\n")
        out.write("        uint16_t BodyLength;\n")
        out.write("    };\n\n")
        out.write("    constexpr size_t MessageMaxSize = 65535 + sizeof(MessageHeader);\n")
        out.write("    constexpr size_t MessageHeaderSize = sizeof(MessageHeader);\n")

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
        # 네임스페이스 이름: 파일명 (확장자 제외)
        ns = os.path.splitext(os.path.basename(file_proto.name))[0]


        # Stub
        with open(f"Out\\{ns}Stub.gen.h", "w", encoding="utf-8") as out:
            out.write("// Auto-generated from all.desc.\n\n")
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
            out.write(f"        virtual void OnUnknownMessageType(uint64_t context, {ns}MessageType messageType) = 0;\n\n")
            out.write(f"        virtual void OnParseMessageFailed(uint64_t context, {ns}MessageType messageType) = 0;\n\n")
            if not force_override:
                out.write(f"        virtual void OnUnhandledMessageType(uint64_t context, {ns}MessageType messageType) = 0;\n\n")

            for msg in file_proto.message_type:
                params = []
                args = []
                for field in msg.field:
                    pname = field.name
                    ptype = cpp_type(field)
                    params.append(f"{ptype} {pname}")
                    args.append(pname)
                param_list = ", ".join(params)
                out.write(f"        virtual void On{msg.name}(uint64_t context")
                if params:
                    out.write(", " + param_list)
                if force_override:
                    out.write(f") = 0;\n\n")
                else:
                    out.write(f") {{ static_cast<TDerivedStub*>(this)->OnUnhandledMessageType(context, {ns}MessageType::{msg.name}); }}\n\n")

            out.write(f"        void Handle{ns}(\n")
            out.write(f"            const uint64_t context,\n")
            out.write(f"            const uint16_t messageType,\n")
            out.write(f"            const uint16_t bodySize,\n")
            out.write(f"            const char* const body)\n")
            out.write(f"        {{\n")
            out.write(f"            switch (static_cast<int32_t>(messageType))\n")
            out.write(f"            {{\n")

            for msg in file_proto.message_type:
                params = []
                args = []
                for field in msg.field:
                    pname = field.name
                    ptype = cpp_type(field)
                    params.append(f"{ptype} {pname}")
                    args.append(pname)
                param_list = ", ".join(params)

                out.write(f"                case static_cast<int32_t>({ns}MessageType::{msg.name}):\n")
                out.write(f"                {{\n")
                out.write(f"                    {msg.name} {msg.name}Message;\n")
                out.write(f"                    if (!{msg.name}Message.ParseFromArray(body, bodySize))\n")
                out.write(f"                    {{\n")
                out.write(f"                        static_cast<TDerivedStub*>(this)->OnParseMessageFailed(context, static_cast<{ns}MessageType>(messageType));\n")
                out.write(f"                        return;\n")
                out.write(f"                    }}\n")
                out.write(f"                    static_cast<TDerivedStub*>(this)->On{msg.name}(context")
                if params:
                    out.write(", " + ", ".join(f"{msg.name}Message.{a}()" for a in args))
                out.write(");\n")
                out.write(f"                    return;\n")
                out.write(f"                }}\n")

            out.write(f"                default:\n")
            out.write(f"                {{\n")
            out.write(f"                    static_cast<TDerivedStub*>(this)->OnUnknownMessageType(context, static_cast<{ns}MessageType>(messageType));\n")
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
            for msg in file_proto.message_type:
                params = []
                args = []
                for field in msg.field:
                    pname = field.name
                    ptype = cpp_type(field)
                    params.append(f"{ptype} {pname}")
                    args.append(pname)
                param_list = ", ".join(params)
                out.write(f"\n        void {msg.name}(const uint64_t context, {param_list})\n")
                out.write(f"        {{\n")
                out.write(f"            class {msg.name} {msg.name}Message;\n")
                for field in msg.field:
                    out.write(f"            {msg.name}Message.set_{field.name}({field.name});\n")
                out.write(f"            static_cast<TDerivedProxy*>(this)->WriteMessage(context, {ns}MessageType::{msg.name}, {msg.name}Message);\n")
                out.write(f"        }}\n")
            out.write(f"    }};\n")
            out.write("}\n\n")
            out.write(f"#endif")

# .proto 파일들을 찾기
proto_files = glob.glob(os.path.join(proto_input_dir, "*.proto"))
run_protoc()
generate_protocol()


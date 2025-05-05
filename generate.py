import os
import subprocess
import glob
import re
from google.protobuf import descriptor_pb2

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
    # 메시지 타입이면 그대로 레퍼런스
    if t == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE:
        return f"const {field.type_name.split('.')[-1]}&"
    # 필요에 따라 나머지 타입도 매핑
    return "/* unknown_type */"

def generate_protocol_header():
    with open("Out\\RatkiniaProtocol.h", "w", encoding="utf-8") as out:
        fds = descriptor_pb2.FileDescriptorSet()
        with open(f"{proto_output_dir}\\all.desc", 'rb') as f:
            fds.ParseFromString(f.read())

        out.write("#ifndef RATKINIA_PROTOCOL_H\n#define RATKINIA_PROTOCOL_H\n")
        out.write("// desc 파일로부터 자동 생성됨.\n\n")
        for file_proto in fds.file:
            out.write(f"#include \"{os.path.splitext(os.path.basename(file_proto.name))[0]}.pb.h\"\n")
        out.write("#include <cstdint>\n\n")
        out.write("namespace RatkiniaProtocol\n{\n")
        out.write("    struct MessageHeader final\n")
        out.write("    {\n")
        out.write("        uint16_t MessageType;\n")
        out.write("        uint16_t BodyLength;\n")
        out.write("    };\n\n")
        out.write("    constexpr size_t MessageMaxSize = 65535 + sizeof(MessageHeader);\n")
        out.write("    constexpr size_t MessageHeaderSize = sizeof(MessageHeader);\n}\n\n")
        
        for file_proto in fds.file:
            # 네임스페이스 이름: 파일명 (확장자 제외)
            ns = os.path.splitext(os.path.basename(file_proto.name))[0]

            # 핸들러 시그니처 정의
            for msg in file_proto.message_type:
                params = []
                for field in msg.field:
                    pname = field.name
                    ptype = cpp_type(field)
                    params.append(f"{ptype} {pname}")
                param_list = ", ".join(params)
                out.write(f"#define {ns.upper()}_{msg.name.upper()}_HANDLER bool On{msg.name}(const uint64_t context")
                if params:
                    out.write(", " + ", ".join(f"{p}" for p in params))
                out.write(")\n")
            out.write("\n")
        
            # 네임스페이스 정의
            out.write(f"namespace RatkiniaProtocol::{ns} \n{{\n")
            out.write("    enum class MessageType : uint16_t \n    {\n")
            
            # 메시지 enum 정의 
            for idx, msg in enumerate(file_proto.message_type):
                out.write(f"        {msg.name} = {idx},\n")
            out.write("    };\n\n")

            # 핸들러 디스패처 정의
            out.write(f"    template<typename T{ns}Handler>\n")
            out.write(f"    bool Handle{ns}(\n")
            out.write(f"        T{ns}Handler& {ns}Handler,\n")
            out.write(f"        const uint64_t context,\n")
            out.write(f"        const uint16_t messageType,\n")
            out.write(f"        const uint16_t bodySize,\n")
            out.write(f"        const char* const body)\n")
            out.write(f"    {{\n")
            out.write(f"        switch (static_cast<int32_t>(messageType))\n")
            out.write(f"        {{\n")

            for msg in file_proto.message_type:
                args = []
                for field in msg.field:
                    pname = field.name
                    ptype = cpp_type(field)
                    args.append(pname)
                arg_list   = ", ".join(args)

                out.write(f"            case static_cast<int32_t>(MessageType::{msg.name}):\n")
                out.write(f"            {{\n")
                out.write(f"                {msg.name} {msg.name}Message;\n")
                out.write(f"                if (!{msg.name}Message.ParseFromArray(body, bodySize))\n")
                out.write(f"                {{\n")
                out.write(f"                    {ns}Handler.OnParseMessageFailed(context, messageType);\n")
                out.write(f"                    return false;\n")
                out.write(f"                }}\n")
                out.write(f"                return {ns}Handler.On{msg.name}(context")
                if params:
                    out.write(", " + ", ".join(f"{msg.name}Message.{a}()" for a in args))
                out.write(");\n")
                out.write(f"            }}\n\n")

            out.write(f"        {ns}Handler.OnUnknownMessageType(context, messageType);\n")
            out.write(f"        return false;\n")
            out.write(f"        }}\n")
            out.write(f"    }}\n\n")

            # 메시지 직렬화 함수 정의
            params = []
            for field in msg.field:
                pname = field.name
                ptype = cpp_type(field)
                params.append(f"{ptype} {pname}")
            param_list = ", ".join(params)

            out.write(f"    template<typename T{ns}Writer>\n")
            out.write(f"    bool Write{msg.name}To(T{ns}Writer& {ns}Writer, {param_list})\n")
            out.write(f"    {{\n")
            out.write(f"        {msg.name} {msg.name}Message;\n")
            for field in msg.field:
                out.write(f"        {msg.name}Message.set_{field.name}({field.name});\n")
            out.write(f"        return {ns}Writer.WriteMessage({msg.name}Message);\n")
            out.write(f"    }}\n")

            out.write("}\n\n")

        out.write(f"#endif")

# .proto 파일들을 찾기
proto_files = glob.glob(os.path.join(proto_input_dir, "*.proto"))
run_protoc()

generate_protocol_header()


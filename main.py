import sys
import os
import subprocess
import glob
import re
import datetime
import shutil

from client_api_patch import client_api_patch
from generate_protocol import generate_protocol as generate_protocol_impl
from generate_component_order import generate_component_order as generate_component_order_impl
from generate_stub import generate_stub
from generate_proxy import generate_proxy
from generate_message_type import generate_message_type
from utils import *
from client_types import client_types
from server_types import server_types

from google.protobuf import descriptor_pb2
from google.protobuf.descriptor_pb2 import FieldDescriptorProto, DescriptorProto, FileDescriptorProto, FileDescriptorSet

proto_files = []
client_copy_dir = "..\\ratkinia-client\\Source\\RatkiniaProtocol\\Private"
server_copy_dir = "..\\ratkinia-server\\Source\\RatkiniaProtocol"

def clear_dir(dir: str):
    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        if os.path.isdir(file_path):
            clear_dir(os.path.join(dir, filename))
            os.rmdir(file_path)
        else:
            os.remove(file_path)

def get_output_include_dir(for_client: bool):
    return "Out\\Client\\Include" if for_client else "Out\\Server\\Include"

def get_types(for_client: bool):
    return client_types if for_client else server_types

def generate_component_message_proto(top_comment: str):
    def to_snake(text: str):
        return re.sub(r'(?<!^)([A-Z])', r'_\1', text).lower()
    
    subprocess.run(["protoc", "--cpp_out=Out\\Intermediate", '--proto_path=In', '--descriptor_set_out=Out\\Components.desc', 'In\\Components\\Components.proto'])
    components_fds = descriptor_pb2.FileDescriptorSet()
    with open(f"Out\\Components.desc", 'rb') as f:
        components_fds.ParseFromString(f.read())

    with open("In\\Components\\ComponentMessage.gen.proto", "w") as f:
        f.write(top_comment)
        f.write(f"syntax = \"proto3\";\n")
        f.write(f"option optimize_for = LITE_RUNTIME;\n")
        f.write(f"package RatkiniaProtocol;\n\n")
        f.write(f"import \"Components/Components.proto\";\n\n")
        f.write(f"message ComponentVariant {{\n")
        f.write(f"    oneof value {{\n")

        field_number = 1
        for fd in components_fds.file:
            for msg in fd.message_type:
                f.write(f"        {msg.name} {to_snake(msg.name)} = {field_number};\n")
                field_number += 1

        f.write(f"    }}\n")
        f.write(f"}}\n\n")
    subprocess.run(["protoc", '--cpp_out=Out\\Intermediate', '--proto_path=In', 'In\\Components\\ComponentMessage.gen.proto'])

# src_dir의 모든 하위 폴더까지 검색하며 dst_dir에는 파일만 존재하도록 복사함.
# ext가 None이 아닐 경우(ex h) 해당 확장자 파일만 복사, None인 경우 모든 파일 복사.
def copy_files(src_dir: str, dst_dir: str, ext: str=None, unpack: bool = False):
    for filename in os.listdir(src_dir):
        file_path = os.path.join(src_dir, filename)

        if os.path.isdir(file_path):
            if unpack:
                copy_files(file_path, dst_dir, ext, unpack)
            else:
                if not os.path.exists(f"{dst_dir}\\{filename}"):
                    os.mkdir(f"{dst_dir}\\{filename}")
                copy_files(file_path, f"{dst_dir}\\{filename}", ext)
            continue
        if ext is not None and os.path.isfile(file_path) and os.path.splitext(filename)[1] != f".{ext}":
            continue
            
        shutil.copy2(file_path, os.path.join(dst_dir, filename))

def run_protoc():
    subprocess.run(["protoc", '--cpp_out=Out\\Intermediate', '--proto_path=In', '--descriptor_set_out=Out\\Rpc.desc', 'In\\*.proto'])

def generate_protocol(top_comment: str, for_client: bool):
    generate_protocol_impl(version, get_output_include_dir(for_client), top_comment, get_types(for_client), for_client)

def generate_rpc(top_comment: str, for_client: bool):
    output_include_dir = get_output_include_dir(for_client)
    rpc_fds = descriptor_pb2.FileDescriptorSet()
    with open(f"Out\\Rpc.desc", 'rb') as f:
        rpc_fds.ParseFromString(f.read())

    types = get_types(for_client)
    
    for rpc_fd in rpc_fds.file:
        name = os.path.splitext(os.path.basename(rpc_fd.name))[0]

        generate_message_type(output_include_dir,
                              top_comment,
                              types,
                              name,
                              rpc_fd.message_type)
        
        generate_stub(output_include_dir,
                      top_comment,
                      types,
                      for_client,
                      name,
                      rpc_fd.message_type)

        generate_proxy(output_include_dir,
                       top_comment,
                       types,
                       for_client,
                       name,
                       rpc_fd.message_type)
        
def generate_component_order(top_comment: str, for_client: bool):
    component_fds = descriptor_pb2.FileDescriptorSet()
    with open(f"Out\\Components.desc", 'rb') as f:
        component_fds.ParseFromString(f.read())
    generate_component_order_impl(get_output_include_dir(for_client), top_comment, for_client, component_fds)
        
version = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
top_comment = f"//\n// {version}. Ratkinia Protocol Generator에 의해 생성됨.\n//\n\n"

clear_dir("Out")
os.mkdir("Out\\Intermediate")
os.mkdir("Out\\Client")
os.mkdir("Out\\Client\\Include")
os.mkdir("Out\\Client\\Src")
os.mkdir("Out\\Server")
os.mkdir("Out\\Server\\Include")
os.mkdir("Out\\Server\\Src")

generate_component_message_proto(top_comment)

run_protoc()

generate_protocol(top_comment, True)
generate_protocol(top_comment, False)

generate_rpc(top_comment, True)
generate_rpc(top_comment, False)

generate_component_order(top_comment, True)
generate_component_order(top_comment, False)

copy_files("Out\\Intermediate", "Out\\Client\\Src", "cc", True)
copy_files("Out\\Intermediate", "Out\\Client\\Include", "h")
# 클라이언트 후처리 - Dllexport
client_api_patch("Out\\Client\\Include\\Components")
client_api_patch("Out\\Client\\Include")

copy_files("Out\\Intermediate", "Out\\Server\\Src", "cc", True)
copy_files("Out\\Intermediate", "Out\\Server\\Include", "h")

copy_files("Out\\Client\\Src", client_copy_dir, unpack=True)
copy_files("Out\\Server\\Src", server_copy_dir, unpack=True)
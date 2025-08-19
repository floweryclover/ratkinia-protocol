import sys
import os
import subprocess
import glob
import re
import datetime
import shutil
from generate_protocol import generate_protocol
from generate_stub import generate_stub
from generate_proxy import generate_proxy
from generate_message_type import generate_message_type
from utils import *
from client_types import client_types
from server_types import server_types
from google.protobuf import descriptor_pb2
from google.protobuf.descriptor_pb2 import FieldDescriptorProto, DescriptorProto

proto_files = []
input_dir = "In"

def copy_to_target(output_dir: str, copy_base_dir: str, for_client: bool):
    for filename in os.listdir(output_dir):
        source_path = os.path.join(output_dir, filename)

        if os.path.isfile(source_path):
            copy_dir = copy_base_dir
            _, ext = os.path.splitext(filename)
            if for_client:
                if ext == ".h":
                    copy_dir = os.path.join(copy_base_dir, "Public", "RatkiniaProtocol")
                else:
                    copy_dir = os.path.join(copy_base_dir, "Private", "RatkiniaProtocol")
            dest_path = os.path.join(copy_dir, filename)
            shutil.copy2(source_path, dest_path)
            print(f"파일 복사 완료: '{filename}'")

def run_protoc(output_dir: str):
    if os.path.exists(output_dir):
        print(f"출력 폴더 비우는 중: {output_dir}")
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isdir(file_path):
                os.rmdir(file_path)
            else:
                os.remove(file_path)
    else:
        print(f"출력 폴더 생성: {output_dir}")
        os.makedirs(output_dir)

    print(".proto 컴파일 중...")
    subprocess.run(["protoc", f'--cpp_out={output_dir}', f'--proto_path={input_dir}', f'--descriptor_set_out={output_dir}\\..\\all.desc', f'In\\*.proto'])

def generate(version: str, for_client: bool):
    if for_client:
        types = client_types
    else:
        types = server_types
    
    if for_client:
        output_dir = "Out\\Client"
    else:
        output_dir = "Out\\Server"
    run_protoc(output_dir)

    proto_fds = descriptor_pb2.FileDescriptorSet()
    with open(f"{output_dir}\\..\\all.desc", 'rb') as f:
        proto_fds.ParseFromString(f.read())

    now = datetime.datetime.now()
    formatted_date = now.strftime('%Y. %m. %d. %H:%M')
    top_comment = f"//\n// {formatted_date}. Ratkinia Protocol Generator에 의해 생성됨.\n//\n\n"

    generate_protocol(version, output_dir, top_comment, types, for_client)
    for proto_fd in proto_fds.file:
        name = os.path.splitext(os.path.basename(proto_fd.name))[0]

        generate_message_type(output_dir,
                              top_comment,
                              types,
                              name,
                              proto_fd.message_type)

        generate_stub(output_dir,
                      top_comment,
                      types,
                      for_client,
                      name,
                      proto_fd.message_type)

        generate_proxy(output_dir,
                       top_comment,
                       types,
                       for_client,
                       name,
                       proto_fd.message_type)

    copy_base_dir = "..\\ratkinia-client\\Source\\Ratkinia" if for_client else "..\\ratkinia-server\\Source\RatkiniaProtocol"
    copy_to_target(output_dir, copy_base_dir, for_client)

proto_files = glob.glob(os.path.join(input_dir, "*.proto"))
version = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")

generate(version, True)
generate(version, False)

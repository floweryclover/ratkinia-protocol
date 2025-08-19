import re
from protocol_types import ProtocolTypes
from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

def make_context_parameter(condition: bool, need_comma: bool=True):
    return f"const uint32_t context{', ' if need_comma else ''}" if condition else ""

def make_context_argument(condition: bool, need_comma: bool=True):
    return f"context{', ' if need_comma else ''}" if condition else ""

def camel_to_pascal_if(text: str, condition: bool):
    if not condition:
        return text
    return text[0].upper() + text[1:]

def get_nested_message_type(message_descriptor: DescriptorProto, nested_message_name: str) -> DescriptorProto:
    for message in message_descriptor.nested_type:
        if message.name == nested_message_name.split(".")[-1]:
            return message
    return None

def is_array(field: DescriptorProto) -> bool:
    return field.label == FieldDescriptorProto.LABEL_REPEATED

def is_trivial_type(field: DescriptorProto) -> bool:
    return field.type != FieldDescriptorProto.TYPE_STRING and not is_array(field)

def parse_only_type_name(field: DescriptorProto) -> str:
    parts = field.type_name.split('.')
    if len(parts) >= 2:
        if parts[-2] and parts[-1]:
            return f"{parts[-2]}_{parts[-1]}"
    return parts[-1]

def snake_to_camel(snake_case_string):
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), snake_case_string)

def snake_to_pascal(snake_case_string):
    words = snake_case_string.split('_')
    pascal_words = [word.capitalize() for word in words]
    return ''.join(pascal_words)

def field_type_to_string(field: DescriptorProto, types: dict) -> str:
    t = field.type
    is_array = field.label == FieldDescriptorProto.LABEL_REPEATED
    if t == FieldDescriptorProto.TYPE_INT32:
        type = types[ProtocolTypes.TYPE_INT32]
    elif t == FieldDescriptorProto.TYPE_UINT32:
        type = types[ProtocolTypes.TYPE_UINT32]
    elif t == FieldDescriptorProto.TYPE_INT64:
        type = types[ProtocolTypes.TYPE_INT64]
    elif t == FieldDescriptorProto.TYPE_UINT64:
        type = types[ProtocolTypes.TYPE_UINT64]
    elif t == FieldDescriptorProto.TYPE_STRING:
        type = types[ProtocolTypes.TYPE_STRING]
    elif t == FieldDescriptorProto.TYPE_BOOL:
        type = types[ProtocolTypes.TYPE_BOOL]
    else:
        type = parse_only_type_name(field)
    
    if is_array:
        type = f"{types[ProtocolTypes.TYPE_SPAN]}<{type}>"
    return type

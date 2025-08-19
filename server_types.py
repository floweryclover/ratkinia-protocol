from protocol_types import ProtocolTypes

server_types = {
    ProtocolTypes.TYPE_INT16: "int16_t",
    ProtocolTypes.TYPE_UINT16: "uint16_t",
    ProtocolTypes.TYPE_INT32: "int32_t",
    ProtocolTypes.TYPE_UINT32: "uint32_t",
    ProtocolTypes.TYPE_INT64: "int64_t",
    ProtocolTypes.TYPE_UINT64: "uint64_t",
    ProtocolTypes.TYPE_SIZE: "size_t",
    ProtocolTypes.TYPE_BOOL: "bool",
    ProtocolTypes.TYPE_STRING: "std::string",
    ProtocolTypes.TYPE_SPAN: "std::span",
}
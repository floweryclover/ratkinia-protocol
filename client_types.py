from protocol_types import ProtocolTypes

client_types = {
    ProtocolTypes.TYPE_INT16: "int16",
    ProtocolTypes.TYPE_UINT16: "uint16",
    ProtocolTypes.TYPE_INT32: "int32",
    ProtocolTypes.TYPE_UINT32: "uint32",
    ProtocolTypes.TYPE_INT64: "int64",
    ProtocolTypes.TYPE_UINT64: "uint64",
    ProtocolTypes.TYPE_SIZE: "SIZE_T",
    ProtocolTypes.TYPE_BOOL: "bool",
    ProtocolTypes.TYPE_STRING: "FString",
    ProtocolTypes.TYPE_SPAN: "TArrayView",
}
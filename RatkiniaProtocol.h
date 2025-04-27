#ifndef RATKINIAPROTOCOL__H
#define RATKINIAPROTOCOL__H

#include <cstdint>

namespace RatkiniaProtocol
{
    struct MessageHeader final
    {
        uint16_t MessageType;
        uint16_t BodyLength;
    };

    constexpr size_t MessageMaxSize = 65535 + sizeof(MessageHeader);
    constexpr size_t MessageHeaderSize = sizeof(MessageHeader);

    namespace Cts
    {
        enum class MessageType : uint16_t
        {
            Unknown,
            LoginRequest
        };
    }

    namespace Stc
    {
        enum class MessageType : uint16_t
        {
            Unknown,
            LoginResponse
        };
    }
}

#endif
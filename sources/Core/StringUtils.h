/*
 * StringUtils.h
 *
 * Copyright (c) 2015 Lukas Hermanns. All rights reserved.
 * Licensed under the terms of the BSD 3-Clause license (see LICENSE.txt).
 */

#ifndef LLGL_STRING_UTILS_H
#define LLGL_STRING_UTILS_H


#include <LLGL/Export.h>
#include "Exception.h"
#include <string>
#include <vector>
#include <stdarg.h>


#define LLGL_STRING_PRINTF(OUTPUT, FORMAT)                          \
    {                                                               \
        va_list args1, args2;                                       \
        va_start(args1, FORMAT);                                    \
        va_copy(args2, args1);                                      \
        {                                                           \
            LLGL::StringPrintf((OUTPUT), (FORMAT), args1, args2);   \
        }                                                           \
        va_end(args2);                                              \
        va_end(args1);                                              \
    }


namespace LLGL
{


/* ----- Templates ----- */

// Returns the specified integral value as hexadecimal string.
template <typename T, T Radix>
const char* IntToStr(T value, const char* prefix = nullptr)
{
    static_assert(std::is_integral<T>::value, "IntToStr<T>: template parameter 'T' must be an integral type");
    static_assert(Radix == 2 || Radix == 8 || Radix == 10 || Radix == 16, "IntToStr<T>: radix must be 2, 8, 10, or 16");

    constexpr std::size_t maxPrefixLen  = 2;
    constexpr std::size_t maxLen        = 64;

    static_assert(sizeof(T)*8 <= maxLen, "IntToStr<T>: exceeded limit of digits");

    /* Use static thread-local buffer for output to avoid deadling with synchronization */
    static thread_local char str[maxLen + maxPrefixLen + 1];

    /* Copy prefix into beginning of output string first */
    std::size_t prefixOffset = 0;
    if (prefix != nullptr)
    {
        for (; prefixOffset < maxPrefixLen && prefix[prefixOffset] != '\0'; ++prefixOffset)
            str[prefixOffset] = prefix[prefixOffset];
    }

    /* Get number of digits from lookup table */
    constexpr int digitsPerByte[] = { 0, 0, 8, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 2 };
    int numLen = static_cast<int>(sizeof(T)) * digitsPerByte[Radix];

    /* Append NUL-terminator at end of string */
    str[prefixOffset + numLen] = '\0';

    /* Insert hex digits from right-to-left */
    constexpr char alphabet[] = "0123456789ABCDEF";

    while (numLen > 0)
    {
        --numLen;
        str[prefixOffset + numLen] = alphabet[value % Radix];
        value /= Radix;
    }

    return str;
}

// Returns the specified integral value as hexadecimal string.
template <typename T>
const char* IntToHex(T value, const char* prefix = "0x")
{
    return IntToStr<T, 16>(value, prefix);
}

// Returns the length of the specified null-terminated string.
template <typename T>
inline std::size_t StrLength(const T* s)
{
    std::size_t len = 0;
    while (*s++ != 0)
        ++len;
    return len;
}


/* ----- Functions ----- */

// Reads the specified text file into a string.
LLGL_EXPORT std::string ReadFileString(const char* filename);

// Reads the specified binary file into a buffer.
LLGL_EXPORT std::vector<char> ReadFileBuffer(const char* filename);

// Converts the UTF16 input string to UTF8 string.
LLGL_EXPORT std::string ToUTF8String(const std::wstring& utf16);
LLGL_EXPORT std::string ToUTF8String(const wchar_t* utf16);

// Converts the UTF8 input string to UTF16 string.
LLGL_EXPORT std::wstring ToUTF16String(const std::string& utf8);
LLGL_EXPORT std::wstring ToUTF16String(const char* utf8);

// Writes a formatted string into an STL string.
LLGL_EXPORT void StringPrintf(std::string& str, const char* format, va_list args1, va_list args2);


} // /namespace LLGL


#endif



// ================================================================================

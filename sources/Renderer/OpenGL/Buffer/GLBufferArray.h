/*
 * GLBufferArray.h
 * 
 * This file is part of the "LLGL" project (Copyright (c) 2015-2017 by Lukas Hermanns)
 * See "LICENSE.txt" for license information.
 */

#ifndef LLGL_GL_BUFFER_ARRAY_H
#define LLGL_GL_BUFFER_ARRAY_H


#include <LLGL/BufferArray.h>
#include "../OpenGL.h"
#include <vector>


namespace LLGL
{


class Buffer;

class GLBufferArray : public BufferArray
{

    public:

        GLBufferArray(const BufferType type);
        GLBufferArray(const BufferType type, unsigned int numBuffers, Buffer* const * bufferArray);

        //! Returns the array of buffer IDs.
        inline const std::vector<GLuint>& GetIDArray() const
        {
            return idArray_;
        }

    protected:

        void BuildArray(unsigned int numBuffers, Buffer* const * bufferArray);

    private:

        std::vector<GLuint> idArray_;

};


} // /namespace LLGL


#endif



// ================================================================================

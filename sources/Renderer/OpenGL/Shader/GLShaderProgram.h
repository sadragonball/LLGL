/*
 * GLShaderProgram.h
 *
 * Copyright (c) 2015 Lukas Hermanns. All rights reserved.
 * Licensed under the terms of the BSD 3-Clause license (see LICENSE.txt).
 */

#ifndef LLGL_GL_SHADER_PROGRAM_H
#define LLGL_GL_SHADER_PROGRAM_H


#include <LLGL/ShaderReflection.h>
#include "GLShaderPipeline.h"
#include "GLShaderUniform.h"


namespace LLGL
{


struct GLShaderAttribute;
class GLShaderBindingLayout;

class GLShaderProgram final : public GLShaderPipeline
{

    public:

        void Bind(GLStateManager& stateMngr) override;
        void BindResourceSlots(const GLShaderBindingLayout& bindingLayout) override;
        void QueryInfoLogs(Report& report) override;

    public:

        GLShaderProgram(
            std::size_t             numShaders,
            const Shader* const*    shaders,
            GLShader::Permutation   permutation = GLShader::PermutationDefault
        );
        ~GLShaderProgram();

    public:

        // Returns true if the native GL shader program was linked successfully.
        static bool GetLinkStatus(GLuint program);

        // Returns the native GL shader program log.
        static std::string GetGLProgramLog(GLuint program);

        // Invokes glBindAttribLocation on the specified program for all vertex attributes.
        static void BindAttribLocations(GLuint program, std::size_t numVertexAttribs, const GLShaderAttribute* vertexAttribs);

        // Invokes glBindFragDataLocation on the specified program for all fragment attributes.
        static void BindFragDataLocations(GLuint program, std::size_t numFragmentAttribs, const GLShaderAttribute* fragmentAttribs);

        // Links the specified GL program and binds the transform feedback varyings.
        static void LinkProgramWithTransformFeedbackVaryings(GLuint program, std::size_t numVaryings, const char* const* varyings);

        // Simply links the GL program.
        static void LinkProgram(GLuint program);

        // Queries the shader reflection for the specified program.
        static void QueryReflection(GLuint program, GLenum shaderStage, ShaderReflection& reflection);

    private:

        const GLShaderBindingLayout*    bindingLayout_          = nullptr;

        #ifdef __APPLE__
        bool                            hasNullFragmentShader_  = false;
        #endif

};


} // /namespace LLGL


#endif



// ================================================================================

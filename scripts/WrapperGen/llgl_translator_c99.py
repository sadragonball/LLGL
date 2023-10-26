#
# llgl_translator_c99.py
#
# Copyright (c) 2015 Lukas Hermanns. All rights reserved.
# Licensed under the terms of the BSD 3-Clause license (see LICENSE.txt).
#

from llgl_translator import *

class C99Translator(Translator):
    def translateModule(self, doc):
        def translateDependency(inType):
            if inType.baseType in [StdType.BOOL]:
                return '<stdbool.h>', True
            elif inType.baseType in [StdType.INT8, StdType.INT16, StdType.INT32, StdType.INT64, StdType.UINT8, StdType.UINT16, StdType.UINT32, StdType.UINT64]:
                return '<stdint.h>', True
            elif inType.baseType in [StdType.SIZE_T]:
                return '<stddef.h>', True
            elif inType.baseType in [StdType.CHAR, StdType.WCHAR, StdType.LONG, StdType.FLOAT]:
                return None, True
            return f'<LLGL-C/{inType.typename}Flags.h>', False

        def translateIncludes(typeDeps):
            stdIncludes = set()
            llglIncludes = LLGLMeta.includes.copy()
            for dep in typeDeps:
                inc = translateDependency(dep)
                if inc and inc[0]:
                    if inc[1]:
                        stdIncludes.add(inc[0])
                    #else:
                    #    llglIncludes.add(inc[0])
            return stdIncludes, llglIncludes

        self.statement('/*')
        self.statement(' * {}.h'.format(doc.name))
        self.statement(' *')
        for line in LLGLMeta.copyright:
            self.statement(' * ' + line)
        self.statement(' */')
        self.statement()
        for line in LLGLMeta.info:
            self.statement('/* {} */'.format(line))
        self.statement()

        # Write header guard
        headerGuardName = 'LLGL_C99{}_H'.format(Translator.convertNameToHeaderGuard(doc.name))
        self.statement('#ifndef ' + headerGuardName)
        self.statement('#define ' + headerGuardName)
        self.statement()
        self.statement()

        # Write all include directives
        includeHeaders = translateIncludes(doc.typeDeps)
        if len(includeHeaders[0]) > 0 or len(includeHeaders[1]) > 0:
            for headers in includeHeaders:
                for inc in headers:
                    self.statement('#include {}'.format(inc))

            for external in LLGLMeta.externals:
                if external.cond and external.include:
                    self.statement()
                    self.statement(f'#if {external.cond}')
                    self.statement(f'#   include {external.include}')
                    self.statement(f'#endif /* {external.cond} */')

            self.statement()
            self.statement()

        # Write all constants
        constStructs = list(filter(lambda record: record.hasConstFieldsOnly(), doc.structs))

        if len(constStructs) > 0:
            self.statement('/* ----- Constants ----- */')
            self.statement()

            for struct in constStructs:
                # Write struct field declarations
                declList = Translator.DeclarationList()
                for field in struct.fields:
                    declList.append(Translator.Declaration('', 'LLGL_{}_{}'.format(struct.name.upper(), field.name.upper()), field.init))

                for decl in declList.decls:
                    self.statement('#define ' + decl.name + declList.spaces(1, decl.name) + ' ( ' + decl.init + ' )')
                self.statement()

            self.statement()

        # Write all enumerations
        sizedTypes = dict()

        if len(doc.enums) > 0:
            self.statement('/* ----- Enumerations ----- */')
            self.statement()

            for enum in doc.enums:
                if enum.base:
                    bitsize = enum.base.getFixedBitsize()
                    if bitsize > 0:
                        sizedTypes[enum.name] = bitsize

                self.statement('typedef enum LLGL{}'.format(enum.name))
                self.openScope()

                # Write enumeration entry declarations
                declList = Translator.DeclarationList()
                for field in enum.fields:
                    declList.append(Translator.Declaration('', 'LLGL{}{}'.format(enum.name, field.name), field.init))

                for decl in declList.decls:
                    if decl.init:
                        self.statement(decl.name + declList.spaces(1, decl.name) + '= ' + decl.init + ',')
                    else:
                        self.statement(decl.name + ',')

                self.closeScope()
                self.statement('LLGL{};'.format(enum.name))
                self.statement()

            self.statement()

        # Write all flags
        if len(doc.flags) > 0:
            def translateFlagInitializer(basename, init):
                s = init
                s = re.sub(r'([a-zA-Z_]\w*)', 'LLGL{}{}'.format(basename, r'\1'), s)
                s = re.sub(r'(\||<<|>>|\+|\-|\*|\/)', r' \1 ', s)
                return s

            def translateFieldName(name):
                exceptions = [
                    ('LLGLCPUAccessReadWrite', None) # Identifier for LLGL::CPUAccessFlags::ReadWrite is already used for LLGL::CPUAccess::ReadWrite
                ]
                for exception in exceptions:
                    if name == exception[0]:
                        return exception[1]
                return name


            self.statement('/* ----- Flags ----- */')
            self.statement()

            for flag in doc.flags:
                self.statement('typedef enum LLGL{}'.format(flag.name))
                basename = flag.name[:-len('Flags')]
                self.openScope()

                # Write flag entry declarations
                declList = Translator.DeclarationList()
                for field in flag.fields:
                    fieldName = translateFieldName(f'LLGL{basename}{field.name}')
                    if fieldName:
                        declList.append(Translator.Declaration('', fieldName, translateFlagInitializer(basename, field.init) if field.init else None))

                for decl in declList.decls:
                    if decl.init:
                        self.statement(decl.name + declList.spaces(1, decl.name) + '= ' + decl.init + ',')
                    else:
                        self.statement(decl.name + ',')

                self.closeScope()
                self.statement('LLGL{};'.format(flag.name))
                self.statement()

            self.statement()

        # Write all structures
        commonStructs = list(filter(lambda record: not record.hasConstFieldsOnly(), doc.structs))

        if len(commonStructs) > 0:
            def translateStructField(fieldType, name):
                nonlocal sizedTypes
                typeStr = ''
                declStr = ''

                # Write type specifier
                if fieldType.isDynamicArray() and not fieldType.isPointerOrString():
                    typeStr += 'const '

                if fieldType.typename in [LLGLMeta.UTF8STRING, LLGLMeta.STRING]:
                    typeStr += 'const char*'
                elif fieldType.baseType == StdType.STRUCT and fieldType.typename in LLGLMeta.interfaces:
                    typeStr += 'LLGL' + fieldType.typename
                else:
                    if fieldType.isConst:
                        typeStr += 'const '
                    if fieldType.baseType == StdType.STRUCT and not fieldType.externalCond:
                        typeStr += 'LLGL'
                    typeStr += fieldType.typename
                    if fieldType.isPointer:
                        typeStr += '*'
                
                if fieldType.isDynamicArray():
                    typeStr += ' const*' if fieldType.isPointerOrString() else '*'

                # Write field name
                declStr += name

                # Write optional bit size for enumerations with underlying type (C does not support explicit underlying enum types)
                bitsize = sizedTypes.get(fieldType.typename)
                if bitsize:
                    declStr += f' : {bitsize}'

                # Write fixed size array dimension
                if fieldType.arraySize > 0:
                    declStr += f'[{fieldType.arraySize}]'

                return (typeStr, declStr)

            def translateFieldInitializer(fieldType, init):
                if fieldType.isDynamicArray():
                    return 'NULL'
                if init:
                    if init == 'nullptr':
                        return 'LLGL_NULL_OBJECT' if fieldType.isInterface() else 'NULL'
                    else:
                        return re.sub(r'(\w+::)', r'LLGL\1', init).replace('::', '').replace('|', ' | ').replace('Flags', '')
                return None

            self.statement('/* ----- Structures ----- */')
            self.statement()

            for struct in commonStructs:
                self.statement('typedef struct LLGL{}'.format(struct.name))
                self.openScope()

                # Write struct field declarations
                declList = Translator.DeclarationList()
                for field in struct.fields:
                    # Write two fields for dynamic arrays
                    externalCond = field.type.externalCond
                    if externalCond:
                        declList.append(Translator.Declaration(inDirective = f'#if {externalCond}'))
                    if field.type.isDynamicArray():
                        declList.append(Translator.Declaration('size_t', f'num{field.name[0].upper()}{field.name[1:]}', '0'))
                    declStr = translateStructField(field.type, field.name)
                    declList.append(Translator.Declaration(
                        declStr[0],
                        declStr[1],
                        translateFieldInitializer(field.type, field.init),
                        inComment = 'DEPRECATED' if field.isDeprecated else None)
                    )
                    if externalCond:
                        declList.append(Translator.Declaration(inDirective = f'#endif /* {externalCond} */'))

                for decl in declList.decls:
                    if decl.directive:
                        self.statement(decl.directive)
                    elif decl.comment:
                        self.statement(f'{decl.type}{declList.spaces(0, decl.type)}{decl.name};{declList.spaces(1, decl.name)}/* {decl.comment} */')
                    elif decl.init:
                        self.statement(f'{decl.type}{declList.spaces(0, decl.type)}{decl.name};{declList.spaces(1, decl.name)}/* = {decl.init} */')
                    else:
                        self.statement(f'{decl.type}{declList.spaces(0, decl.type)}{decl.name};')
                self.closeScope()
                self.statement('LLGL{};'.format(struct.name))
                self.statement()

            self.statement()

        self.statement('#endif /* {} */'.format(headerGuardName))
        self.statement()
        self.statement()
        self.statement()
        self.statement('/* ================================================================================ */')
        self.statement()

    def translateModuleToCsharp(self, doc):
        builtinTypenames = {
            StdType.VOID: 'void',
            StdType.BOOL: 'bool',
            StdType.CHAR: 'byte',
            StdType.WCHAR: 'char',
            StdType.INT8: 'sbyte',
            StdType.INT16: 'short',
            StdType.INT32: 'int',
            StdType.INT64: 'long',
            StdType.UINT8: 'byte',
            StdType.UINT16: 'ushort',
            StdType.UINT32: 'uint',
            StdType.UINT64: 'ulong',
            StdType.LONG: 'uint',
            StdType.SIZE_T: 'UIntPtr',
            StdType.FLOAT: 'float',
            StdType.FUNC: 'IntPtr',
        }

        self.statement('/*')
        self.statement(' * {}.cs'.format(doc.name))
        self.statement(' *')
        for line in LLGLMeta.copyright:
            self.statement(' * ' + line)
        self.statement(' */')
        self.statement()
        for line in LLGLMeta.info:
            self.statement('/* {} */'.format(line))
        self.statement()
        self.statement('using System;')
        self.statement('using System.Runtime.InteropServices;')
        self.statement()
        self.statement('namespace LLGL')
        self.openScope()

        # Write all constants
        constStructs = list(filter(lambda record: record.hasConstFieldsOnly(), doc.structs))

        if len(constStructs) > 0:
            self.statement('/* ----- Constants ----- */')
            self.statement()

            for struct in constStructs:
                self.statement('public enum {} : int'.format(struct.name))
                self.openScope()

                # Write struct field declarations
                declList = Translator.DeclarationList()
                for field in struct.fields:
                    declList.append(Translator.Declaration('', field.name, field.init))

                for decl in declList.decls:
                    self.statement(decl.name + declList.spaces(1, decl.name) + ' = ' + decl.init + ',')

                self.closeScope()
                self.statement()

            self.statement()

        # Write all enumerations
        if len(doc.enums) > 0:
            self.statement('/* ----- Enumerations ----- */')
            self.statement()

            for enum in doc.enums:
                self.statement('public enum ' + enum.name)
                self.openScope()

                # Write enumeration entry declarations
                declList = Translator.DeclarationList()
                for field in enum.fields:
                    declList.append(Translator.Declaration('', field.name, field.init))

                for decl in declList.decls:
                    if decl.init:
                        self.statement(decl.name + declList.spaces(1, decl.name) + '= ' + decl.init + ',')
                    else:
                        self.statement(decl.name + ',')

                self.closeScope()
                self.statement()

            self.statement()

        # Write all flags
        if len(doc.flags) > 0:
            def translateFlagInitializer(init):
                s = init
                s = re.sub(r'(\||<<|>>|\+|\-|\*|\/)', r' \1 ', s)
                return s

            self.statement('/* ----- Flags ----- */')
            self.statement()

            for flag in doc.flags:
                self.statement('[Flags]')
                self.statement('public enum {} : uint'.format(flag.name))
                #basename = flag.name[:-len('Flags')]
                self.openScope()

                # Write flag entry declarations
                declList = Translator.DeclarationList()
                for field in flag.fields:
                    declList.append(Translator.Declaration('', field.name, translateFlagInitializer(field.init) if field.init else None))

                for decl in declList.decls:
                    if decl.init:
                        self.statement(decl.name + declList.spaces(1, decl.name) + '= ' + decl.init + ',')
                    else:
                        self.statement(decl.name + ',')

                self.closeScope()
                self.statement()

            self.statement()

        # Write native LLGL interface
        self.statement('internal static class NativeLLGL')
        self.openScope()

        # Write DLL name
        self.statement('#if DEBUG')
        self.statement('const string DllName = "LLGLD";')
        self.statement('#else')
        self.statement('const string DllName = "LLGL";')
        self.statement('#endif')
        self.statement()
        self.statement('#pragma warning disable 0649 // Disable warning about unused fields')
        self.statement()

        # Write all interface handles
        self.statement('/* ----- Handles ----- */')
        self.statement()

        def writeInterfaceCtor(self, interface, parent):
            self.statement(f'public {interface}({parent} instance)')
            self.openScope()
            self.statement('ptr = instance.ptr;')
            self.closeScope()

        def writeInterfaceInterpret(self, interface):
            self.statement(f'public {interface} As{interface}()')
            self.openScope()
            self.statement(f'return new {interface}(this);')
            self.closeScope()

        def writeInterfaceRelation(self, interface, parent, children):
            if interface in children:
                writeInterfaceCtor(self, interface, parent)
                writeInterfaceInterpret(self, parent)
            elif interface == parent:
                for child in children:
                    writeInterfaceCtor(self, parent, child)
                    writeInterfaceInterpret(self, child)

        for interface in LLGLMeta.interfaces:
            self.statement(f'public unsafe struct {interface}')
            self.openScope()
            self.statement('internal unsafe void* ptr;')
            writeInterfaceRelation(self, interface, 'Surface', ['Window', 'Canvas'])
            writeInterfaceRelation(self, interface, 'RenderTarget', ['SwapChain'])
            self.closeScope()
            self.statement()

        self.statement()

        # Write all structures
        commonStructs = list(filter(lambda record: not record.hasConstFieldsOnly(), doc.structs))

        class CsharpDeclaration:
            marshal = None
            type = ''
            ident = ''

            def __init__(self, ident):
                self.marshal = None
                self.type = ''
                self.ident = ident

        def translateDecl(declType, ident = None, isInsideStruct = False):
            decl = CsharpDeclaration(ident)

            def sanitizeTypename(typename):
                nonlocal isInsideStruct
                if typename.startswith(LLGLMeta.typePrefix):
                    return typename[len(LLGLMeta.typePrefix):]
                elif typename in [LLGLMeta.UTF8STRING, LLGLMeta.STRING]:
                    return 'string' if not isInsideStruct else 'byte*'
                else:
                    return typename

            nonlocal builtinTypenames

            if declType.baseType == StdType.STRUCT and declType.typename in LLGLMeta.interfaces:
                decl.type = sanitizeTypename(declType.typename)
            else:
                builtin = builtinTypenames.get(declType.baseType)
                if isInsideStruct:
                    if declType.arraySize > 0 and builtin:
                        decl.type += 'fixed '
                    decl.type += builtin if builtin else sanitizeTypename(declType.typename)
                    if declType.isPointer or declType.arraySize == -1:
                        decl.type += '*'
                    elif declType.arraySize > 0:
                        if builtin:
                            decl.ident += f'[{declType.arraySize}]'
                        else:
                            decl.marshal = '<unroll>'
                    elif declType.baseType == StdType.BOOL:
                        decl.marshal = 'MarshalAs(UnmanagedType.I1)'
                else:
                    decl.type += builtin if builtin else sanitizeTypename(declType.typename)
                    if declType.isPointer or declType.arraySize > 0:
                        if declType.baseType == StdType.STRUCT:
                            decl.marshal = 'ref'
                        elif declType.baseType == StdType.CHAR:
                            decl.type = 'string'
                            decl.marshal = 'MarshalAs(UnmanagedType.LPStr)'
                        elif declType.baseType == StdType.WCHAR:
                            decl.type = 'string'
                            decl.marshal = 'MarshalAs(UnmanagedType.LPWStr)'
                        else:
                            decl.type += '*'

            return decl

        if len(commonStructs) > 0:
            self.statement('/* ----- Structures ----- */')
            self.statement()

            for struct in commonStructs:
                self.statement('public unsafe struct ' + struct.name)
                self.openScope()

                # Write struct field declarations
                declList = Translator.DeclarationList()
                for field in struct.fields:
                    if not field.type.externalCond:
                        # Write two fields for dynamic arrays
                        if field.type.arraySize == -1:
                            declList.append(Translator.Declaration('UIntPtr', 'num{}{}'.format(field.name[0].upper(), field.name[1:])))
                        fieldDecl = translateDecl(field.type, field.name, isInsideStruct = True)
                        if fieldDecl.marshal and fieldDecl.marshal == '<unroll>':
                            for i in range(0, field.type.arraySize):
                                declList.append(Translator.Declaration(fieldDecl.type, f'{fieldDecl.ident}{i}', field.init))
                        else:
                            if fieldDecl.marshal:
                                declList.append(Translator.Declaration(None, fieldDecl.marshal))
                            declList.append(Translator.Declaration(fieldDecl.type, fieldDecl.ident, field.init))

                for decl in declList.decls:
                    if not decl.type:
                        self.statement(f'[{decl.name}]')
                    elif decl.init:
                        self.statement(f'public {decl.type}{declList.spaces(0, decl.type)}{decl.name};{declList.spaces(1, decl.name)}/* = {decl.init} */')
                    else:
                        self.statement(f'public {decl.type}{declList.spaces(0, decl.type)}{decl.name};')
                self.closeScope()
                self.statement()

            self.statement()

        # Write all functions
        if len(doc.funcs) > 0:
            self.statement('/* ----- Functions ----- */')
            self.statement()

            for func in doc.funcs:
                self.statement(f'[DllImport(DllName, EntryPoint="{func.name}", CallingConvention=CallingConvention.Cdecl)]');

                returnType = translateDecl(func.returnType)
                if returnType.type == 'bool':
                    self.statement(f'[return: MarshalAs(UnmanagedType.I1)]')
                elif returnType.marshal:
                    self.statement(f'[return: {returnType.marshal}]')

                paramListStr = ''
                for param in func.params:
                    if len(paramListStr) > 0:
                        paramListStr += ', '
                    paramDecl = translateDecl(param.type, param.name)
                    if paramDecl.marshal:
                        if paramDecl.marshal == 'ref':
                            paramListStr += f'{paramDecl.marshal} '
                        else:
                            paramListStr += f'[{paramDecl.marshal}] '
                    paramListStr += f'{paramDecl.type} {paramDecl.ident}'

                funcName = func.name[len(LLGLMeta.funcPrefix):]
                self.statement(f'public static extern unsafe {returnType.type} {funcName}({paramListStr});');
                self.statement()

        self.statement('#pragma warning restore 0649 // Restore warning about unused fields')
        self.statement()

        self.closeScope()
        self.closeScope()
        self.statement()
        self.statement()
        self.statement()
        self.statement()
        self.statement('// ================================================================================')

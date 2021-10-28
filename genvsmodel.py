#!/usr/bin/env python3

import argparse
import json
import os
import sys
import textwrap

parser = argparse.ArgumentParser(
        description="Generate VeriStand model boilerplate types/functions.")

parser.add_argument("config", metavar="CONFIG", type=argparse.FileType('r'),
        help="JSON model config file (or '-' to read from stdin)")
parser.add_argument("-O", "--outdir", metavar="DIR", type=str,
        default=os.getcwd(),
        help="directory to output files to instead of the working directory")
parser.add_argument("-o", metavar="FILE", type=str, dest='outsrcfile',
        default="model.c",
        help="name of the output model source file (default: %(default)s)")
parser.add_argument("-w", "--indentwidth", metavar="N", type=int,
        default=2,
        help="number of spaces used to indent (default: %(default)s)")
parser.add_argument("-t", "--tabs", action='store_true',
        help="use tabs to instead of spaces to indent generated code")
parser.add_argument("-f", "--force", action='store_true',
        help="overwrite output files if they exist")
parser.add_argument("--stdout", action='store_true',
        help="print generated output to stdout instead of files on disk")

def AddOptGen(name: str, help: str, default: bool = True):
    parser.add_argument(f'--{name}', action=argparse.BooleanOptionalAction,
            dest=f"gen_{name}", default=default, help=help)

AddOptGen("header", "generate model.h")
AddOptGen("src", "generate model source file")

args = parser.parse_args()

config = {}

outsrcfile = os.path.join(args.outdir, args.outsrcfile)
outheaderfile = os.path.join(args.outdir, "model.h")

if not args.stdout and not args.force:
    if args.gen_src and os.path.exists(outsrcfile):
        print(f"Output file {outsrcfile} exists, not overwriting.",
                file=sys.stderr)
        print("Use -f to override this behavior.", file=sys.stderr)
        exit(1)

    if args.gen_header and os.path.exists(outheaderfile):
        print(f"Output file {outheaderfile} exists, not overwriting.",
                file=sys.stderr)
        print("Use -f to override this behavior.", file=sys.stderr)
        exit(1)

config = json.load(args.config)

if not "name" in config:
    print("Error: config does not define a model name", file=sys.stderr)
    exit(1)
else:
    if not str(config["name"]).isidentifier():
        print("Error: model name is not a valid identifier", file=sys.stderr)
        exit(1)

if not "builder" in config:
    print("Error: config does not define a model builder", file=sys.stderr)
    exit(1)
if not "baserate" in config:
    print("Error: config does not define a model baserate", file=sys.stderr)
    exit(1)


def Expand(msg: str):
    msg = textwrap.dedent(msg).strip()
    if not args.tabs:
        return msg.expandtabs(max(0, args.indentwidth))
    else:
        return msg

def GetCategoryAndName(portname: str):
    if not "." in portname and portname.isidentifier():
        return (":default", portname)
    elif "." in portname and len(portname.split(".")) == 2:
        (cat, name) = portname.split(".")
        if cat.isidentifier() and name.isidentifier():
            return (cat, name)
        else:
            # TODO error handling
            return (None, None)
    else:
        return (None, None)

def ParseValueDefs(values, desc=False, types=False):
    outdata = {}

    for valdef in values:
        dimX = 1
        dimY = 1
        cat = None
        name = None
        description = None
        datatype = "double"

        if isinstance(valdef, dict):
            if "name" in valdef:
                (cat, name) = GetCategoryAndName(str(valdef["name"]))
            if desc and "description" in valdef:
                description = str(valdef["description"])
            if types and "type" in valdef:
                datatype = "int32_t" if valdef["type"] == "i32" else "double"
            if "dimX" in valdef:
                dimX = max(1, int(valdef["dimX"]))
            if "dimY" in valdef:
                dimY = max(1, int(valdef["dimY"]))
        elif isinstance(valdef, str):
            (cat, name) = GetCategoryAndName(str(valdef["name"]))

        if not cat is None:
            valdata = {
                    "name": name,
                    "dimX": dimX,
                    "dimY": dimY,
                    }
            if desc:
                if description is None:
                    description = name
                valdata["description"] = description
            if types:
                valdata["type"] = datatype
            if not cat in outdata:
                outdata[cat] = []
            outdata[cat] += [valdata]

    return outdata

def ParsePorts(ports):
    return ParseValueDefs(ports, types=False, desc=False)

def ParseParameters(params):
    return ParseValueDefs(params, types=True, desc=False)

def ParseSignals(signals):
    return ParseValueDefs(signals, desc=True, types=True)

def FmtValueDefsStruct(valuedata, structname: str, types=False):
    outstr = f'typedef struct {structname} {{\n'

    for cat in valuedata:
        indentlevel = 1

        if cat == ":default":
            indentlevel = 1
        else:
            indentlevel = 2
            outstr += f'\tstruct {cat} {{\n'

        for valdef in valuedata[cat]:
            datatype = "double"
            if types and "type" in valdef:
                datatype = valdef["type"]
            outstr += ("\t" * indentlevel) + f'{datatype} {valdef["name"]}'
            if valdef["dimX"] > 1 or valdef["dimY"] > 1:
                outstr += f'[{valdef["dimX"]}]'
            if valdef["dimY"] > 1:
                outstr += f'[{valdef["dimY"]}]'
            outstr += ';\n'

        if indentlevel == 2:
            outstr += f'\t}} {cat};\n'

    outstr += f"}} {structname};\n"
    return outstr

def FmtPortsStruct(ports, structname: str):
    return FmtValueDefsStruct(ports, structname, types=False)

def FmtParametersStruct(params):
    return FmtValueDefsStruct(params, "Parameters", types=True)

def FmtSignalsStruct(signals):
    return FmtValueDefsStruct(signals, "Signals", types=True)

def FmtExtIO(port, category: str, is_input: bool):
    catfield = category + '/' if category != ":default" else ""
    dirfield = 0 if is_input else 1
    dims = f'{port["dimX"]}, {port["dimY"]}'
    return f'{{0, "{catfield}{port["name"]}", 0, {dirfield}, 1, {dims}}}'

def FmtExtIOList(inports, outports):
    inportcount = 0
    outportcount = 0

    if len(inports) > 0:
        for cat in inports:
            inportcount += len(inports[cat])
    if len(outports) > 0:
        for cat in outports:
            outportcount += len(outports[cat])

    outstr = f'int32_t InportSize = {inportcount};\n'
    outstr += f'int32_t OutportSize = {outportcount};\n'
    outstr += 'int32_t ExtIOSize DataSection(".NIVS.extlistsize") = '
    outstr += f'{inportcount + outportcount};\n'
    outstr += f'NI_ExternalIO rtIOAttribs[] DataSection(".NIVS.extlist") = {{\n'

    if inportcount > 0:
        outstr += f'\t/* Inports */\n'
        for cat in inports:
            for port in inports[cat]:
                outstr += f'\t{FmtExtIO(port, cat, True)},\n'
        outstr += '\n'

    if outportcount > 0:
        outstr += f'\t/* Outports */\n'
        for cat in outports:
            for port in outports[cat]:
                outstr += f'\t{FmtExtIO(port, cat, False)},\n'
        outstr += '\n'

    outstr += f'\t/* Terminate list */\n'
    outstr += f'\t{{-1, NULL, 0, 0, 0, 0, 0}},\n}};\n'

    return outstr

def FmtParamAttribs(param, category: str, offset=0):
    catfield = category + '/' if category != ":default" else ""
    namefield = catfield + param['name']
    structoffset = f'offsetof(Parameters, {param["name"]})'
    typefield = 'rtDBL' if param["type"] == "double" else 'rtINT'
    dim = param["dimX"] * param["dimY"]
    return '{{0, "{}", {}, {}, {}, 2, {}, 0}}'.format(
            namefield, structoffset, typefield, dim, offset)

def FmtParamList(params):
    outstr = ''
    paramcount = 0

    for cat in params:
        paramcount += len(params[cat])

    if paramcount > 0:
        outstr += 'extern Parameters rtParameter[2];\n'
        outstr += 'extern int32_t READSIDE;\n'
        outstr += '#define readParam rtParameter[READSIDE]\n\n'

    outstr += 'int32_t ParameterSize DataSection(".NIVS.paramlistsize") = '
    outstr += f'{paramcount};\n'

    if paramcount == 0:
        outstr += 'NI_Parameter rtParamAttribs[1] '
        outstr += 'DataSection(".NIVS.paramlist");\n'
        outstr += 'int32_t ParamDimList[1] DataSection(".NIVS.paramdimlist");\n'
        outstr += 'Parameters initParams DataSection(".NIVS.defaultparams");\n'
        outstr += 'ParamSizeWidth Parameters_sizes[1] '
        outstr += 'DataSection(".NIVS.defaultparamsizes");\n'
    else:
        outstr += 'NI_Parameter rtParamAttribs[] DataSection(".NIVS.paramlist")'
        outstr += ' = {\n'
        offset = 0
        for cat in params:
            for param in params[cat]:
                outstr += f'\t{FmtParamAttribs(param, cat, offset)},\n'
                offset += 2
        outstr += '};\n'

        outstr += 'int32_t ParamDimList[] DataSection(".NIVS.paramdimlist")'
        outstr += ' = {\n'
        for cat in params:
            for param in params[cat]:
                outstr += f'\t{param["dimX"]:>2}, {param["dimY"]:>2}, '
                if cat != ':default':
                    outstr += f'/* {cat}.{param["name"]} */\n'
                else:
                    outstr += f'/* {param["name"]} */\n'
        outstr += '};\n'

        outstr += 'Parameters initParams DataSection(".NIVS.defaultparams")'
        outstr += ' = {\n'
        outstr += f'\t/* Your default parameter values here */\n}};\n'

        outstr += 'ParamSizeWidth Parameters_sizes[] '
        outstr += 'DataSection(".NIVS.defaultparamsizes") = {\n'
        outstr += f'\t{{sizeof(Parameters), 0, 0}},\n'
        for cat in params:
            for param in params[cat]:
                ptype = 'rtDBL' if param["type"] == "double" else 'rtINT'
                dim = param["dimX"] * param["dimY"]
                outstr += f'\t{{sizeof({param["type"]}), {dim}, {ptype}}}, '
                if cat != ':default':
                    outstr += f'/* {cat}.{param["name"]} */\n'
                else:
                    outstr += f'/* {param["name"]} */\n'
        outstr += '};\n'

    return outstr

def FmtSignalAttribs(signal, category: str, offset=0):
    catfield = category + '/' if category != ":default" else ""
    namefield = str(config["name"]) + '/' + catfield + signal['name']
    typefield = 'rtDBL' if signal["type"] == "double" else 'rtINT'
    dim = signal["dimX"] * signal["dimY"]
    return '{{0, "{}", 0, "{}", 0, 0, {}, {}, 2, {}, 0}}'.format(
            namefield, signal["description"], typefield, dim, offset)

def FmtSignalList(signals):
    outstr = ''
    signalcount = 0

    for cat in signals:
        signalcount += len(signals[cat])

    if signalcount > 0:
        outstr += 'Signals rtSignal;\n\n'

    outstr += 'int32_t SignalSize DataSection(".NIVS.siglistsize") = '
    outstr += f'{signalcount};\n'

    if signalcount == 0:
        outstr += 'NI_Signal rtSignalAttribs[1] DataSection(".NIVS.siglist");\n'
        outstr += 'int32_t SigDimList[1] DataSection(".NIVS.sigdimlist");\n'
    else:
        outstr += 'NI_Signal rtSignalAttribs[] DataSection(".NIVS.siglist")'
        outstr += ' = {\n'
        offset = 0
        for cat in signals:
            for sig in signals[cat]:
                outstr += f'\t{FmtSignalAttribs(sig, cat, offset)},\n'
                offset += 2
        outstr += '};\n'

        outstr += 'int32_t SigDimList[] DataSection(".NIVS.sigdimlist") = {\n'
        for cat in signals:
            for sig in signals[cat]:
                outstr += f'\t{sig["dimX"]:>2}, {sig["dimY"]:>2}, '
                if cat != ':default':
                    outstr += f'/* {cat}.{sig["name"]} */\n'
                else:
                    outstr += f'/* {sig["name"]} */\n'
        outstr += '};\n'

    return outstr

def FmtSignalInit(signals):
    if len(signals) == 0:
        return ''

    outstr = '\n'
    i = 0

    for cat in signals:
        for sig in signals[cat]:
            outstr += f'\trtSignalAttribs[{i}].addr = (uintptr_t)'
            prefix = ''
            if sig["dimX"] == 1 and sig["dimY"] == 1:
                prefix = '&'
            elif sig["dimX"] > 1 and sig["dimY"] == 1:
                prefix = ''
            elif sig["dimX"] > 1 and sig["dimY"] > 1:
                prefix = '*'
            catname = '' if cat == ':default' else '.' + cat
            outstr += f'{prefix}rtSignal{catname}.{sig["name"]};\n'
            i += 1

    return outstr


inports = {}
outports = {}
parameters = {}
signals = {}
baserate = float(config["baserate"])
if "inports" in config:
    inports = ParsePorts(config["inports"])
if "outports" in config:
    outports = ParsePorts(config["outports"])
if "parameters" in config:
    parameters = ParseParameters(config["parameters"])
if "signals" in config:
    signals = ParseSignals(config["signals"])


incguard = f'{str(config["name"]).upper()}_MODEL_H'
output_model_h = f'''
#ifndef {incguard}
#define {incguard}

#include <stdint.h>

/* Parameters structure */
{FmtParametersStruct(parameters)}

#endif /* {incguard} */
'''

output_model_src = f'''
#include "ni_modelframework.h"
#include "model.h"

/* User-defined data types for parameters and signals */
#define rtDBL 0
#define rtINT 1
'''

inportsstruct = f'''
/* Inports structure */
{FmtPortsStruct(inports, "Inports")}
'''
if len(inports) > 0:
    output_model_src += inportsstruct

outportsstruct = f'''
/* Outports structure */
{FmtPortsStruct(outports, "Outports")}
'''
if len(outports) > 0:
    output_model_src += outportsstruct

output_model_src += f'''
#ifdef __cplusplus
extern "C" {{
#endif /* __cplusplus */

/* Model info */
const char* USER_ModelName DataSection(".NIVS.compiledmodelname") =
\t\t"{config["name"]}";
const char* USER_Builder DataSection(".NIVS.builder") =
\t\t"{config["builder"]}";


/* Model baserate */
double USER_BaseRate = {baserate};

/* Model task configuration */
NI_Task rtTaskAttribs DataSection(".NIVS.tasklist") = {{0, {baserate}, 0, 0}};


/* Parameters */
{FmtParamList(parameters)}

/* Signals */
{FmtSignalList(signals)}

/* Inports and outports */
{FmtExtIOList(inports, outports)}

int32_t USER_SetValueByDataType(void* ptr, int32_t idx, double value, int32_t type) {{
\tswitch (type) {{
\t\tcase rtDBL:
\t\t\t((double*)ptr)[idx] = (double)value;
\t\t\treturn NI_OK;
\t\tcase rtINT:
\t\t\t((int32_t*)ptr)[idx] = (int32_t)value;
\t\t\treturn NI_OK;
\t}}

\treturn NI_ERROR;
}}

double USER_GetValueByDataType(void* ptr, int32_t idx, int32_t type) {{
\tswitch (type) {{
\t\tcase rtDBL:
\t\t\treturn ((double*)ptr)[idx];
\t\tcase rtINT:
\t\t\treturn (double)(((int32_t*)ptr)[idx]);
\t}}

\t/* Return NaN on error */
\tstatic const uint64_t nan = ~(uint64_t)0;
\treturn *(const double*)&nan;
}}

int32_t USER_Initialize(void) {{{FmtSignalInit(signals)}
\treturn NI_OK;
}}

int32_t USER_ModelStart(void) {{
\treturn NI_OK;
}}

int32_t USER_TakeOneStep(double* inData, double* outData, double timestamp) {{
'''

inportscast = 'const struct Inports* inports = (const struct Inports*)inData;\n'
outportscast = 'struct Outports* outports = (struct Outports*)outData;\n'
if len(inports) > 0:
    output_model_src += '\t' + inportscast
if len(outports) > 0:
    output_model_src += '\t' + outportscast

output_model_src += f'''
\treturn NI_OK;
}}

int32_t USER_ModelFinalize(void) {{
\treturn NI_OK;
}}

#ifdef __cplusplus
}} /* extern "C" */
#endif /* __cplusplus */
'''

if args.gen_header:
    print(Expand(output_model_h),
            file=sys.stdout if args.stdout else open(outheaderfile, 'w'))

if args.gen_src:
    print(Expand(output_model_src),
            file=sys.stdout if args.stdout else open(outsrcfile, 'w'))

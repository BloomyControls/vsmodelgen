#!/usr/bin/env python3

import argparse
import json
import os
import sys
import textwrap

parser = argparse.ArgumentParser(
        description="Generate VeriStand model boilerplate types/functions.",
        usage='%(prog)s [options] CONFIG')

parser.add_argument("config", metavar="CONFIG", type=argparse.FileType('r'),
        help="JSON model config file (or '-' to read from stdin)")

parser.add_argument("-v", "--verbose", action='store_true',
        help="enable verbose output printed to stderr for debugging")

outputargs = parser.add_argument_group('output options',
        'Options controlling the output of the generated source.')
outputargs.add_argument("-f", "--force", action='store_true',
        help="overwrite output files if they exist")
outputargs.add_argument("-O", "--outdir", metavar="DIR", type=str,
        default=os.getcwd(),
        help="directory to output files to instead of the working directory")
outputargs.add_argument("-o", metavar="FILE", type=str, dest='outsrcfile',
        default="model.c",
        help="name of the output model source file (default: %(default)s)")
outputargs.add_argument("-s", "--stdout", action='store_true',
        help="print generated output to stdout instead of files on disk")

genargs = parser.add_argument_group('generation options',
        'Options controlling the generated output.')
genargs.add_argument(f'--header', action=argparse.BooleanOptionalAction,
        dest="gen_header", default=True, help="generate model.h")
genargs.add_argument(f'--src', action=argparse.BooleanOptionalAction,
        dest="gen_src", default=True, help="generate model source file")

formatargs = parser.add_argument_group('formatting options',
        'Options controlling the formatting of the generated source.')
formatargs.add_argument("-t", "--tabs", action='store_true',
        help="use tabs to instead of spaces to indent generated code")
formatargs.add_argument("-w", "--indentwidth", metavar="N", type=int,
        default=2,
        help="number of spaces used to indent (default: %(default)s)")

args = parser.parse_args()

def Vprint(*objects, sep=' ', end='\n'):
    if args.verbose:
        print("info:", *objects, sep=sep, end=end, file=sys.stderr, flush=True)

def Eprint(*objects, sep=' ', end='\n'):
    print(*objects, sep=sep, end=end, file=sys.stderr, flush=True)

def Die(*objects, code=1):
    Eprint("error:", *objects)
    exit(code)

# output source and header file paths
outsrcfile = os.path.join(args.outdir, args.outsrcfile)
outheaderfile = os.path.join(args.outdir, "model.h")

if not args.stdout:
    Vprint("output source file path:", outsrcfile)
    Vprint("output header file path:", outheaderfile)

    if not args.force:
        if args.gen_src and os.path.exists(outsrcfile):
            Eprint(f"output file {outsrcfile} exists, not overwriting")
            Eprint("use -f to override this behavior")
            exit(1)

        if args.gen_header and os.path.exists(outheaderfile):
            Eprint(f"output file {outheaderfile} exists, not overwriting")
            Eprint("use -f to override this behavior")
            exit(1)
    else:
        if args.gen_src and os.path.exists(outsrcfile):
            print(f"note: {outsrcfile} exists and will be overwritten (-f)")

        if args.gen_header and os.path.exists(outheaderfile):
            print(f"note: {outheaderfile} exists and will be overwritten (-f)")
else:
    Vprint("output will be written to stdout")


# load config from JSON file
config = json.load(args.config)

if not "name" in config:
    Die("config does not define a model name")
else:
    if not str(config["name"]).isidentifier():
        Die("model name is not a valid identifier")

if not "builder" in config:
    Die("config does not define a model builder")
if not "baserate" in config:
    Die("config does not define a model baserate")

Vprint(f'model name: {config["name"]}')
Vprint(f'model builder: {config["builder"]}')
Vprint(f'model baserate: {config["baserate"]}')


def Expand(msg: str) -> str:
    """
    Expand tabs as specified by the user.

    :param msg: the string to indent
    :returns: the string with tabs expanded as necessary

    """
    msg = textwrap.dedent(msg).strip()
    if not args.tabs:
        return msg.expandtabs(max(0, args.indentwidth))
    else:
        return msg

def GetCategoryAndName(portname: str) -> (str, str):
    """
    Parse the name of an inport, outport, signal, or parameter into a category
    and a name.

    :param portname: the name of the inport, outport, signal, or parameter

    :returns: a tuple of ("category", "name")

    """
    if not "." in portname:
        if portname.isidentifier():
            return (":default", portname)
        else:
            Die(f"{portname} is not a valid identifier")
    else:
        parts = portname.split(".")
        if len(parts) == 2:
            (cat, name) = parts
            if not cat.isidentifier():
                Die(f"'{portname}': '{cat}' is not a valid identifier")
            elif not name.isidentifier():
                Die(f"'{portname}': '{name}' is not a valid identifier")
            else:
                return (cat, name)
        else:
            Die(f"'{portname}': names cannot contain more than one '.'")

def ParseValueDefs(values, desc=False, types=False) -> dict:
    """
    Parse value definitions (inports, outports, signals, parameters) from the
    JSON config data.

    :param values: array of objects from JSON
    :type values: list
    :param desc: whether or not this value type has a definition field (i.e.
    signals) (Default value = False)
    :param types: whether or not this value type has a type field (i.e. signals
    and parameters) (Default value = False)

    :returns: a dictionary mapping categories to lists of objects containing
    name, dimX>=1, dimY>=1, and optionally a description and a type

    """
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
            else:
                Die("unnamed port, signal, or parameter")

            if desc and "description" in valdef:
                description = str(valdef["description"])

            if types and "type" in valdef:
                if valdef["type"] == "i32":
                    datatype = "int32_t"
                elif valdef["type"] == "double":
                    datatype = "double"
                else:
                    Die(f"'{valdef['name']}': unknown type: {valdef['name']}")

            if "dimX" in valdef:
                dimX = int(valdef["dimX"])
            if "dimY" in valdef:
                dimY = int(valdef["dimY"])
            if dimX < 1:
                Die(f"'{valdef['name']}': dimX cannot be less than 1")
            if dimY < 1:
                Die(f"'{valdef['name']}': dimY cannot be less than 1")
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

def ParsePorts(ports) -> dict:
    """
    Wraps around ParseValueDefs() to parse inports or outports.

    """
    return ParseValueDefs(ports, types=False, desc=False)

def ParseParameters(params) -> dict:
    """
    Wraps around ParseValueDefs() to parse parameters.

    """
    return ParseValueDefs(params, types=True, desc=False)

def ParseSignals(signals) -> dict:
    """
    Wraps around ParseValueDefs() to parse signals.

    """
    return ParseValueDefs(signals, desc=True, types=True)

def FmtValueDefsStruct(valuedata, structname: str, types=False) -> str:
    """
    Format a dict of value definitions (inports, outports, signals, parameters)
    as returned by ParseValueDefs() into a C structure. This will be in the
    format `typedef struct structname {...} structname;`.

    Categories will be represented as sub-structures.

    :param valuedata: dictionary containing definitions of categories and their
    values
    :type valuedata: dict
    :param structname: the name of the struct to create (must be a valid
    C identifier)
    :param types: whether or not to expect a type field in the definition for
    each value

    :returns: a string containing the struct definition

    """
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

def FmtPortsStruct(ports, structname: str) -> str:
    """
    Format a struct for inports or outports using FmtValueDefsStruct().

    :param structname: the name of the struct to create

    """
    return FmtValueDefsStruct(ports, structname, types=False)

def FmtParametersStruct(params) -> str:
    """
    Format a struct for parameters using FmtValueDefsStruct().

    """
    return FmtValueDefsStruct(params, "Parameters", types=True)

def FmtSignalsStruct(signals) -> str:
    """
    Format a struct for signals using FmtValueDefsStruct().

    """
    return FmtValueDefsStruct(signals, "Signals", types=True)

def FmtExtIO(port, category: str, is_input: bool) -> str:
    """
    Format an entry in the generated ExtIO list. The result does not contain
    leading or trailing whitespace.

    :param port: the object containing the inport/outport data
    :type port: dict
    :param category: the category of the inport/outport
    :param is_input: whether or not this is an inport

    :returns: a string containing the generated ExtIO struct

    """
    catfield = category + '/' if category != ":default" else ""
    dirfield = 0 if is_input else 1
    dims = f'{port["dimX"]}, {port["dimY"]}'
    return f'{{0, "{catfield}{port["name"]}", 0, {dirfield}, 1, {dims}}}'

def FmtExtIOList(inports, outports) -> str:
    """
    Generates the ExtIO array from the given inports and outports. Also
    generates the variables defining the number of inports and outports.

    :param inports: list of inports
    :param outports: list of outports

    :returns: a string containing the generated ExtIO array

    """
    inportcount = 0
    outportcount = 0

    if len(inports) > 0:
        for cat in inports:
            inportcount += len(inports[cat])
    if len(outports) > 0:
        for cat in outports:
            outportcount += len(outports[cat])

    Vprint(f"found {inportcount} inports and {outportcount} outports")

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

def FmtParamAttribs(param, category: str, offset=0) -> str:
    """
    Generate a parameter attributes structure for a parameter definition.

    :param param: the parameter object
    :type param: dict
    :param category: the category this parameter is in
    :param offset: the offset field value (starts at 0, should increase by 2 for
    each entry in the list)

    :returns: a string containing the parameter attributes structure to be put
    into the array for VeriStand

    """
    catfield = category + '/' if category != ":default" else ""
    namefield = catfield + param['name']
    structoffset = f'offsetof(Parameters, {param["name"]})'
    typefield = 'rtDBL' if param["type"] == "double" else 'rtINT'
    dim = param["dimX"] * param["dimY"]
    return '{{0, "{}", {}, {}, {}, 2, {}, 0}}'.format(
            namefield, structoffset, typefield, dim, offset)

def FmtParamList(params) -> str:
    """
    Generate the list of parameter attributes and the variables/definitions that
    go along with it.

    :param params: the list of parameter objects
    :type params: list

    :returns: a string containing the generated parameter configuration data

    """
    outstr = ''
    paramcount = 0

    for cat in params:
        paramcount += len(params[cat])

    Vprint(f"found {paramcount} parameters")

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

def FmtSignalAttribs(signal, category: str, offset=0) -> str:
    """
    Generate a signal attributes structure for a signal.

    :param signal: the signal object to use
    :type signal: dict
    :param category: the category this signal is in
    :param offset: the value of the offset field in the entry (should start at
    0 and increase by 2 for each entry)

    :returns a string containing the generated signal attributes structure

    """
    catfield = category + '/' if category != ":default" else ""
    namefield = str(config["name"]) + '/' + catfield + signal['name']
    typefield = 'rtDBL' if signal["type"] == "double" else 'rtINT'
    dim = signal["dimX"] * signal["dimY"]
    return '{{0, "{}", 0, "{}", 0, 0, {}, {}, 2, {}, 0}}'.format(
            namefield, signal["description"], typefield, dim, offset)

def FmtSignalList(signals) -> str:
    """
    Generate the signal list.

    :param signals: the list of signals
    :type signals: list

    :returns: a string containing the generated signal list and related
    configuration data

    """
    outstr = ''
    signalcount = 0

    for cat in signals:
        signalcount += len(signals[cat])

    Vprint(f"found {signalcount} signals")

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

def FmtSignalInit(signals) -> str:
    """
    Generate the code used to configure pointers to signals in the
    initialization function.

    :param signals: list of signals
    :type signals: list

    :returns: the signal initialization code generated (beginning with
    a newline)

    """
    if len(signals) == 0:
        return ''

    outstr = '\n'
    outstr += '\t/* Populate pointers to signal values */\n'
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


# data taken from the config
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

# generate an include guard based on the name of the model
incguard = f'{str(config["name"]).upper()}_MODEL_H'

if args.gen_header:
    Vprint(f"using {incguard} as model.h include guard")

# contents of the model.h file
output_model_h = f'''
#ifndef {incguard}
#define {incguard}

#include <stdint.h>

/* Parameters structure */
{FmtParametersStruct(parameters)}

#endif /* {incguard} */
'''

# model source contents
output_model_src = f'''
#include "ni_modelframework.h"
#include "model.h"

/* User-defined data types for parameters and signals */
#define rtDBL 0
#define rtINT 1
'''

# add inports and outports only if applicable
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

# generate the header and source files and print them to their intended
# destinations (either files or stdout) if they are enabled
if args.gen_header:
    output_model_h = Expand(output_model_h)
    linecount = len(output_model_h.splitlines())
    if args.stdout:
        print(output_model_h, file=sys.stdout)
    else:
        print(output_model_h, file=open(outheaderfile, 'w'))
        print(f"wrote {linecount} lines to {outheaderfile}")

if args.gen_src:
    output_model_src = Expand(output_model_src)
    linecount = len(output_model_src.splitlines())
    if args.stdout:
        print(output_model_src, file=sys.stdout)
    else:
        print(output_model_src, file=open(outsrcfile, 'w'))
        print(f"wrote {linecount} lines to {outsrcfile}")

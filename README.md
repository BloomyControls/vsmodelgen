# C/C++ VeriStand Model Generation Utility

This tool is used to generate a skeleton for a new C/C++ VeriStand model from
a simple JSON description of the inports, outports, signals, and parameters of
the model. Creating a new VeriStand model is a tedious task, and any small error
can cause VeriStand to either fail to load the model or crash entirely.

## Features

This utility generates the required `model.h` header (which defines the
`Parameters` type and any other types required by the model), as well as a bare
source file (compatible with both C and C++) which contains VeriStand's required
interface definitions. This includes:

- Model name, builder, and baserate
- Model task configuration
- Inports and outports
- Signals, including a `USER_Initialize()` function which initializes the
  pointers VeriStand requires for signals (a very tedious process to do by hand)
- Parameters
- Scalar and vector (1D or 2D) values for all of the above
- Two types for parameters and signals (i32 and double)
- Skeleton definitions of required VeriStand interface functions
- Tabs or spaces for indentation (default is 2 spaces)
- Optionally generates a makefile to build the model for VeriStand
  - Optionally generates a batch file to use NI's toolchain to build with the
    generated makefile
  - Supported architectures: Linux x86_64, Windows x86 and x64<sup>\*</sup>
- The generated code stands alone and does not need to be edited, making it safe
  to regenerate without erasing user code
- Generates function prototypes to be defined elsewhere which implement the
  initialize, start, step, and finalize functionality of the model
- Optionally generates a source file containing skeleton definitions for these
  functions, making it easy to get started implementing the model (this file
  will never be overwritten)

It's very likely that you'll need to change your model's parameters, inports,
outports, etc. during development--nobody's right the first time. This requires
regenerating the `model.c` and `model.h` files. In order to avoid overwriting
code, the generated code from this script isolates itself from your code. The
function prototypes in `model.h` can be implemented elsewhere for your model and
don't need to change unless you change specific things. This way you can safely
regenerate the VeriStand model source without accidentally overwriting your
model's code!

<sup>\*</sup> *Building for Windows requires Visual Studio 2017 or newer
installed with the C/C++ build tools included.*

## Usage Example

*Run the script with `-h` or `--help` for a quick reference on all of the
available options.*

Imagine you wish to create a model with the following features:

- An execution rate of 400Hz
- A scaler inport and scalar outport
- A 1D vector inport and 1D vector outport
- A 2D vector inport and 2D vector outport
- Two signals, one 1D vector of i32 and one double
- Two parameters, one i32 and one 2D vector of double

Additionally, you'd like the vector inports and outports to be defined in
a sub-category of the inports and outports (this shows up as a folder in the
list of ports in the VeriStand system definition editor). You'd also like for
the source files to be generated in the `src` subdirectory of your project.
To do all of this, you would write
[this config file](/examples/examplemodel1/model.json) and run the script like
so:

```
mkdir src
python3 genvsmodel.py -O src model.json
```

This will generate `src/model.h` and `src/model.c` from your configuration. For
this example, the generated output can be found
[here](/examples/examplemodel1/src). It might take you an hour or two to write
all that out by hand, and for much more complex models with many inports,
outports, signals, and parameters, it might take many hours to get it right.
Instead, all the hard work has been done for you, and it's up to you to simply
fill in the model's functionality! If you would like to generate the boilerplate
for this, you can then do this:

```
python3 genvsmodel.py -O src --impl --no-src --no-header model.json
```

This will generate a file called `<model_name>.c` (configurable using the `-i`
flag) in the `src` directory which defines the required functions for your
model. You can then edit this file to implement your model without ever having
to interact with the VeriStand interface!

To generate build files for VeriStand 2020 consisting of a Makefile and a batch
script to build the model on Windows, you can do this:

```
python3 genvsmodel.py -O src --makefile --bat --no-src --no-header -V 2020 model.json
```

If you want to combine all of this together, that's trivial as well! You can go
from `model.json` to all of the above files using just the following commands:

```
mkdir src
python3 genvsmodel.py -O src --impl --makefile --bat -V 2020 model.json
```

### Modifying the Model

Let's say you've updated `model.json` and you want to regenerate the model code.
However, you don't want to overwrite the code you've written for the model.
That's easy. Recall that the model implementation file created with `--impl`
will never be overwritten, and its existence means you never have to touch the
auto-generated files. As a result, all it takes is the `--force` flag (or `-f`
for short) to regenerate whatever files you need to!

## Documentation

To see the list of available options when running the script, use `--help` or
`-h`.

For information on the JSON model configuration file, see
[docs/configuration.md](/docs/configuration.md).

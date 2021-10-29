# C/C++ VeriStand Model Generation Utility

This tool is used to generate a skeleton for a new C/C++ VeriStand model from
a simple JSON description of the inports, outports, signals, and parameters of
the model. Creating a new VeriStand model is a tedious task, and any small error
can cause VeriStand to either fail to load the model or crash entirely.

## Features

This utility generates the required `model.h` header (which defines the
`Parameters` type), as well as a bare source file (compatible with both C and
C++) which contains type definitions, VeriStand's required interface
definitions, and so on. This includes:

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
fill in the model's functionality!

## Documentation

To see the list of available options when running the script, use `--help` or
`-h`.

For information on the JSON model configuration file, see
[docs/configuration.md](/docs/configuration.md)

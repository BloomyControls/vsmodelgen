# Model Configuration Specifications

The specification for the JSON file is written as TypeScript interfaces for
clarity and consistency. Here's a quick primer:

An `interface` defines the values which should exist in a JSON object and their
types. Some of these values will be optional, which is specified with a question
mark (`?`). Arrays are specified with a `[]`. The name of the value in the
interface is the name of the JSON key for that data.

## Types

### `Identifier`

The `Identifier` type is a string which contains a valid C identifier. That is,
it must contain only letters, numbers, and underscores, and may not begin with
a number.

```typescript
type Identifier = string;
```

### `CompoundIdentifier`

A specialization of the `Identifier` type which contains a single `.` separating
two identifiers. This is used to create nested inports, outports, signals, and
parameters. At this time, only one level of nesting is allowed, meaning `x.y` is
valid, but `x.y.z` is not.

```typescript
type CompoundIdentifier = `${Indentifier}.${Identifier}`;
```

### `DataType`

Specifies a data type for signals and parameters. Not used for inports or
outports (this is a VeriStand limitation). At the moment, only `double` and
`i32` are available.

```typescript
type DataType = "double" | "i32";
```

## Model Configuration Interface

The overall structure of the JSON file should be one object matching this
interface:

```typescript
/* Entire model configuration object */
interface ModelConfig {
  /* The brief, unique name of the model. */
  name: Identifier;

  /*
   * A longer description of the model. Not sure where VeriStand uses this, but
   * their examples show it as a full name (with spaces, capitals, etc.) and
   * version numbers, company names, etc.
   */
  builder: string;

  /* The model baserate. For example, 400Hz is 0.0025. */
  baserate: number;

  /* List of inports for this model (optional). */
  inports?: Channel[];

  /* List of outports for this model (optional). */
  outports?: Channel[];

  /* List of parameters for this model (optional). */
  parameters?: Parameter[];

  /* List of signals for this model (optional). */
  signals?: Signal[];
}
```

### Channel Interface

All channels (inports, outports, parameters, and signals) share basic
configuration details. As such, they all extend this interface:

```typescript
/* Generic channel interface */
interface Channel {
  /* The name of the channel (optionally compound). */
  name: Identifier | CompoundIdentifier;

  /*
   * The X (first) dimension used for vector channels. Cannot be less than 1.
   * Optional; defaults to 1.
   */
  dimX?: number;

  /*
   * The Y (second) dimension used for vector channels. Cannot be less than 1.
   * Optional; defaults to 1.
   */
  dimY?: number;
}
```

If a channel has an X dimension of 1 (or unspecified) and a Y dimension of 1 (or
unspecified), the channel is a scalar value. For a 1D vector, specify an
X dimension greater than 1 and leave the Y dimension unspecified or 1. For 2D,
specify a Y dimension greater than 1. If the X dimension is 1 and the
Y dimension is greater than 1, you will get a 2D array with dimensions `[1][Y]`.

### Parameters

Parameters can have types other than `double`, so they require an additional
parameter. They also share all of the same channel values as inports and
outports.

```typescript
/* Parameter interface */
interface Parameter extends Channel {
  /*
   * Type of this parameter.
   * Optional; defaults to "double" if unspecified.
   */
  type?: DataType;
}
```

### Signals

Signals, like parameters, can have user-defined types. However, they can also
have a description.

```typescript
/* Signal interface */
interface Signal extends Channel {
  /*
   * Type of this parameter.
   * Optional; defaults to "double" if unspecified.
   */
  type?: DataType;

  /*
   * Description of this signal.
   * Optional; defaults to the signal's name if unspecified.
   */
  description?: string;
}
```

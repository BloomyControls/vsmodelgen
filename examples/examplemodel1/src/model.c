#include "ni_modelframework.h"
#include "model.h"

#include <stddef.h> /* offsetof() */

/* User-defined data types for parameters and signals */
#define rtDBL 0
#define rtINT 1

/* Inports structure */
typedef struct Inports {
  double scalar_in;
  struct Inports_vectors {
    double vector1d_in[8];
    double vector2d_in[2][12];
  } vectors;
} Inports;


/* Outports structure */
typedef struct Outports {
  double scalar_out;
  struct Outports_vectors {
    double vector1d_out[6];
    double vector2d_out[3][5];
  } vectors;
} Outports;


/* Signals structure */
typedef struct Signals {
  int32_t i32_vec_sig[24];
  double double_sig;
} Signals;


#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/* Model info */
const char* USER_ModelName DataSection(".NIVS.compiledmodelname") =
    "my_new_model";
const char* USER_Builder DataSection(".NIVS.builder") =
    "a newly-generated model";


/* Model baserate */
double USER_BaseRate = 0.0025;

/* Model task configuration */
NI_Task rtTaskAttribs DataSection(".NIVS.tasklist") = {0, 0.0025, 0, 0};


/* Parameters */
extern Parameters rtParameter[2];
extern int32_t READSIDE;
#define readParam rtParameter[READSIDE]

int32_t ParameterSize DataSection(".NIVS.paramlistsize") = 2;
NI_Parameter rtParamAttribs[] DataSection(".NIVS.paramlist") = {
  {0, "my_new_model/i32_param", offsetof(Parameters, i32_param), rtINT, 1, 2, 0, 0},
  {0, "my_new_model/double_vec_param", offsetof(Parameters, double_vec_param), rtDBL, 16, 2, 2, 0},
};
int32_t ParamDimList[] DataSection(".NIVS.paramdimlist") = {
   1,  1, /* i32_param */
   4,  4, /* double_vec_param */
};
/* Set default parameter values here */
Parameters initParams DataSection(".NIVS.defaultparams");
ParamSizeWidth Parameters_sizes[] DataSection(".NIVS.defaultparamsizes") = {
  {sizeof(Parameters), 0, 0},
  {sizeof(int32_t), 1, rtINT}, /* i32_param */
  {sizeof(double), 16, rtDBL}, /* double_vec_param */
};


/* Signals */
Signals rtSignal;

int32_t SignalSize DataSection(".NIVS.siglistsize") = 2;
NI_Signal rtSignalAttribs[] DataSection(".NIVS.siglist") = {
  {0, "my_new_model/i32_vec_sig", 0, "an array of integers", 0, 0, rtINT, 24, 2, 0, 0},
  {0, "my_new_model/double_sig", 0, "a double value", 0, 0, rtDBL, 1, 2, 2, 0},
};
int32_t SigDimList[] DataSection(".NIVS.sigdimlist") = {
  24,  1, /* i32_vec_sig */
   1,  1, /* double_sig */
};


/* Inports and outports */
int32_t InportSize = 3;
int32_t OutportSize = 3;
int32_t ExtIOSize DataSection(".NIVS.extlistsize") = 6;
NI_ExternalIO rtIOAttribs[] DataSection(".NIVS.extlist") = {
  /* Inports */
  {0, "scalar_in", 0, 0, 1, 1, 1},
  {0, "vectors/vector1d_in", 0, 0, 1, 8, 1},
  {0, "vectors/vector2d_in", 0, 0, 1, 2, 12},

  /* Outports */
  {0, "scalar_out", 0, 1, 1, 1, 1},
  {0, "vectors/vector1d_out", 0, 1, 1, 6, 1},
  {0, "vectors/vector2d_out", 0, 1, 1, 3, 5},

  /* Terminate list */
  {-1, NULL, 0, 0, 0, 0, 0},
};


int32_t USER_SetValueByDataType(void* ptr, int32_t idx, double value, int32_t type) {
  switch (type) {
    case rtDBL:
      ((double*)ptr)[idx] = (double)value;
      return NI_OK;
    case rtINT:
      ((int32_t*)ptr)[idx] = (int32_t)value;
      return NI_OK;
  }

  return NI_ERROR;
}

double USER_GetValueByDataType(void* ptr, int32_t idx, int32_t type) {
  switch (type) {
    case rtDBL:
      return ((double*)ptr)[idx];
    case rtINT:
      return (double)(((int32_t*)ptr)[idx]);
  }

  /* Return NaN on error */
  static const uint64_t nan = ~(uint64_t)0;
  return *(const double*)&nan;
}

int32_t USER_Initialize(void) {
  /* Populate pointers to signal values */
  rtSignalAttribs[0].addr = (uintptr_t)rtSignal.i32_vec_sig;
  rtSignalAttribs[1].addr = (uintptr_t)&rtSignal.double_sig;

  return NI_OK;
}

int32_t USER_ModelStart(void) {
  return NI_OK;
}

int32_t USER_TakeOneStep(double* inData, double* outData, double timestamp) {
  /*
   * Unused parameters and variables are casted to void to suppress compiler
   * warnings. When you make use of these variables, you should remove these
   * casts. Those likely to be removed are marked with "FIXME".
   */
  const struct Inports* inports = (const struct Inports*)inData;
  (void)inports; /* FIXME */  struct Outports* outports = (struct Outports*)outData;
  (void)outports; /* FIXME */
  (void)timestamp; /* FIXME */
  return NI_OK;
}

int32_t USER_ModelFinalize(void) {
  return NI_OK;
}

#ifdef __cplusplus
} /* extern "C" */
#endif /* __cplusplus */

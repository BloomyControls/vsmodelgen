/*
 * Auto-generated VeriStand model types for my_new_model.
 *
 * Generated Mon Aug 05 13:01:48 2024
 *
 * You almost certainly do NOT want to edit this file, as it may be overwritten
 * at any time!
 */

#ifndef MY_NEW_MODEL_MODEL_H
#define MY_NEW_MODEL_MODEL_H

#include <stdint.h>

/* Parameters structure */
typedef struct Parameters {
  int32_t i32_param;
  double double_vec_param[4][4];
} Parameters;


#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/* Parameters are defined by NI model interface code */
/* Use readParam to access parameters */
extern Parameters rtParameter[2];
extern int32_t READSIDE;
#define readParam rtParameter[READSIDE]

#ifdef __cplusplus
} /* extern "C" */
#endif /* __cplusplus */

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

/* Model signals */
extern Signals rtSignal;

/* Your model code should define these functions. Return NI_OK or NI_ERROR. */
int32_t my_new_model_Initialize(void);
int32_t my_new_model_Start(void);
int32_t my_new_model_Step(const Inports* inports, Outports* outports, double timestamp);
int32_t my_new_model_Finalize(void);

#ifdef __cplusplus
} /* extern "C" */
#endif /* __cplusplus */

#endif /* MY_NEW_MODEL_MODEL_H */

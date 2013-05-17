// oml.i
// SWIG Interface file to play with OML Library
%module oml          // Name of our module
%{
#include "oml2/omlc.h"
#undef omlc_zero_array
void omlc_zero_array(OmlValueU * var, int n) {
  memset(var, 0, n*sizeof(OmlValueU));
}

#if 0
void c_omlc_set_int32(OmlValueU * var, int n, int32_t val) {
  omlc_set_int32(var[n], val);
}

/** \see _omlc_set_intrinsic_value */
#define omlc_set_uint32(var, val) \
  _omlc_set_intrinsic_value(var, uint32, (uint32_t)(val))
/** \see _omlc_set_intrinsic_value */
#define omlc_set_int64(var, val) \
  _omlc_set_intrinsic_value(var, int64, (int64_t)(val))
/** \see _omlc_set_intrinsic_value */
#define omlc_set_uint64(var, val) \
  _omlc_set_intrinsic_value(var, int64, (uint64_t)(val))
/** \see _omlc_set_intrinsic_value */
#define omlc_set_double(var, val) \
  _omlc_set_intrinsic_value(var, double, (double)(val))
#endif


%}
typedef void* o_log_fn;

%typemap(in,numinputs=1) 
  (int *argcPtr, const char **argv)
  (int argc) {
  PyObject *list = $input;
  if(!PySequence_Check(list)) {
    PyErr_SetString(PyExc_TypeError,"need sequence as input");
    return NULL;
  }  
  argc = PySequence_Size(list);
  int i;
  $1 = &argc;
  $2 = malloc(sizeof(char*) * argc);
  for(i=0; i<argc; i++) {
    PyObject *li=PySequence_GetItem(list,i);
    if(!PyString_Check(li))  {
      PyErr_SetString(PyExc_TypeError,"need strings in sequence");
      free($2);
      return NULL;
    }  
    $2[i] = PyString_AsString(li);
  }
}

%typemap(freearg)   
  (int *argcPtr, const char **argv)
{
  free($2);
} 

%typemap(in,numinputs=1) 
 (OmlMPDef *mp_def)
 (int n)
{
  PyObject *list = $input;
  if(!PySequence_Check(list)) {
    PyErr_SetString(PyExc_TypeError,"need sequence as input");
    return NULL;
  }  
  n = PySequence_Size(list);
  int i;
  $1 = malloc(sizeof(OmlMPDef) * (n + 1));
  
  for(i=0; i < n; i++) {
    PyObject *li=PySequence_GetItem(list,i);
    int ok = PyArg_ParseTuple(li, "si", & $1[i].name, & $1[i].param_types); 
    if(!ok)  {
      PyErr_SetString(PyExc_TypeError,"need (string,int) tuples in sequence");
      free($1);
      return NULL;
    }  
  }
  $1[n].name = NULL; 
  $1[n].param_types = 0; 
} 

%typemap(freearg)   
  (OmlMPDef *mp_def)
{
 // free($1);
 // crash at omlc_start
} 

typedef int int32_t;
typedef unsigned int uint32_t;
typedef long long int64_t;
typedef unsigned long long uint64_t;


%include "oml2/omlc.h"

#undef omlc_zero_array

void omlc_zero_array(OmlValueU * var, int n); 


%define declare_set(type, typename)
void c_omlc_set_ ## type(OmlValueU * var, int n, typename val);

%{
void c_omlc_set_ ## type(OmlValueU * var, int n, typename val) {
  omlc_set_ ## type(var[n], val);
}
%}

%enddef

declare_set(int32, int32_t);
declare_set(uint32, uint32_t);
declare_set(int64, int64_t);
declare_set(uint64, uint64_t);
declare_set(double, double);

void c_omlc_set_string(OmlValueU * var, int n, const char * val);
void c_omlc_reset_string(OmlValueU * var, int n);

%{
void c_omlc_set_string(OmlValueU * var, int n, const char *val) {
  // const char *copy = strdup(val);
  omlc_set_string(var[n], val);
}
void c_omlc_reset_string(OmlValueU * var, int n) {
  omlc_reset_string(var[n]);
}

%}


%include <carrays.i>

%array_class(OmlValueU, OmlValueUArray);



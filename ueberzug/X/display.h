#ifndef __DISPLAY_H__
#define __DISPLAY_H__

#include "python.h"

#include <X11/Xlib.h>


typedef struct {
    PyObject_HEAD
    Display *display;
} DisplayObject;
PyTypeObject DisplayType;

#endif

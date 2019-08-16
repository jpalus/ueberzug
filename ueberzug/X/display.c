#include "python.h"

#include <X11/Xlib.h>

#include "util.h"
#include "display.h"


static int
Display_init(DisplayObject *self, PyObject *args, PyObject *kwds) {
    if (self->display != NULL) {
        XCloseDisplay(self->display);
    }

    self->display = XOpenDisplay(NULL);

    if (self->display == NULL) {
        raiseInit(OSError, "could not open a connection to the X server");
    }

    Py_INIT_RETURN_SUCCESS;
}

static void
Display_dealloc(DisplayObject *self) {
    if (self->display != NULL) {
        XCloseDisplay(self->display);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *
Display_wait_for_event(DisplayObject *self) {
    Py_BEGIN_ALLOW_THREADS
    XEvent event;
    XPeekEvent(self->display, &event);
    Py_END_ALLOW_THREADS
    Py_RETURN_NONE;
}

static PyObject *
Display_discard_event(DisplayObject *self) {
    Py_BEGIN_ALLOW_THREADS
    XEvent event;
    XNextEvent(self->display, &event);
    Py_END_ALLOW_THREADS
    Py_RETURN_NONE;
}

static PyMethodDef Display_methods[] = {
    {"wait_for_event", (PyCFunction)Display_wait_for_event,
     METH_NOARGS,
     "Waits for an event to occur. till an event occur."},
    {"discard_event", (PyCFunction)Display_discard_event,
     METH_NOARGS,
     "Discards the first event from the event queue."},
    {NULL}  /* Sentinel */
};

PyTypeObject DisplayType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "ueberzug.X.Display",
    .tp_doc = "X11 display\n",
    .tp_basicsize = sizeof(DisplayObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc)Display_init,
    .tp_dealloc = (destructor)Display_dealloc,
    .tp_methods = Display_methods,
};

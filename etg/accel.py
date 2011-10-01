#---------------------------------------------------------------------------
# Name:        etg/accel.py
# Author:      Kevin Ollivier
#
# Created:     06-Sept-2011
# Copyright:   (c) 2011 by Wide Open Technologies
# License:     wxWindows License
#---------------------------------------------------------------------------

import etgtools
import etgtools.tweaker_tools as tools

PACKAGE   = "wx"
MODULE    = "_core"
NAME      = "accel"   # Base name of the file to generate to for this script
DOCSTRING = ""

# The classes and/or the basename of the Doxygen XML files to be processed by
# this script. 
ITEMS  = [ 'wxAcceleratorEntry', 'wxAcceleratorTable', ]    
    
#---------------------------------------------------------------------------

def run():
    # Parse the XML file(s) building a collection of Extractor objects
    module = etgtools.ModuleDef(PACKAGE, MODULE, NAME, DOCSTRING)
    etgtools.parseDoxyXML(module, ITEMS)
    
    #-----------------------------------------------------------------
    # Tweak the parsed meta objects in the module object as needed for
    # customizing the generated code and docstrings.

    c = module.find('wxAcceleratorEntry')
    assert isinstance(c, etgtools.ClassDef)
    tools.removeVirtuals(c)

    c = module.find('wxAcceleratorTable')
    assert isinstance(c, etgtools.ClassDef)
    tools.removeVirtuals(c)    
       
    # Replace the implementation of the AcceleratorTable ctor so it can
    # accept a Python sequence of tuples or AcceleratorEntry objects like
    # Classic does. Using the arraySize and array annotations does let us
    # pass a list of entries, but they have to already be AccelertorEntry
    # obejcts. We want to allow Items in the list to be either
    # wx.AcceleratorEntry items or a 3-tuple containing the values to pass to
    # the wx.AcceleratorEntry ctor.

    # See EXPERIMENTAL in object.py...
    # First ignore the fact that this class derives from wxObject. This is
    # so there will not be any inherited virtuals, so SIP will not generate a
    # derived class. That makes the adding of a new ctor easier.
    #c.bases = []

    # Ignore the current constructor
    c.find('wxAcceleratorTable').findOverload('entries').ignore()
        
    # and add the code for the new constructor
    c.addCppCtor(
        briefDoc="TODO",
        argsString='(PyObject* entries)', 
        body="""\
    const char* errmsg = "Expected a sequence of 3-tuples or wx.AcceleratorEntry objects.";
    if (!PySequence_Check(entries)) {
        PyErr_SetString(PyExc_TypeError, errmsg);
        return NULL;
    }
    int count = PySequence_Size(entries);
    wxAcceleratorEntry* tmpEntries = new wxAcceleratorEntry[count];
    if (! tmpEntries) {
        PyErr_SetString(PyExc_MemoryError, "Unable to allocate temporary array");
        return NULL;
    }
    int idx;
    for (idx=0; idx<count; idx++) {
        PyObject* obj = PySequence_ITEM(entries, idx);
        if (sipCanConvertToType(obj, sipType_wxAcceleratorEntry, SIP_NO_CONVERTORS)) {
            int err = 0;
            wxAcceleratorEntry* entryPtr = reinterpret_cast<wxAcceleratorEntry*>(
                sipConvertToType(obj, sipType_wxAcceleratorEntry, NULL, 0, 0, &err));
            tmpEntries[idx] = *entryPtr;
        }
        else if (PySequence_Check(obj) && PySequence_Size(obj) == 3) {
            PyObject* o1 = PySequence_ITEM(obj, 0);
            PyObject* o2 = PySequence_ITEM(obj, 1);
            PyObject* o3 = PySequence_ITEM(obj, 2);
            tmpEntries[idx].Set(PyInt_AsLong(o1), PyInt_AsLong(o2), PyInt_AsLong(o3));
            Py_DECREF(o1);
            Py_DECREF(o2);
            Py_DECREF(o3);            
        }
        else {
            PyErr_SetString(PyExc_TypeError, errmsg);
            return NULL;
        }
        Py_DECREF(obj);
    }
    
    wxAcceleratorTable* table = new wxAcceleratorTable(count, tmpEntries);
    delete tmpEntries;
    return table;
    """)

    # Mac doesn't have this, and we don't real with resource files from
    # wxPython anyway.
    c.find('wxAcceleratorTable').findOverload('resource').ignore()
    
    #-----------------------------------------------------------------
    tools.doCommonTweaks(module)
    tools.addGetterSetterProps(module)
    tools.runGenerators(module)
    
    
#---------------------------------------------------------------------------
if __name__ == '__main__':
    run()

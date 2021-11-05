# encoding: utf-8
import inspect
import sys


def extend_module_with_instance_methods(module_name, instance):
    """
    @:param module_name: module
    @:param instance:
    Utility to take the methods of the instance of a class, instance,
    and add them as functions to a module, module_name, so that Fabric
    can find and call them. Call this at the bottom of a module after
    the class definition.

    @see: http://www.saltycrane.com/blog/2010/09/class-based-fabric-scripts-metaprogramming-hack/
    """
    # get the module as an object
    module_obj = sys.modules[module_name]

    # Iterate over the methods of the class and dynamically create a function
    # for each method that calls the method and add it to the current module
    for method in inspect.getmembers(instance, predicate=inspect.ismethod):
        method_name, method_obj = method

        if not method_name.startswith('_'):
            # get the bound method
            func = getattr(instance, method_name)

            # add the function to the current module
            setattr(module_obj, method_name, func)

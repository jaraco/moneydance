Installation
============

Copy or link the modules in this directory into the Moneydance environment.
Moneydance does add the tmp/pythonTemp/Lib to sys.path, so the following
should work in OS X environments:

    ln -s $(pwd) ~/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Application\ Support/Moneydance/tmp/pythonTemp/Lib

Or on xonsh:

    ln -s @($(pwd).strip()) '~/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Application Support/Moneydance/tmp/pythonTemp/Lib'

Usage
=====

Now you should be able to import the modules from the Python Environment.

If you have not already, enable the Python Interpreter extension and launch
the interpreter.

From the interpreter, simply import the module and invoke the desired function:

    import migration
    migration.run(moneydance)

Note that functions may require access to the "moneydance" object, so it is
currently necessary to pass that in from the interpreter's local namespace.

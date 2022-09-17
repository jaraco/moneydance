Installation
============

Using a regular Python interpreter, run `python -m install`.

Usage
=====

Now you should be able to import the modules from MoneyBot.

From MoneyBot, add a snippet to simply import the module and invoke the
desired function. ex:

    import migration
    migration.run(moneydance)

Note that functions may require access to the "moneydance" object, so it is
currently necessary to pass that in from the interpreter's local namespace.

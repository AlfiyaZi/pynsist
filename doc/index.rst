pynsis |version|
================

pynsis is a tool to build Windows installers for your Python applications. The
installers bundle Python itself, so you can distribute your application to
people who don't have Windows installed.

Quickstart
----------

1. Get the tools. Install `NSIS <http://nsis.sourceforge.net/Download>`_, and
   then install pynsis from PyPI by running ``pip install pynsis``.

2. Add this code to the top of your script, above any other imports::

       import sys
       sys.path.insert(0, 'pkgs')

   This will let your installed application find the packages installed with it.

3. Write a config file ``installer.cfg``, like this:

   .. code-block:: ini
   
       [Application]
       name=My App
       version=1.0
       script=myapp.py
       icon=myapp.ico

       [Python]
       version=3.4.0

       [Include]
       # Importable packages that your application requires, one per line
       packages = requests
            bs4
            html5lib

       # Other files and folders that should be installed
       files = LICENSE
           data_files/

  See :doc:`cfgfile` for more details about this.

4. Run ``pynsis installer.cfg`` to generate your installer. If ``pynsis`` isn't
   found, you can use ``python -m nsisbuilder installer.cfg`` instead.

Contents
--------

.. toctree::
   :maxdepth: 2

   cfgfile
   faq

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


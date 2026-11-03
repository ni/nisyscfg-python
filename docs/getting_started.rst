Getting Started
===============

Use a :class:`nisyscfg.Session` to connect to the local system and query
National Instruments hardware:

.. code-block:: python

   import nisyscfg

   with nisyscfg.Session() as session:
       device_filter = session.create_filter()
       device_filter.is_present = True
       device_filter.is_ni_product = True
       device_filter.is_device = True
       for resource in session.find_hardware(device_filter):
           print(resource.expert_user_alias[0])

The NI System Configuration Runtime must be installed for this example to run.

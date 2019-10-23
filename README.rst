About the OS2Rollekataloget Integration
=======================================

This repository contains an integration between OS2MO and OS2Rollekataloget.
It contains a Python script which can either be executed directly, or built
and run as a Docker container using the included Dockerfile.

Configuration
-------------

The integration is configured using environment variables

* ``EMPLOYEE_MAPPING_PATH`` - The location of the mapping between OS2mo UUIDs and AD GUIDs
* ``AD_SYSTEM_NAME`` - The same of the Active Directory system found in OS2mo
* ``OS2MO_URL`` - The URL for OS2mo
* ``OS2MO_API_KEY`` - The API key for OS2mo
* ``ROLLEKATALOG_URL`` - The URL for Rollekataloget
* ``ROLLEKATALOG_API_KEY`` - The API key for Rollekataloget
* ``LOG_PATH`` - The location of the log file (defaults to log.log)

License and Copyright
---------------------

Copyright (c) 2019, Magenta ApS.

OS2MO Tools is free software and may be used, studied, modified and shared
under the terms of `Mozilla Public License, version 2.0
<https://www.mozilla.org/en-US/MPL/>`_. A copy of the license text may
be found in the LICENSE file.


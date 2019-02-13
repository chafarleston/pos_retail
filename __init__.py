# -*- coding: utf-8 -*-
from . import medical
from . import pos
from . import account
from . import product
from . import res
from . import sale
from . import stock
from . import mrp
from . import purchase

import odoo
version_info = odoo.release.version_info
if version_info[0] and version_info[0] == 12:
    from . import v12
else:
    from . import v11

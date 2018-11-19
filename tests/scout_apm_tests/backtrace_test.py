from __future__ import absolute_import, division, print_function, unicode_literals

import scout_apm


def test_traceback():
    bt = scout_apm.core.backtrace.capture()
    for frame in bt:
        keys = list(frame.keys())
        keys.sort()
        assert keys == ["file", "function", "line"]

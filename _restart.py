# _restart.py — warm restart helper (exec'd via WebREPL after OTA upload)
# Purges cached user modules so fresh code loads from flash, then re-runs main.py.
# WiFi + WebREPL stay up because their modules are preserved.
import sys
import gc

_keep = set('sys gc machine network webrepl _webrepl websocket socket'
            ' uos os micropython esp esp32 time struct io json errno'
            ' select binascii hashlib collections re math _thread ssl'
            ' ntptime framebuf btree onewire ds18x20'.split())
n = 0
for _m in list(sys.modules):
    if _m not in _keep:
        del sys.modules[_m]
        n += 1
del _keep
gc.collect()
print('Purged', n, 'modules, free=', gc.mem_free())
exec(open('main.py').read())

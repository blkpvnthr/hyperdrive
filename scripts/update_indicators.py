import os
import sys
sys.path.append('hyperdrive')
from DataSource import Glassnode  # noqa autopep8
from Constants import PathFinder  # noqa autopep8
import Constants as C  # noqa autopep8

counter = 0
glass = Glassnode()

try:
    filename = glass.save_s2f_ratio(
        timeframe='max', retries=1 if C.TEST else 2)
    counter += 1
except Exception as e:
    print('Glassnode S2F update failed.')
    print(e)
finally:
    filename = PathFinder().get_s2f_path()
    if C.CI and os.path.exists(filename):
        os.remove(filename)

try:
    filename = glass.save_diff_ribbon(
        timeframe='max', retries=1 if C.TEST else 2)
    counter += 1
except Exception as e:
    print('Glassnode Diff Ribbon update failed.')
    print(e)
finally:
    filename = PathFinder().get_diff_ribbon_path()
    if C.CI and os.path.exists(filename):
        os.remove(filename)

try:
    filename = glass.save_sopr(timeframe='max', retries=1 if C.TEST else 2)
    counter += 1
except Exception as e:
    print('Glassnode SOPR update failed.')
    print(e)
finally:
    filename = PathFinder().get_sopr_path()
    if C.CI and os.path.exists(filename):
        os.remove(filename)

if counter < 3:
    exit(1)

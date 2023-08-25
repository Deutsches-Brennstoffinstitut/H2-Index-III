import time
from base_python.source.helper.initialize_logger import LoggingLevels

import base_python.base_value_chains.A_RE_Based_Production_H2 as Model_A
import base_python.base_value_chains.B_Grid_Based_Production_H2 as Model_B
import base_python.base_value_chains.C_Methanation as Model_C
import base_python.base_value_chains.D_Pipeline_Transport as Model_D

logging_level = LoggingLevels.DEBUG

all_tests = [Model_A,
             Model_B,
             Model_C,
             Model_D,
             ]
failed_tests = []
for test in all_tests:
    try:
        print(f'Running Test:"{test.__name__}" ...')
        test.run_local(logging_level)
        print(f'Test "{test.__name__}" successful!\n')
    except:
        print(f'Test:"{test.__name__}" failed!\n')
        failed_tests.append(test.__name__)

print(f'\n\nResult: {len(all_tests) - len(failed_tests)} von {len(all_tests)} Tests have been successful.')
time.sleep(2)
if len(failed_tests) > 0:
    print('Failed Tests are:\n')
    for test in failed_tests:
        print(test)

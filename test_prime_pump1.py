import logging
import time

import controller  # Import controller to access globals and functions
from controller import MOTORS, motor_forward, motor_stop, setup_gpio, DEBUG

import settings  # Import settings for any global configs if needed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Duration
PRIME_DURATION = 10  # seconds

# Pump 1 (0-based index)
pump_index = 0
ia, ib = MOTORS[pump_index]

setup_gpio()

try:
    # Prime Pump 1
    logger.info(f'Priming Pump 1 (pins {ia}, {ib}) for {PRIME_DURATION} seconds...')
    motor_forward(ia, ib)
    time.sleep(PRIME_DURATION)
    motor_stop(ia, ib)

except KeyboardInterrupt:
    logger.info('Test interrupted.')
    motor_stop(ia, ib)

finally:
    if not DEBUG:
        for dev in controller.pin_devices.values():
            dev.close()
        controller.pin_devices.clear()
    else:
        logger.debug('Cleanup skipped in debug mode.')

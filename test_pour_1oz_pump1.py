import logging
import time

import controller  # Import controller to access globals and functions
from controller import MOTORS, motor_forward, motor_reverse, motor_stop, setup_gpio, DEBUG

from settings import OZ_COEFFICIENT, RETRACTION_TIME  # Import timing coefficients

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Amount to pour
AMOUNT_OZ = 1.0

# Pump 1 (0-based index)
pump_index = 0
ia, ib = MOTORS[pump_index]

setup_gpio()

try:
    # Calculate pour time
    seconds_to_pour = AMOUNT_OZ * OZ_COEFFICIENT
    if RETRACTION_TIME:
        logger.debug(f'Retraction time is set to {RETRACTION_TIME:.2f} seconds. Adding this time to pour time')
        seconds_to_pour += RETRACTION_TIME

    # Pour from Pump 1
    logger.info(f'Pouring {AMOUNT_OZ} oz from Pump 1 (pins {ia}, {ib}) for {seconds_to_pour:.2f} seconds...')
    motor_forward(ia, ib)
    time.sleep(seconds_to_pour)

    if RETRACTION_TIME:
        logger.info(f'Retracting Pump 1 for {RETRACTION_TIME:.2f} seconds')
        motor_reverse(ia, ib)
        time.sleep(RETRACTION_TIME)

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

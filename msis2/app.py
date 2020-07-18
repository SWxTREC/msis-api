"""MSIS2 API

Inputs to the Fortran subroutine
C        IYD - YEAR AND DAY AS YYDDD (day of year from 1 to 365 (or 366))
C              (Year ignored in current model)
C        SEC - UT(SEC)
C        ALT - ALTITUDE(KM)
C        GLAT - GEODETIC LATITUDE(DEG)
C        GLONG - GEODETIC LONGITUDE(DEG)
C        STL - LOCAL APPARENT SOLAR TIME(HRS; see Note below)
C        F107A - 81 day AVERAGE OF F10.7 FLUX (centered on day DDD)
C        F107 - DAILY F10.7 FLUX FOR PREVIOUS DAY
C        AP - MAGNETIC INDEX(DAILY) OR WHEN SW(9)=-1. :
C           - ARRAY CONTAINING:
C             (1) DAILY AP
C             (2) 3 HR AP INDEX FOR CURRENT TIME
C             (3) 3 HR AP INDEX FOR 3 HRS BEFORE CURRENT TIME
C             (4) 3 HR AP INDEX FOR 6 HRS BEFORE CURRENT TIME
C             (5) 3 HR AP INDEX FOR 9 HRS BEFORE CURRENT TIME
C             (6) AVERAGE OF EIGHT 3 HR AP INDICIES FROM 12 TO 33 HRS PRIOR
C                    TO CURRENT TIME
C             (7) AVERAGE OF EIGHT 3 HR AP INDICIES FROM 36 TO 57 HRS PRIOR
C                    TO CURRENT TIME
C        MASS - MASS NUMBER (ONLY DENSITY FOR SELECTED GAS IS
C                 CALCULATED.  MASS 0 IS TEMPERATURE.  MASS 48 FOR ALL.
C                 MASS 17 IS Anomalous O ONLY.)

Output from the Fortran subroutine
!     OUTPUT VARIABLES:
!       TN     Temperature at altitude (K)
!       DN(1)  Total mass density (kg/m3)
!       DN(2)  N2 number density (m-3)
!       DN(3)  O2 number density (m-3)
!       DN(4)  O number density (m-3)
!       DN(5)  He number density (m-3)
!       DN(6)  H number density (m-3)
!       DN(7)  Ar number density (m-3)
!       DN(8)  N number density (m-3)
!       DN(9)  Anomalous oxygen number density (m-3)
!       DN(10) Not used in NRLMSIS 2.0 (will contain NO in future release)
!       TEX    Exospheric temperature (K) (optional argument)

Initialization of MSIS controlling which options are desired.
Default is for all of them to be set to 1
!                            1 - F10.7
!                            2 - Time independent
!                            3 - Symmetrical annual
!                            4 - Symmetrical semiannual
!                            5 - Asymmetrical annual
!                            6 - Asymmetrical semiannual
!                            7 - Diurnal
!                            8 - Semidiurnal
!                            9 - Geomagnetic activity:
!                                  1.0 = Daily Ap mode
!                                 -1.0 = Storm-time ap mode
!                           10 - All UT/long effects
!                           11 - Longitudinal
!                           12 - UT and mixed UT/long
!                           13 - Mixed Ap/UT/long
!                           14 - Terdiurnal
!                           15-25 - Not used in NRLMSIS 2.0
"""
from datetime import datetime
import json
import sys
import os

import numpy as np

# Have to add the library path into the system's path to find them on load
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(CWD, "lib"))

from msis2 import init_msis, run_msis


def validate_event(event):
    for x in ['dates', 'lons', 'lats', 'alts', 'f107s', 'f107as', 'aps']:
        if x not in event:
            raise ValueError(f"{x} is required as input.")
        if not np.iterable(event[x]):
            raise ValueError(f"{x} must be an iterable.")

    # Validate shapes
    ndates = len(event['dates'])
    if (len(event['f107s']) != ndates or len(event['f107as']) != ndates or
            len(event['aps']) != ndates):
        raise ValueError("Dates, F107, F107a, and Ap must be the same length.")

    MAX_SIZE = 10000
    if (ndates * len(event['lons']) * len(event['lats']) *
            len(event['alts']) > MAX_SIZE):
        raise ValueError("Too many calculations requested. " +
                         f"The maximum number of points is {MAX_SIZE}")


def lambda_handler(event, context):
    """Handle the incoming API event and route properly."""
    # Data is passed in the body, so pull it out of there
    data = json.loads(event['body'])
    # Validate the event
    validate_event(data)

    # Convert the dates
    data['dates'] = [datetime.strptime(x, "%Y-%m-%dT%H:%M") for x in data['dates']]

    # Initialize the model, default is all ones
    options = data.get("options", [1]*25)
    if len(options) != 25:
        raise ValueError("options requires a length 25 array")
    init_msis(options)

    # Call the main loop
    output = run_msis(data['dates'], data['lons'], data['lats'],
                      data['alts'], data['f107s'], data['f107as'],
                      data['aps'])
    return {
        'statusCode': 200,
        'body': json.dumps(output.tolist()),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }


def main():
    """For command line testing."""
    # Call initialization routine only once
    init_msis([1]*25)

    # date = datetime(2001, 2, 2, 8, 3, 36)  # 8.06 hour
    date = datetime(2001, 7, 2, 8, 3, 36)  # 8.06 hour

    alt = 200
    f107 = 146.7
    f107a = 163.6666
    ap = 7
    dates = [date]
    lons = range(-180, 185, 5)
    lats = range(-90, 95, 5)
    alts = [alt]
    f107s = [f107]
    f107as = [f107a]
    aps = [ap]

    event = {'dates': dates, 'lons': lons, 'lats': lats, 'alts': alts,
             'f107s': f107s, 'f107as': f107as, 'aps': aps}
    context = None

    stime = time.time()
    output = lambda_handler(event, context)
    print("output:", output)
    print("Returned time:", time.time()-stime)
    # altitude_profile(date, glat, glon, plot=False)
    # altitude_surface2(date, alt, plot=False, json=True)


if __name__ == "__main__":
    main()
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
import os
import sys

import numpy as np

# Have to add the library path into the system's path to find them on load
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(CWD, "lib"))

from pymsis2 import gml


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
    # Parse the incoming path and route the event properly
    if 'surface' in event['path']:
        return surface_handler(event, context)

    if 'altitude' in event['path']:
        return altitude_handler(event, context)

    # Data is passed in the body, so pull it out of there
    data = json.loads(event['body'])
    # Validate the event
    validate_event(data)

    # Convert the dates
    data['dates'] = [datetime.strptime(x, "%Y-%m-%dT%H:%M")
                     for x in data['dates']]

    # Initialize the model, default is all ones
    options = data.get("options", [1]*25)
    if len(options) != 25:
        raise ValueError("options requires a length 25 array")

    # Call the main loop
    _, output = run_msis(data['dates'], data['lons'], data['lats'],
                         data['alts'], data['f107s'], data['f107as'],
                         data['aps'], options)
    ndates = len(data['dates'])
    nlons = len(data['lons'])
    nlats = len(data['lats'])
    nalts = len(data['alts'])
    nspecies = 11
    return {
        'statusCode': 200,
        'body': json.dumps(output.reshape((ndates, nlons,
                                           nlats, nalts, nspecies)).tolist()),
        "headers": {"Access-Control-Allow-Origin": "*",
                    "content-type": "application/json"}
    }


def surface_handler(event, context):
    """Handle the incoming API event and route properly."""
    # Data is passed in the URL, so pull it out of there
    params = event['queryStringParameters']
    date = datetime.strptime(params['date'], "%Y-%m-%dT%H:%M")
    altitude = float(params['altitude'])
    f107 = float(params['f107'])
    f107a = float(params['f107a'])
    ap = float(params['ap'])
    # Initialize the model, default is all ones
    options = params.get('options', [1]*25)
    if isinstance(options, str):
        # Extract the list input out of the string storage
        options = json.loads(options)

    if len(options) != 25:
        raise ValueError("options requires a length 25 array")
    if isinstance(options, str):
        # Extract the list input out of the string storage
        options = json.loads(options)

    # Make the 5 degree x 5 degree grid (center points)
    lats = [x + 2.5 for x in range(-90, 90, 5)]
    lons = [x + 2.5 for x in range(-180, 180, 5)]

    # Call the main loop
    input_data, output = run_msis([date], lons, lats, [altitude],
                                  [f107], [f107a], [ap], options)

    # input data == (:, (alt, lat, lon))
    features = {"Latitude": input_data[:, 1].tolist(),
                "Longitude": input_data[:, 2].tolist(),
                "Mass": output[:, 0].tolist(),
                "N2": output[:, 1].tolist(),
                "O2": output[:, 2].tolist(),
                "O": output[:, 3].tolist(),
                "He": output[:, 4].tolist(),
                "H": output[:, 5].tolist(),
                "Ar": output[:, 6].tolist(),
                "N": output[:, 7].tolist(),
                "AnomO": output[:, 8].tolist(),
                "NO": output[:, 9].tolist(),
                "Temperature": output[:, 10].tolist()}

    return {
        'statusCode': 200,
        'body': json.dumps(features),
        "headers": {"Access-Control-Allow-Origin": "*",
                    "content-type": "application/json"}
    }


def altitude_handler(event, context):
    """Handle the incoming API event and route properly."""
    # Data is passed in the URL, so pull it out of there
    params = event['queryStringParameters']
    date = datetime.strptime(params['date'], "%Y-%m-%dT%H:%M")
    longitude = float(params['longitude'])
    latitude = float(params['longitude'])
    f107 = float(params['f107'])
    f107a = float(params['f107a'])
    ap = float(params['ap'])
    # Initialize the model, default is all ones
    options = params.get('options', [1]*25)
    if isinstance(options, str):
        # Extract the list input out of the string storage
        options = json.loads(options)

    if len(options) != 25:
        raise ValueError("options requires a length 25 array")

    # Make the list of altitudes to use
    alts = [x for x in range(100, 1005, 5)]

    # Call the main loop
    input_data, output = run_msis([date], [longitude], [latitude], alts,
                                  [f107], [f107a], [ap], options)

    features = {"Altitude": input_data[:, 0].tolist(),
                "Mass": output[:, 0].tolist(),
                "N2": output[:, 1].tolist(),
                "O2": output[:, 2].tolist(),
                "O": output[:, 3].tolist(),
                "He": output[:, 4].tolist(),
                "H": output[:, 5].tolist(),
                "Ar": output[:, 6].tolist(),
                "N": output[:, 7].tolist(),
                "AnomO": output[:, 8].tolist(),
                "NO": output[:, 9].tolist(),
                "Temperature": output[:, 10].tolist()}

    return {
        'statusCode': 200,
        'body': json.dumps(features),
        "headers": {"Access-Control-Allow-Origin": "*",
                    "content-type": "application/json"}
    }


def run_msis(dates, lons, lats, alts, f107s, f107as, aps, options):
    """Call MSIS looping over all possible inputs.

    Parameters
    ----------
    dates : list of dates
        Date and time to calculate the output at.
    lons : list of floats
        Longitudes to calculate the output at.
    lats : list of floats
        Latitudes to calculate the output at.
    alts : list of floats
        Altitudes to calculate the output at.
    f107s : list of floats
        F107 value for the given date(s).
    f107as : list of floats
        F107 running 100-day average for the given date(s).
    aps : list of floats
        Ap for the given date(s).
    options : list of floats (length 25)
        A list of options (switches) to the model
    """
    # 11 == 10 densities + 1 temperature
    # Output density: He, O, N2, O2, Ar, Total (gm/cm3), H, N, Anomalous O
    # Output temp: exospheric, specific altitude
    gml.initswitch(options)

    input_data = np.array([[date.timetuple().tm_yday,
                            date.hour*3600 + date.minute*60 + date.second,
                            alt, lat, lon, f107s[i], f107as[i]] + [aps[i]]*7
                           for i, date in enumerate(dates) for lon in lons
                           for lat in lats for alt in alts])

    output = gml.msiscalc_gml(input_data[:, 0], input_data[:, 1],
                              input_data[:, 2], input_data[:, 3],
                              input_data[:, 4], input_data[:, 5],
                              input_data[:, 6], input_data[:, 7:])

    # Force to float, JSON serializer in future calls does not work
    # with float32 output
    # Return the altitutdes, latitudes, longitudes with the data
    return (input_data[:, 2:5], output.astype(np.float))

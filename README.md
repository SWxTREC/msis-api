# MSIS API

Version 0.1

The [NRLMSIS](https://www.nrl.navy.mil/ssd/branches/7630/modeling-upper-atmosphere) code is developed at the Naval Research Laboratory. It is an empirical code to determine the temperature and density of species in the upper atmosphere.

This API receives requests of times, locations, geomagnetic activity, and other parameters and dispatches those requests to call the Fortran code and deliver the results back to the requestor. This enables easier public access to the research code and results. This API has been developed with AWS's Serverless Application Model (SAM), for details on deploying this API see the [SAM documentation](SAM_README.md)

## Endpoints

There are three separate endpoints for calculating msis parameters.

- [`/msis2`](#/msis2) : POST
  - Generic endpoint to calculate any combination of parameters
- [`/msis2/surface`](#/msis2/surface) : GET
  - Returns a gridded surface product for a specific altitude
- [`/msis2/altitude`](#/msis2/altitude) : GET
  - Returns an altitude profile given a specific latitude and longitude

### /msis2

Computes values at all locations and levels requested in the body of the request. The endpoint has a limit of 10,000 calculation points in a single call.

#### Body of request

The body of the `POST` must contain the following:

- `dates` : list

A list of date and times, the required format is `YYYY-mm-ddTHH:MM`.

- `lons` : list

A list of longitudes, in degrees, between -180 and 360.

- `lats` : list

A list of latitudes, in degrees, between -90 and 90.

- `alts` : list

A list of altitudes, in kilometers, above the surface.

- `f107s` : list

A list of F107 values, the same length as dates.

- `f107as` : list

A list of 81-day centered F107 values, the same length as dates.

- `aps` : list

A list of ap values, the same length as dates.

- `options` : list, optional

A list of length 25 to control the switches that can be selected within the model, by default all options are set to `1`. Details of the [options available are listed here](#options)

#### Example body request

```json
{
    "dates": [
      "2018-01-01T12:00"
    ],
    "lons": [
      0,
      90,
      180,
      270
    ],
    "lats": [
      -90,
      -45,
      0,
      45,
      90
    ],
    "alts": [
      200,
      300
    ],
    "f107s": [
      146.7
    ],
    "f107as": [
      163.6666
    ],
    "aps": [
      7
    ],
    "options": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
}
```

#### Generic outputs

The output from the API is a multi-dimensional list that corresponds to the size of the request. The shape of the returned list will be `[ndates, nlons, nlats, nalts, 11]` with the order corresponding to the input values. The final axis with shape 11 contains the output species density and temperature.

1. Total mass density (kg/m3)
2. N2 number density (m-3)
3. O2 number density (m-3)
4. O number density (m-3)
5. He number density (m-3)
6. H number density (m-3)
7. Ar number density (m-3)
8. N number density (m-3)
9. Anomalous oxygen number density (m-3)
10. Not used in NRLMSIS 2.0 (will contain NO in future release)
11. Temperature at altitude (K)

### /msis2/surface

Computes a gridded surface product for a specific altitude.

#### Surface query parameters

The request uses query parameters for the input data.

- `date` : string

A date and time, the required format is `YYYY-mm-ddTHH:MM`.

- `altitude` : float

An altitude, in kilometers above the surface.

- `f107` : float

An F107 value.

- `f107a` : float

An 81-day centered F107 value.

- `ap` : float

An ap value.

- `options` : list, optional

A list of length 25 to control the switches that can be selected within the model, by default all options are set to `1`. Details of the [options available are listed here](#options)

#### Example surface request

```html
http://127.0.0.1:3000/msis2/surface?date=2018-01-01T12:00&altitude=400&f107=146.7&f107a=163.6666&ap=7&options=[0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
```

#### Surface outputs

The output from the API is a json object that contains an array for each variable.
The object contains the following variables, each with the same length output.

```json
"Latitude": "Latitude of this point (deg)"
"Longitude": "Longitude of this point (deg)"
"Mass": "Total mass density (kg/m3)"
"N2": "N2 number density (m-3)"
"O2": "O2 number density (m-3)"
"O": "O number density (m-3)"
"He": "He number density (m-3)"
"H": "H number density (m-3)"
"Ar": "Ar number density (m-3)"
"N": "N number density (m-3)"
"AnomO": "Anomalous oxygen number density (m-3)"
"NO": "Not used in NRLMSIS 2.0 (will contain NO in future release)"
"Temperature": "Temperature at altitude (K)"
```

### /msis2/altitude

Computes a gridded surface product for a specific altitude.

#### Altitude query parameters

The request uses query parameters for the input data.

- `date` : string

A date and time, the required format is `YYYY-mm-ddTHH:MM`.

- `latitude` : float

A latitude, in degrees, between -90 and 90.

- `longitude` : float

A longitude, in degrees, between -180 and 360.

- `f107` : float

An F107 value.

- `f107a` : float

An 81-day centered F107 value.

- `ap` : float

An ap value.

- `options` : list, optional

A list of length 25 to control the switches that can be selected within the model, by default all options are set to `1`. Details of the [options available are listed here](#options)

#### Example altitude request

```html
http://127.0.0.1:3000/msis2/altitude?date=2018-01-01T12:00&latitude=0&longitude=0&f107=146.7&f107a=163.6666&ap=7&options=[0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
```

#### Altitude outputs

The output from the API is a json object that contains an array for each variable.
The object contains the following variables, each with the same length output.

```json
"Altitude": "Altitude of this point (km)"
"Mass": "Total mass density (kg/m3)"
"N2": "N2 number density (m-3)"
"O2": "O2 number density (m-3)"
"O": "O number density (m-3)"
"He": "He number density (m-3)"
"H": "H number density (m-3)"
"Ar": "Ar number density (m-3)"
"N": "N number density (m-3)"
"AnomO": "Anomalous oxygen number density (m-3)"
"NO": "Not used in NRLMSIS 2.0 (will contain NO in future release)"
"Temperature": "Temperature at altitude (K)"
```

## Options

To test out various effects on the calculation, there are some optional switches that can be selected for the model. These switches can be selected within the API through an extra `options` list.

1. F10.7
2. Time independent
3. Symmetrical annual
4. Symmetrical semiannual
5. Asymmetrical annual
6. Asymmetrical semiannual
7. Diurnal
8. Semidiurnal
9. Geomagnetic activity:
    - 1.0 = Daily Ap mode
    - -1.0 = Storm-time ap mode
10. All UT/long effects
11. Longitudinal
12. UT and mixed UT/long
13. Mixed Ap/UT/long
14. Terdiurnal

15-25 are not used in NRLMSIS 2.0.

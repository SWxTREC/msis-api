# MSIS API

Version 0.1

The [NRLMSIS](https://www.nrl.navy.mil/ssd/branches/7630/modeling-upper-atmosphere) code is developed at the Naval Research Laboratory. It is an empirical code to determine the temperature and density of species in the upper atmosphere.

This API receives requests of times, locations, geomagnetic activity, and other parameters and dispatches those requests to call the Fortran code and deliver the results back to the requestor. This enables easier public access to the research code and results. This API has been developed with AWS's Serverless Application Model (SAM), for details on deploying this API see the [SAM documentation](SAM_README.md)

## Endpoints

Currently, there is a single endpoint that receives the requests and computes values at all locations and levels requested. The endpoint has a limit of 10,000 calculation points in a single call.

- `/msis2` : POST


## Body of request
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

### Optional values

To test out various effects on the calculation, there are some optional switches that can be selected for the model. These switches can be selected within the API through an extra `options` list.

- `options` : list

A list of length 25 to control the switches that can be selected within the model, by default all options are set to `1`. The switches are defined below.

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

### Example body request

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

## Outputs

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


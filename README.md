# mfr24

Unofficial Python SDK for [MyFlightRadar24](https://my.flightradar24.com): fetch any public profile's logged flights as typed data and globe-ready arcs.

> Not affiliated with Flightradar24. Reads public profile data; respect their Terms of Service.

## Install

```bash
pip install mfr24            # SDK + CLI
pip install "mfr24[api]"     # also the FastAPI server
```

## Usage

```python
from mfr24 import MyFlightRadar24Client, arcs, airports, to_globe

client = MyFlightRadar24Client()
flights = client.flights("johndoe")   # list[Flight], newest first
arcs(flights)                         # great-circle routes
airports(flights)                     # unique airports + visit counts
to_globe(flights)                     # {"arcs": [...], "airports": [...]}
```

## CLI

```bash
mfr24 export johndoe -o globe-arcs.json   # write the globe payload
mfr24 serve                               # run the HTTP API (needs the [api] extra)
```

ILSspy - A $15 ILS/VOR receiver using RTL-SDR
===

Experimenting with Python, scipy and d3js libraries.

Installation
---
Python 3.5 or later required. Anaconda distribution is recommended on Windows.

On Raspberry Pi 3 it is recommended to install the latest scipy lib. See
    http://asgaut.blogspot.no/2016/09/installing-optimized-python-scipy.html 

Install the Osmocom RTL-SDR:
    $ sudo apt-get install rtl-SDR

On 64 bit Windows, the files libusb-1.0.dll, pthreadVC2-w64.dll and rtlsdr.dll from the Osmocom 
[pre-built binaries](http://sdr.osmocom.org/trac/attachment/wiki/rtl-sdr/RelWithDebInfo.zip) must 
be in the path. I recommend C:\windows\system32.

Using
---
Run with
    python app.py

Then open [http://localhost:9000/spectrum-rf.html] or [http://localhost:9000/spectrum-lf.html] to view 
the RF spectrum (2.048 MHz bandwidth) or LF spectrum (64 kHz bandwith).

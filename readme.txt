========================================================================
🚀 WI-FI PROFESSIONAL BROADBAND PSD ANALYSIS DASHBOARD
========================================================================
A real-time, high-fidelity RF spectrum analyzer built natively for macOS 
and served instantly as an interactive web-based dashboard via Streamlit.

This application monitors the local physical airwaves, parses nearby Wi-Fi 
infrastructure layers, dynamically calculates co-channel interference power, 
and charts a real-time Power Spectral Density (PSD) envelope for 2.4 GHz and 
5 GHz wireless bands.

------------------------------------------------------------------------
📋 ARCHITECTURE & SPECIFICATIONS
------------------------------------------------------------------------
- Core UI Framework: Streamlit Engine (Dynamic Data Container Polling)
- Graphics Engine: Matplotlib (Broadband Envelope Shader Grid)
- Hardware Telemetry Layer: Apple CoreWLAN (Objective-C System Bridge)
- Fallback Framework Layer: macOS System Configuration Framework (scutil)
- Spectrum Interference Math: Non-linear adjacent overlap integrated PSD matrix
  (Converts raw RSSI metrics to dynamic shared milliwatt spectral densities)

========================================================================
⚙️ SYSTEM REQUIREMENTS
========================================================================
1. Hardware: Physical Apple Mac computer (MacBook, Mac mini, Mac Studio, etc.)
2. Operating System: macOS (Requires local hardware execution)
3. Python Environment: Python 3.8 to Python 3.14 recommended
4. Core Dependencies: streamlit, matplotlib, numpy, pyobjc-framework-CoreWLAN

*CRITICAL NOTE: This application directly addresses physical macOS hardware 
peripherals via Objective-C runtime frameworks. It CANNOT be deployed or executed 
on Linux-based cloud infrastructure (such as Streamlit Community Cloud). 
It must be launched locally by the end-user on their machine.*

========================================================================
🚀 QUICK START INSTALLATION GUIDE
========================================================================

STEP 1: POSITION THE APPLICATION FILES
Ensure that your script and dependencies are grouped in the same project directory:
   - `app.py`          (The main Streamlit script)
   - `requirements.txt` (The dependency list)

STEP 2: PREPARE YOUR SEPARATE PY-ENVIRONMENT (RECOMMENDED)
Open your terminal application, navigate into your working folder, and establish an 
isolated environment to prevent library mismatches:
   $ cd "/path/to/your/Spectrum Analyzer Folder"
   $ python3 -m venv .venv
   $ source .venv/bin/activate

STEP 3: PROVISION SYSTEM LOGISTICS (INSTALL DEPENDENCIES)
Execute the package manager to download and link the analytical modules inside 
your active workspace environment:
   $ python3 -m pip install --upgrade pip
   $ python3 -m pip install -r requirements.txt

STEP 4: RUN THE ANALYSIS DASHBOARD
Boot the local engine using the implicit project runtime wrapper:
   $ python3 -m streamlit run app.py

The console layer will spin up an internal network thread socket and mirror 
the web execution layout directly inside your browser window at:
   👉 http://localhost:8501

========================================================================
⚠️ CRITICAL SECURITY CLEARANCE (LOCATION PERMISSIONS)
========================================================================
Apple considers surrounding Wi-Fi broadcast data (SSID name strings and BSSID 
physical MAC coordinates) as highly sensitive telemetry vectors tied directly 
to an individual's physical location. 

If your environment is not configured correctly, your Mac will automatically 
redact the spectrum string names, causing the table and graphs to output generic 
labels like "Hidden_Ch_Unknown" or "Hidden_ChX_xxxx".

TO EXPLICITLY PERMIT ACCESS ON MACOS:
1. Navigate to: Apple Menu () -> System Settings -> Privacy & Security.
2. In the right panel selection field, select: Location Services.
3. Verify that the primary 'Location Services' master switch slider is toggled ON.
4. Scan the app list registry below and locate 'Terminal' (or your active developer 
   environment executable such as 'Visual Studio Code' / 'PyCharm').
5. Toggle the permission switch next to your terminal window executable to ON.
6. IMPORTANT: Completely terminate and restart your Terminal or IDE app instance 
   to clear the cached security token before executing `python3 -m streamlit run app.py` 
   once again.

========================================================================
📊 UNDERSTANDING THE ANALYSIS SYSTEM METRICS
========================================================================
- Peak RSSI (Received Signal Strength Indicator): Peak localized signal carrier 
  amplitude power measured in decibel-milliwatts (dBm). Closer to 0 is stronger.
- Integrated Band PSD: The calculated integration of the overall broadcast footprint 
  power spread uniformly across the exact width of the assigned bandwidth (20/40/80 MHz).
- SINR (Co-Channel Adjust): True Signal-to-Interference-plus-Noise Ratio. Rather than 
  relying on a static theoretical noise variable floor, this custom algorithm parses 
  overlapping boundaries of all airwave traffic on your operating channel, converts 
  power states to linear milliwatts, aggregates neighbor interference metrics, and 
  calculates an accurate structural signal headroom quality calculation.
========================================================================
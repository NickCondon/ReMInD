# ReMInD
# 🧬 Recommended Metadata Interface for Documentation

**Version**: 2.27 (Full & Lite)  
**Author**: Dr Nicholas Condon (n.condon@uq.edu.au)  
**Affiliation**: Institute for Molecular Bioscience (IMB) Microscopy Facility, The University of Queensland  
**Date**: June 2025

---

## 📖 Overview

ReMInD assists researchers in capturing and organizing essential metadata for imaging experiments. It generates structured `ReadME.txt` files and JSON exports that can be stored alongside raw data to support good research data management (RDM) practices and future reuse.

The tool is especially useful for users of light microscopy and other imaging systems, helping to ensure that contextual information is not lost after acquisition. It features automatic metadata extraction from microscopy file formats to streamline the documentation process.

---

## 🚀 Features

### Core Functionality
- **GUI-based metadata form** with tooltips for each field  
- **Controlled vocabulary dropdowns** (e.g. microscope type, immersion media)  
- **Timestamp insertion** in Notes field
- **Template system** for pre-filling common fields
- **Load existing ReadME.txt** files to edit and update metadata
- **Export to multiple formats**: human-readable `ReadME.txt` and structured JSON

### Image Metadata Extraction
- **Automatic metadata extraction** from microscopy files:
  - **CZI files** (Zeiss) - acquisition settings, microscope info, channels
  - **LIF files** (Leica) - system details, imaging parameters
  - **ND2 files** (Nikon) - experimental setup, time series, Z-stacks
- **Smart field mapping** - automatically populates relevant form fields
- **Raw metadata display** - view complete extracted metadata
- **Round-trip compatibility** - reload metadata when opening saved ReadME files

### Adaptive Interface
- **Responsive design** - adapts to different screen resolutions (1024x768+)
- **Scrollable interface** for low-resolution displays
- **Scalable fonts** (A+/A- buttons)
- **Two-row button layout** for narrow screens

### UQ RDM Integration (Full Version)
- **UQ InstGateway connectivity** - automatic detection of available RDM projects
- **Visual indicators** for network connectivity status
- **Manual entry fallback** when not connected to institutional systems

---

## 🖥️ Requirements*

- **Python** 3.7+
- **Tkinter** (included with most Python installations)
- **Additional libraries** for metadata extraction:
  - `czifile` - for Zeiss CZI files [link](https://github.com/cgohlke/czifile)
  - `readlif` - for Leica LIF files [link](https://github.com/Arcadia-Science/readlif)
  - `nd2` - for Nikon ND2 files [link](https://github.com/tlambert03/nd2)

*Only needed for editing and testing the Python code

---

## 📁 Versions Available

### ReMInD Full (Remind_v2.27.py)
- Complete feature set including RDM connectivity
- UQ InstGateway integration for institutional users
- Recommended for University of Queensland researchers

### ReMInD Lite (Remind_Lite_V2.27.py)  
- Streamlined version without RDM connectivity
- All metadata extraction features included
- Suitable for general use and other institutions

---

## ⌨️ Creating the Executable

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```
2.  Place the python file into its own directory with no spaces
3.  In Command Prompt navigate to this directory with the script
4.  Run the following command replacing <scriptname> with your own (or e.g. Remind_v2.27.py)
   ```bash
   pyinstaller --onefile --windowed --name "executablename" --add-data "CZI_MetadataGUI.py;." --add-data "LIF_MetadataGUI.py;." --add-data "ND2_v2a.py;." <scriptname>.py
   ```
5.  Your single executable will be within the dist directory that was created.


## 📦 Packaged Executable
- The Remind.exe file can be downloaded and is fully self contained for Windows 11
- If using the custom icon file (provided) you will need to create a shortcut to the Remind.exe to use custom icons in Windows 11


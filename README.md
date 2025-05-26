# ReMInD
# 🧬 Recommended Metadata Interface for Documentation

**Version**: 2.0  
**Author**: Dr Nicholas Condon (n.condon@uq.edu.au)  
**Affiliation**: Institute for Molecular Bioscience (IMB) Microscopy Facility, The University of Queensland  
**Date**: May 2025

---

## 📖 Overview

This tool assists researchers in capturing and organizing essential metadata for imaging experiments. It generates a structured `ReadME.txt` file that can be stored alongside raw data to support good research data management (RDM) practices and future reuse.

The tool is especially useful for users of light microscopy and other imaging systems, helping to ensure that contextual information is not lost after acquisition.

---

## 🚀 Features

- GUI-based metadata form with tooltips for each field  
- Dropdowns for controlled vocabulary (e.g. microscope type, immersion media)  
- Timestamp insertion in Notes  
- Load existing `ReadME.txt` or template file to prefill the form  
- Export metadata to a human-readable `ReadME.txt` file  

---

## 🖥️ Requirements*

- **Python** 3.7+
- **Tkinter** (included with most Python installations)
* Only needed for editing and testing the python code

## ⌨️ Creating the executable

1.  Install PyInstaller 
   ```
pip install pyinstaller
```
3.  Place the python file into its own directory with no spaces
4.  In Command Prompt navigate to this directory with the script
5.  Run the following command replacing <scriptname> with your own.
```
pyinstaller --onefile --windowed <scriptname>.py
```
6.  Your single executable will be within the dist directory that was created.


## 📦 Packaged Executable
- The Remind.exe file can be downloaded and is fully self contained for Windows 11
- If using the custom icon file (provided) you will need to create a shortcut to the Remind.exe to use custom icons in Windows 11


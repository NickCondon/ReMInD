"""
Extract and summarize Zeiss CZI metadata using pylibCZIrw.
Outputs key image, instrument, and channel metadata in a structured, human-readable format.
Requires pylibCZIrw to read the metadata and tkinter for GUI file selection.

Version: 0.1.0
Author: Dr James Springfield (j.springfield@imb.uq.edu.au)
Affiliation: Institute for Molecular Bioscience (IMB) Microscopy Facility, The University of Queensland
Date: May 2025
"""

import os
import json
import tkinter as tk
from tkinter import filedialog
from pylibCZIrw import czi as pyczi
import sys
import subprocess

# --- Helper functions ---
def install_pylibczirw():
    """Install pylibCZIrw if not already installed."""
    try:
        import pylibCZIrw
    except ImportError:
        print("pylibCZIrw not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pylibCZIrw"])
        print("pylibCZIrw installed successfully.")

def convert_time_interval(value, unit="ms"):
    """
    Convert a time interval value and unit to seconds.
    Returns the interval in seconds (rounded to 6 decimals) or "N/A" if invalid.
    """
    try:
        if value is not None and value != "" and value != "N/A":
            value = float(value)
            if unit == "ms":
                result = value / 1000.0
            elif unit == "s":
                result = value
            elif unit == "min":
                result = value * 60.0
            elif unit == "h":
                result = value * 3600.0
            else:
                result = value
            return round(result, 6)
    except Exception:
        pass
    return "N/A"

def safe_get(d, *keys, default="N/A"):
    """Safely get nested dictionary keys."""
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d

def ensure_list(val):
    """Ensure the value is a list."""
    if isinstance(val, list):
        return val
    elif isinstance(val, dict):
        return [val]
    else:
        return []

def safe_round(val):
    """Round a value to 3 decimals if possible, else return as is."""
    try:
        return round(float(val), 3)
    except Exception:
        return val

def to_microns_or_na(val):
    """Convert a value in meters to microns, rounded to 3 decimals, or 'N/A' if invalid/zero."""
    try:
        if val is not None and val != "N/A" and float(val) != 0:
            return round(float(val) * 1e6, 3)
    except Exception:
        pass
    return "N/A"

def safe_image_size(size, pixel_size):
    """Calculate image size in microns."""
    try:
        return round(float(size) * float(pixel_size), 3)
    except Exception:
        return "N/A"

def select_czi_file():
    """Open a file dialog to select a CZI file and return its path. Plays a sound when opened."""
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.focus_force()
    root.withdraw()
    # Play a system beep when the file dialog opens
    if sys.platform == "darwin":
        try:
            subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], check=False)
        except Exception:
            pass
    else:
        try:
            root.bell()
        except Exception:
            pass
    file_path = filedialog.askopenfilename(
        title="Select CZI file",
        filetypes=[("CZI files", "*.czi"), ("All files", "*.*")]
    )
    root.destroy()
    return file_path

def extract_metadata(demo_czi_read):
    """Extract and return filtered and full metadata from a CZI file."""
    with pyczi.open_czi(demo_czi_read) as czi_doc:
        metadata_dict = czi_doc.metadata

        # --- Metadata navigation ---
        meta = safe_get(metadata_dict, "ImageDocument", "Metadata", default={})
        info_meta = safe_get(meta, "Information", default={})
        config_meta = safe_get(meta, "HardwareSetting", "Configuration", default={})
        image_meta = safe_get(info_meta, "Image", default={})
        instrument_meta = safe_get(info_meta, "Instrument", default={})
        microscope_meta = safe_get(instrument_meta, "Microscopes", default={})
        objectives_meta = safe_get(instrument_meta, "Objectives", default={})
        application_meta = safe_get(info_meta, "Application", default={})
        experiment_meta = safe_get(meta, "Experiment", default={})
        acquisition_blocks = ensure_list(safe_get(experiment_meta, "ExperimentBlocks", "AcquisitionBlock", default=[]))
        acquisition_meta = acquisition_blocks[0] if acquisition_blocks else {}
        track_meta = safe_get(acquisition_meta, "MultiTrackSetup", default={})

        # --- Document info ---
        document_name = safe_get(info_meta, "Document", "Name", default=os.path.splitext(os.path.basename(demo_czi_read))[0])
        document_user_name = safe_get(info_meta, "Document", "UserName")
        document_creation_date = safe_get(info_meta, "Document", "CreationDate")

        # --- Application info ---
        application_name = safe_get(application_meta, "Name")
        application_version = safe_get(application_meta, "Version")

        # --- System info ---
        microscope = safe_get(microscope_meta, "Microscope", default={})
        system_name = microscope.get("System", "")
        if not system_name:
            device = config_meta.get("Device", {})
            if isinstance(device, list):
                system_name = next((d.get("@Name", "") for d in device if d.get("@Id") == "Microscope" and "@Name" in d), "")
                if not system_name:
                    system_name = next((d.get("@Name", "") for d in device if "@Name" in d), "")
            elif isinstance(device, dict):
                system_name = device.get("@Name", "")

        # --- Image info ---
        pixel_type = image_meta.get("PixelType", "N/A")
        size_x = image_meta.get("SizeX", "N/A")
        size_y = image_meta.get("SizeY", "N/A")
        size_z = image_meta.get("SizeZ", "N/A")
        size_t = image_meta.get("SizeT", "N/A")
        size_s = image_meta.get("SizeS", "N/A")
        size_m = image_meta.get("SizeM", "N/A")

        # --- Channel info ---
        dim_info = safe_get(metadata_dict, "ImageDocument", "Metadata", "Information", "Image", "Dimensions", default={})
        tracks = ensure_list(dim_info.get("Tracks", {}).get("Track", []))
        channel_ids = {cref["@Id"] for track in tracks for cref in ensure_list(track.get("ChannelRefs", {}).get("ChannelRef", [])) if "@Id" in cref}
        size_c = len(channel_ids)

        # --- Pixel sizes (microns) ---
        acq_mode_setup = safe_get(acquisition_meta, "AcquisitionModeSetup", default={})
        pixel_Size_X = to_microns_or_na(acq_mode_setup.get("ScalingX", "N/A"))
        pixel_Size_Y = to_microns_or_na(acq_mode_setup.get("ScalingY", "N/A"))
        pixel_Size_Z = to_microns_or_na(acq_mode_setup.get("ScalingZ", "N/A"))
        # Fallback: if any pixel size is "N/A", try to get from scaling items' distances (already in microns)
        scaling_items = safe_get(metadata_dict, "ImageDocument", "Metadata", "Scaling", "Items", default={})
        distances = ensure_list(scaling_items.get("Distance", []))
        distance_map = {d.get("@Id"): d.get("Value") for d in distances if "@Id" in d and "Value" in d}
        if pixel_Size_X == "N/A":
            pixel_Size_X = to_microns_or_na(distance_map.get("X", "N/A"))
        if pixel_Size_Y == "N/A":
            pixel_Size_Y = to_microns_or_na(distance_map.get("Y", "N/A"))
        if pixel_Size_Z == "N/A":
            pixel_Size_Z = to_microns_or_na(distance_map.get("Z", "N/A"))

        # --- Image sizes (microns) ---
        image_size_x = safe_image_size(size_x, pixel_Size_X)
        image_size_y = safe_image_size(size_y, pixel_Size_Y)
        image_size_z = safe_image_size(size_z, pixel_Size_Z)

        # --- Objective info ---
        objective = objectives_meta.get("Objective", {})
        objective_model = safe_get(objective, "Manufacturer", "Model")
        objective_NA = safe_round(objective.get("LensNA", "N/A"))
        objective_mag = safe_round(objective.get("NominalMagnification", "N/A"))
        objective_RI = safe_round(image_meta.get("ObjectiveSettings", {}).get("RefractiveIndex", "N/A"))
        objective_Medium = image_meta.get("ObjectiveSettings", {}).get("Medium", "N/A")

        # --- Channel details ---
        channels_info = ensure_list(
            safe_get(metadata_dict, "ImageDocument", "Metadata", "Information", "Image", "Dimensions", "Channels", "Channel", default=[])
        )
        channel_names = [ch.get("@Name", "N/A") for ch in channels_info]
        illumination_Types = [ch.get("IlluminationType", "N/A") for ch in channels_info]
        contrast_Methods = [ch.get("ContrastMethod", "N/A") for ch in channels_info]
        pinhole_Sizes = [safe_round(ch.get("PinholeSizeAiry", "N/A")) for ch in channels_info]
        excitation_wavelengths = [safe_round(ch.get("ExcitationWavelength", "N/A")) for ch in channels_info]
        emission_wavelengths = [safe_round(ch.get("EmissionWavelength", "N/A")) for ch in channels_info]
        acquisition_modes = [ch.get("AcquisitionMode", "N/A") for ch in channels_info]
        dye_names = [ch.get("Fluor", "N/A") for ch in channels_info]
        zoom_list = [safe_round(safe_get(ch, "LaserScanInfo", "ZoomX")) for ch in channels_info]
        total_magnifications = [safe_round(safe_get(ch, "CustomAttributes", "MM.TotalMagnification")) for ch in channels_info]

        # --- Per-detector wavelength ranges ---
        all_detector_wavelength_ranges = []
        for track in ensure_list(track_meta.get("TrackSetup", [])):
            for detector in ensure_list(track.get("Detectors", {}).get("Detector", [])):
                wl_range = detector.get("DetectorWavelengthRanges", {}).get("DetectorWavelengthRange", {})
                if isinstance(wl_range, dict):
                    wl_start = wl_range.get("WavelengthStart", "N/A")
                    wl_end = wl_range.get("WavelengthEnd", "N/A")
                    try:
                        wl_start_nm = round(float(wl_start) * 1e9, 3)
                        wl_end_nm = round(float(wl_end) * 1e9, 3)
                        detector_wavelength_range = f"{wl_start_nm} - {wl_end_nm}"
                    except Exception:
                        detector_wavelength_range = f"{wl_start} - {wl_end}"
                else:
                    detector_wavelength_range = "N/A"
                all_detector_wavelength_ranges.append(detector_wavelength_range)

        # --- Update Emission Wavelength Range for any channel containing 'ChA', ie: Airyscan detector ---
        for i, channel_name in enumerate(channel_names):
            if "ChA" in channel_name:
                filterset_value = None
                for track in ensure_list(track_meta.get("TrackSetup", [])):
                    for detector in ensure_list(track.get("Detectors", {}).get("Detector", [])):
                        if "ChA" in detector.get("ImageChannelName", ""):
                            filtersets = detector.get("Filtersets", {})
                            filterset_value = filtersets.get("Filterset", None)
                            break
                    if filterset_value:
                        break
                if filterset_value:
                    all_detector_wavelength_ranges[i] = filterset_value

        # --- Time Interval (s) ---
        # Try to get value and unit from the primary location
        ts = safe_get(acquisition_meta, "SubDimensionSetups", "TimeSeriesSetup", "Interval", "TimeSpan", default={})
        value = ts.get("Value", None)
        unit = ts.get("DefaultUnitFormat", "ms")
        time_interval = convert_time_interval(value, unit)
        # Fallback: Try secondary location if still N/A
        if time_interval == "N/A":
            ts = safe_get(
                metadata_dict,
                "ImageDocument", "Metadata", "Experiment", "ExperimentBlocks", "AcquisitionBlock",
                "TimeSeriesSetup", "Switches", "Switch", "SwitchAction", "SetIntervalAction", "Interval", "TimeSpan",
                default={}
            )
            value = ts.get("Value", None)
            unit = ts.get("DefaultUnitFormat", "ms")
            time_interval = convert_time_interval(value, unit)

        # --- Per-channel Pinhole Diameter (um) ---
        all_pinhole_diameters = []
        for channel_name in channel_names:
            pinhole_diameter_um = "N/A"
            for track in ensure_list(track_meta.get("TrackSetup", [])):
                for detector in ensure_list(track.get("Detectors", {}).get("Detector", [])):
                    det_channel = detector.get("ImageChannelName", "")
                    if det_channel == channel_name or det_channel in channel_name or channel_name in det_channel:
                        pinhole_diameter = detector.get("PinholeDiameter", None)
                        if pinhole_diameter is None or pinhole_diameter == "" or pinhole_diameter == "N/A":
                            pinhole_diameter_um = "N/A"
                        else:
                            try:
                                pinhole_diameter_um = round(float(pinhole_diameter) * 1e6, 3)
                            except Exception:
                                pinhole_diameter_um = "N/A"
                        break
                if pinhole_diameter_um != "N/A":
                    break
            all_pinhole_diameters.append(pinhole_diameter_um)

        # --- Per-channel Airyscan Virtual Pinhole Size (um) ---
        airy_scan_virtual_pinhole_sizes = []
        for channel_name in channel_names:
            value = "N/A"
            for track in ensure_list(track_meta.get("TrackSetup", [])):
                for detector in ensure_list(track.get("Detectors", {}).get("Detector", [])):
                    if detector.get("@Name") == "Airyscan":
                        det_channel = detector.get("ImageChannelName", "")
                        if det_channel == channel_name or det_channel in channel_name or channel_name in det_channel:
                            airy_val = detector.get("AiryScanVirtualPinholeSize", None)
                            if airy_val is not None:
                                try:
                                    value = round(float(airy_val) * 1e6, 3)
                                except Exception:
                                    value = airy_val
                            break
                if value != "N/A":
                    break
            airy_scan_virtual_pinhole_sizes.append(value)

        # --- Assemble metadata output ---
        metadata_output = {
            "Document Name": document_name,
            "Document User Name": document_user_name,
            "Document Creation Date": document_creation_date,
            "Application Name": application_name,
            "Application Version": application_version,
            "System Name": system_name,
            "Pixel Type": pixel_type,
            "Size X": size_x,
            "Size Y": size_y,
            "Size Z": size_z,
            "Size M": size_m,
            "Size T": size_t,
            "Size C": size_c,
            "Size S": size_s,
            "Pixel Size X (um)": pixel_Size_X,
            "Pixel Size Y (um)": pixel_Size_Y,
            "Pixel Size Z (um)": pixel_Size_Z,
            "Image Size X (um)": image_size_x,
            "Image Size Y (um)": image_size_y,
            "Image Size Z (um)": image_size_z,
            "Time Interval (s)": time_interval,
            "Objective Model": objective_model,
            "Objective NA": objective_NA,
            "Objective Magnification": objective_mag,
            "Objective Refractive Index": objective_RI,
            "Objective Medium": objective_Medium,
            "Illumination_Types": illumination_Types,
            "Contrast Methods": contrast_Methods,
            "Acquisition Modes": acquisition_modes,
            "Channel Names": channel_names,
            "Dye Names": dye_names,
            "Excitation Wavelengths": excitation_wavelengths,
            "Emission Wavelengths": emission_wavelengths,
            "Emission Wavelength Range (nm)": all_detector_wavelength_ranges,
            "Pinhole Sizes (Airy Units)": pinhole_Sizes,
            "Pinhole Diameters (um)": all_pinhole_diameters,
            "AiryScan Virtual Pinhole Size (um)": airy_scan_virtual_pinhole_sizes,
            "Zoom": zoom_list,
            "TotalMagnification": total_magnifications,
        }

        return metadata_output, metadata_dict


def main():
    """Main function to run the CZI metadata reader GUI."""
    # Install pylibCZIrw if not already installed
    if "pylibCZIrw" not in sys.modules: 
        install_pylibczirw()

    # Select file
    demo_czi_read = select_czi_file()
    if not demo_czi_read:
        print("No file selected. Exiting.")
        return

    # Extract metadata
    metadata_output, metadata_dict = extract_metadata(demo_czi_read)

    # Print filtered metadata
    print("Zeiss CZI Metadata Dictionary:")
    for key, value in metadata_output.items():
        print(f"{key}: {value}")

    # Export filtered metadata to JSON
    base_name = os.path.splitext(os.path.basename(demo_czi_read))[0]
    json_path = os.path.join(os.path.dirname(demo_czi_read), f"{base_name}_filtered.json")
    with open(json_path, "w") as f:
        json.dump(metadata_output, f, indent=2)
    print(f"\nFiltered Metadata exported to: {json_path}")

    # Export full metadata_dict to JSON
    metadata_json_path = os.path.join(os.path.dirname(demo_czi_read), f"{base_name}_metadata.json")
    with open(metadata_json_path, "w") as f:
        json.dump(metadata_dict, f, indent=2)
    print(f"Full metadata exported to: {metadata_json_path}")

    # Display filtered metadata in a scrollable window
    display_root = tk.Tk()
    display_root.title("CZI Filtered Metadata")
    text = tk.Text(display_root, wrap="none", width=100, height=40)
    text.pack(side="left", fill="both", expand=True)

    # Add scrollbars
    yscroll = tk.Scrollbar(display_root, command=text.yview)
    yscroll.pack(side="right", fill="y")
    text.configure(yscrollcommand=yscroll.set)

    xscroll = tk.Scrollbar(display_root, command=text.xview, orient="horizontal")
    xscroll.pack(side="bottom", fill="x")
    text.configure(xscrollcommand=xscroll.set)

    # Insert metadata text
    metadata_text = json.dumps(metadata_output, indent=2)
    text.insert("1.0", metadata_text)

    # Make the window modal
    display_root.grab_set()
    tk.mainloop()

if __name__ == "__main__":
    main()

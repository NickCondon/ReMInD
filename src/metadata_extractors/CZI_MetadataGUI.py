"""
Extract and summarize Zeiss CZI metadata using pylibCZIrw.
Outputs key image, instrument, and channel metadata in a structured, human-readable format.
All numeric values are converted to standard units and rounded to 3 decimal places where appropriate.
"""

import os
import xml.etree.ElementTree as ET
from pylibCZIrw import czi as pyczi

def safe_round(val):
    """Round a value to 3 decimals if possible, else return as is."""
    try:
        fval = float(val)
        return round(fval, 3)
    except Exception:
        return val

def round_list(lst):
    """Round all numeric values in a list to 3 decimals, leave others unchanged."""
    return [
        round(float(x), 3) if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).replace('-', '', 1).isdigit())
        else x
        for x in lst
    ]

def to_microns(val):
    """Convert a value in meters to microns, rounded to 3 decimals."""
    try:
        return round(float(val) * 1e6, 3)
    except Exception:
        return val

def to_int(val):
    """Convert a value to int if possible, else return as is."""
    try:
        return int(float(val))
    except Exception:
        return val

def extract_metadata(demo_czi_read):
    """Extract and return filtered and full metadata from a CZI file."""
    with pyczi.open_czi(demo_czi_read) as czi_doc:
        root = ET.fromstring(czi_doc.raw_metadata)
        metadata_dict = czi_doc.metadata

        # --- Helper functions ---
        def safe_get(d, *keys, default="N/A"):
            for k in keys:
                if isinstance(d, dict) and k in d:
                    d = d[k]
                else:
                    return default
            return d

        def ensure_list(val):
            if isinstance(val, list):
                return val
            elif isinstance(val, dict):
                return [val]
            else:
                return []

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
        acquisition_blocks = ensure_list(
            safe_get(experiment_meta, "ExperimentBlocks", "AcquisitionBlock", default=[])
        )
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

        device = config_meta.get("Device", {})
        widefield_name = ""
        if isinstance(device, list):
            widefield_name = next((d.get("@Name", "") for d in device if d.get("@Id") == "Microscope" and "@Name" in d), "")
            if not widefield_name:
                widefield_name = next((d.get("@Name", "") for d in device if "@Name" in d), "")
        elif isinstance(device, dict):
            widefield_name = device.get("@Name", "")
        if not system_name:
            system_name = widefield_name

        # --- Image info ---
        pixel_type = image_meta.get("PixelType", "N/A")
        size_x = to_int(image_meta.get("SizeX", "N/A"))
        size_y = to_int(image_meta.get("SizeY", "N/A"))
        size_z = to_int(image_meta.get("SizeZ", "N/A"))
        size_t = to_int(image_meta.get("SizeT", "N/A"))
        size_s = to_int(image_meta.get("SizeS", "N/A"))
        size_m = to_int(image_meta.get("SizeM", "N/A"))

        # --- Channel info ---
        dim_info = safe_get(metadata_dict, "ImageDocument", "Metadata", "Information", "Image", "Dimensions", default={})
        tracks = ensure_list(dim_info.get("Tracks", {}).get("Track", []))
        channel_ids = set()
        for track in tracks:
            channel_refs = ensure_list(track.get("ChannelRefs", {}).get("ChannelRef", []))
            for cref in channel_refs:
                if "@Id" in cref:
                    channel_ids.add(cref["@Id"])
        size_c = to_int(len(channel_ids))

        # --- Pixel sizes (microns) ---
        acq_mode_setup = safe_get(acquisition_meta, "AcquisitionModeSetup", default={})
        pixel_Size_X = to_microns(acq_mode_setup.get("ScalingX", "N/A"))
        pixel_Size_Y = to_microns(acq_mode_setup.get("ScalingY", "N/A"))
        pixel_Size_Z = to_microns(acq_mode_setup.get("ScalingZ", "N/A"))

        # Fallback for pixel sizes
        scaling_items = safe_get(metadata_dict, "ImageDocument", "Metadata", "Scaling", "Items", default={})
        distances = ensure_list(scaling_items.get("Distance", []))
        distance_map = {d.get("@Id"): d.get("Value") for d in distances if "@Id" in d and "Value" in d}

        def fallback_pixel_size(val, axis):
            if not val or val == "N/A" or val == 0:
                v = distance_map.get(axis)
                try:
                    return round(float(v) * 1e6, 3)
                except Exception:
                    return val
            return val

        pixel_Size_X = fallback_pixel_size(pixel_Size_X, "X")
        pixel_Size_Y = fallback_pixel_size(pixel_Size_Y, "Y")
        pixel_Size_Z = fallback_pixel_size(pixel_Size_Z, "Z")

        # --- Image size in microns ---
        def safe_image_size(size, pixel_size):
            try:
                return round(float(size) * float(pixel_size), 3)
            except Exception:
                return "N/A"

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

        # Per-channel MM.TotalMagnification
        total_magnifications = []
        for ch in channels_info:
            mm_total_mag = safe_get(ch, "CustomAttributes", "MM.TotalMagnification")
            try:
                mm_total_mag = round(float(mm_total_mag), 3)
            except Exception:
                pass
            total_magnifications.append(mm_total_mag)

        channel_names = [ch.get("@Name", "N/A") for ch in channels_info]
        illumination_Types = [ch.get("IlluminationType", "N/A") for ch in channels_info]
        contrast_Methods = [ch.get("ContrastMethod", "N/A") for ch in channels_info]
        pinhole_Sizes = [safe_round(ch.get("PinholeSizeAiry", "N/A")) for ch in channels_info]
        excitation_wavelengths = [safe_round(ch.get("ExcitationWavelength", "N/A")) for ch in channels_info]
        emission_wavelengths = [safe_round(ch.get("EmissionWavelength", "N/A")) for ch in channels_info]
        acquisition_modes = [ch.get("AcquisitionMode", "N/A") for ch in channels_info]
        dye_names = [ch.get("Fluor", "N/A") for ch in channels_info]
        zoom_list = []
        for ch in channels_info:
            zoom_x = safe_get(ch, "LaserScanInfo", "ZoomX")
            try:
                zoom_x = round(float(zoom_x), 3)
            except Exception:
                pass
            zoom_list.append(zoom_x)

        # --- Per-detector wavelength ranges ---
        tracks = ensure_list(track_meta.get("TrackSetup", []))
        all_detector_wavelength_ranges = []
        for track in tracks:
            detectors = ensure_list(track.get("Detectors", {}).get("Detector", []))
            for detector in detectors:
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

        # --- Per-channel Airyscan Virtual Pinhole Size ---
        airy_scan_virtual_pinhole_sizes = []
        for channel_name in channel_names:
            value = "N/A"
            for track in tracks:
                detectors = ensure_list(track.get("Detectors", {}).get("Detector", []))
                for detector in detectors:
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

        # --- Per-channel Pinhole Diameter (um) ---
        all_pinhole_diameters = []
        for channel_name in channel_names:
            pinhole_diameter_um = "N/A"
            for track in tracks:
                detectors = ensure_list(track.get("Detectors", {}).get("Detector", []))
                for detector in detectors:
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

        # --- Time Interval (s) ---
        time_interval = "N/A"
        try:
            time_interval = (
                safe_get(acquisition_meta, "SubDimensionSetups", "TimeSeriesSetup", "Interval", "TimeSpan", "Value")
            )
            if time_interval != "N/A":
                time_interval = float(time_interval)
        except Exception:
            pass

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
            "MM.TotalMagnification (per channel)": total_magnifications,
        }

        # --- Update Emission Wavelength Range for any channel containing 'ChA' ---
        for i, channel_name in enumerate(metadata_output["Channel Names"]):
            if "ChA" in channel_name:
                filterset_value = None
                for track in tracks:
                    detectors = ensure_list(track.get("Detectors", {}).get("Detector", []))
                    for detector in detectors:
                        if "ChA" in detector.get("ImageChannelName", ""):
                            filtersets = detector.get("Filtersets", {})
                            filterset_value = filtersets.get("Filterset", None)
                            break
                    if filterset_value:
                        break
                if filterset_value:
                    metadata_output["Emission Wavelength Range (nm)"][i] = filterset_value

        return metadata_output, metadata_dict

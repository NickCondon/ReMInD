from readlif.reader import LifFile
import re
import xml.etree.ElementTree as ET

def extract_lif_metadata(lif_path):
    """Extracts metadata from a Leica LIF file and returns a summary dictionary."""
    lif_file = LifFile(lif_path)
    metadata_list = []
    xml_header = lif_file.xml_header

    for idx, image in enumerate(lif_file.get_iter_image()):
        info = image.info
        meta = extract_leica_metadata(info, xml_header)
        meta["Image Index"] = idx + 1
        meta["Image Name"] = info.get('name', 'Unnamed')
        meta["Dimensions"] = str(info.get("dims", "N/A"))
        meta["Number of channels"] = info.get("channels", "N/A")
        meta["Voxel size (scale)"] = str(info.get("scale", "N/A"))
        settings = info.get("settings", {})
        meta["Objective"] = settings.get("ObjectiveName", "N/A")
        meta["Magnification"] = settings.get("Magnification", "N/A")
        meta["Numerical Aperture"] = settings.get("NumericalAperture", "N/A")
        meta["Immersion"] = settings.get("Immersion", "N/A")
        metadata_list.append(meta)

    # Optionally, add global header info
    header = xml_header
    matches = re.findall(r'(AcquisitionDate|CreationDate)[^>]*>([^<]+)', header)
    if matches:
        for tag, date in matches:
            metadata_list[0][f"Header_{tag}"] = date

    # Timestamps
    root_xml = ET.fromstring(xml_header)
    timestamps = []
    for elem in root_xml.iter():
        if 'timestamp' in elem.attrib:
            timestamps.append(elem.attrib['timestamp'])
        if elem.tag.lower().endswith('timestamp') and elem.text:
            timestamps.append(elem.text)
    if timestamps:
        metadata_list[0]["Timestamps"] = timestamps

    # DataSourceTypeName and System Type Name
    ds_type = re.findall(r'DataSourceTypeName="([^"]+)"', header)
    sys_type = re.findall(r'System Type Name="([^"]+)"', header)
    if ds_type:
        metadata_list[0]["DataSourceTypeName"] = ds_type[0]
    if sys_type:
        metadata_list[0]["System Type Name"] = sys_type[0]

    return metadata_list

def extract_leica_metadata(info, xml_header):
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_header)
    settings = info.get("settings", {})
    dims = info.get("dims", None)
    scale = info.get("scale", (None, None, None))
    channels = info.get("channels", "N/A")

    def find_tag(name):
        for elem in root.iter():
            if elem.tag.lower().endswith(name.lower()):
                return elem.text
        return "N/A"

    def find_attr(attr):
        for elem in root.iter():
            if attr in elem.attrib:
                return elem.attrib[attr]
        return "N/A"

    app_name = app_version = "N/A"
    for att in root.findall(".//Attachment"):
        if "Software" in att.attrib:
            app_version = att.attrib["Software"]
        if "Application" in att.attrib:
            app_name = att.attrib["Application"]

    # Unique channel names
    channel_names = []
    seen_channels = set()
    for ch in root.findall(".//ChannelDescription"):
        name = ch.attrib.get("LUTName") or ch.attrib.get("ChannelName") or ch.attrib.get("NameOfMeasuredQuantity") or "N/A"
        if name not in seen_channels:
            channel_names.append(name)
            seen_channels.add(name)

    dye_names = []
    excitation_wavelengths = []
    emission_wavelengths = []
    emission_wavelength_ranges = []
    pinhole_sizes = []
    pinhole_diameters = []
    airy_virtual_pinhole = []
    zooms = []

    for ch in root.findall(".//ChannelDescription"):
        name = ch.attrib.get("LUTName") or ch.attrib.get("ChannelName") or ch.attrib.get("NameOfMeasuredQuantity") or "N/A"
        channel_names.append(name)
        if "PinholeAiry" in ch.attrib:
            pinhole_sizes.append(ch.attrib["PinholeAiry"])
        if "Pinhole" in ch.attrib:
            pinhole_diameters.append(ch.attrib["Pinhole"])

    for mb in root.findall(".//MultiBand"):
        dye_names.append(mb.attrib.get("DyeName", "N/A"))
        excitation_wavelengths.append(mb.attrib.get("TargetWaveLengthBegin", "N/A"))
        emission_wavelengths.append(mb.attrib.get("TargetWaveLengthEnd", "N/A"))
        emission_wavelength_ranges.append(f"{mb.attrib.get('LeftWorld', 'N/A')}-{mb.attrib.get('RightWorld', 'N/A')}")

    for atl in root.findall(".//ATLConfocalSettingDefinition"):
        if "PinholeAiry" in atl.attrib:
            pinhole_sizes.append(atl.attrib["PinholeAiry"])
        if "Pinhole" in atl.attrib:
            pinhole_diameters.append(atl.attrib["Pinhole"])
        if "Zoom" in atl.attrib:
            zooms.append(atl.attrib["Zoom"])
        if "AiryScanVirtualPinholeSize" in atl.attrib:
            airy_virtual_pinhole.append(atl.attrib["AiryScanVirtualPinholeSize"])

    active_ex_waves = []
    active_em_waves = []
    for lls in root.findall(".//LaserLineSetting"):
        if lls.attrib.get("IsLineChecked", "0") == "1":
            if "LaserLine" in lls.attrib:
                active_ex_waves.append(lls.attrib["LaserLine"])
    for det in root.findall(".//Detector"):
        if det.attrib.get("IsActive", "0") == "1":
            if "ChannelName" in det.attrib:
                active_em_waves.append(det.attrib.get("ChannelName"))

    meta = {
        "Document Name": info.get("name", find_tag("Name")),
        "Document User Name": find_attr("UserName"),
        "Document Creation Date": find_attr("CreationDate") or find_tag("CreationDate"),
        "Application Name": app_name,
        "Application Version": app_version,
        "System Name": find_attr("SystemTypeName"),
        "Pixel Type": find_attr("PixelType"),
        "Size X": dims.x if dims else "N/A",
        "Size Y": dims.y if dims else "N/A",
        "Size Z": dims.z if dims else "N/A",
        "Size M": dims.m if dims and hasattr(dims, "m") else "N/A",
        "Size T": dims.t if dims and hasattr(dims, "t") else "N/A",
        "Size C": channels,
        "Size S": "N/A",
        "Pixel Size X (um)": scale[0] if scale and len(scale) > 0 else "N/A",
        "Pixel Size Y (um)": scale[1] if scale and len(scale) > 1 else "N/A",
        "Pixel Size Z (um)": scale[2] if scale and len(scale) > 2 else "N/A",
        "Image Size X (um)": float(scale[0])*dims.x if scale and dims and scale[0] else "N/A",
        "Image Size Y (um)": float(scale[1])*dims.y if scale and dims and scale[1] else "N/A",
        "Image Size Z (um)": float(scale[2])*dims.z if scale and dims and scale[2] else "N/A",
        "Time Interval (s)": find_attr("TimeInterval"),
        "Objective Model": settings.get("ObjectiveName", find_attr("ObjectiveName")),
        "Objective NA": settings.get("NumericalAperture", find_attr("NumericalAperture")),
        "Objective Magnification": settings.get("Magnification", find_attr("Magnification")),
        "Objective Refractive Index": settings.get("RefractionIndex", find_attr("RefractionIndex")),
        "Objective Medium": settings.get("Immersion", find_attr("Immersion")),
        "Illumination_Types": find_attr("IlluminationType"),
        "Contrast Methods": find_attr("ContrastMethod"),
        "Acquisition Modes": find_attr("AcquisitionMode"),
        "Channel Names": ", ".join(channel_names) if channel_names else "N/A",
        "Dye Names": ", ".join(dye_names) if dye_names else "N/A",
        "Excitation Wavelengths (active)": ", ".join(active_ex_waves) if active_ex_waves else "N/A",
        "Emission Channels (active)": ", ".join(active_em_waves) if active_em_waves else "N/A",
        "Excitation Wavelengths (all)": ", ".join(excitation_wavelengths) if excitation_wavelengths else "N/A",
        "Emission Wavelengths (all)": ", ".join(emission_wavelengths) if emission_wavelengths else "N/A",
        "Emission Wavelength Range (nm)": ", ".join(emission_wavelength_ranges) if emission_wavelength_ranges else "N/A",
        "Pinhole Sizes (Airy Units)": ", ".join(pinhole_sizes) if pinhole_sizes else "N/A",
        "Pinhole Diameters (um)": ", ".join(pinhole_diameters) if pinhole_diameters else "N/A",
        "AiryScan Virtual Pinhole Size (um)": ", ".join(airy_virtual_pinhole) if airy_virtual_pinhole else "N/A",
        "Zoom": ", ".join(zooms) if zooms else "N/A",
        "MM.TotalMagnification (per channel)": find_attr("TotalMagnification"),
    }
    return meta

# Optional: CLI usage for testing
if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print("Usage: python LIF_MetadataGUI.py <file.lif>")
    else:
        lif_path = sys.argv[1]
        metadata = extract_lif_metadata(lif_path)
        print(json.dumps(metadata, indent=2))
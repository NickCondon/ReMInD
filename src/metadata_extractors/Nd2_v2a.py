import os
from nd2 import ND2File
from datetime import datetime

def extract_nd2_metadata(file_path):
    """
    Extract metadata from ND2 file and return a dictionary suitable for ReMInD.
    
    Args:
        file_path (str): Path to the ND2 file
        
    Returns:
        dict: Metadata dictionary with keys compatible with ReMInD fields
    """
    try:
        with ND2File(file_path) as nd2:
            metadata = {}
            
            # Basic file information
            metadata["File Path"] = file_path
            metadata["File Name"] = os.path.basename(file_path)
            
            # File size
            try:
                if hasattr(nd2, 'path') and nd2.path:
                    file_size = nd2.path.stat().st_size / (1024*1024)
                    metadata["File Size MB"] = f"{file_size:.2f}"
            except:
                metadata["File Size MB"] = "N/A"
            
            # Image dimensions
            try:
                metadata["Shape"] = str(nd2.shape) if hasattr(nd2, 'shape') else "N/A"
                metadata["Data Type"] = str(nd2.dtype) if hasattr(nd2, 'dtype') else "N/A"
            except:
                metadata["Shape"] = "N/A"
                metadata["Data Type"] = "N/A"
            
            # Dimension sizes
            try:
                if hasattr(nd2, 'sizes') and nd2.sizes:
                    sizes = nd2.sizes
                    metadata["Time Points"] = str(sizes.get('T', 1))
                    metadata["Channels"] = str(sizes.get('C', 1))
                    metadata["Z Slices"] = str(sizes.get('Z', 1))
                    metadata["Height"] = str(sizes.get('Y', 'N/A'))
                    metadata["Width"] = str(sizes.get('X', 'N/A'))
                else:
                    metadata.update({
                        "Time Points": "1",
                        "Channels": "1", 
                        "Z Slices": "1",
                        "Height": "N/A",
                        "Width": "N/A",
                    })
            except:
                metadata.update({
                    "Time Points": "N/A",
                    "Channels": "N/A", 
                    "Z Slices": "N/A",
                    "Height": "N/A",
                    "Width": "N/A",
                })
            
            # Experiment information
            try:
                if hasattr(nd2, 'experiment') and nd2.experiment:
                    exp = nd2.experiment
                    if isinstance(exp, (list, tuple)) and len(exp) > 0:
                        exp = exp[0]
                    
                    if exp:
                        metadata["Experiment Name"] = getattr(exp, 'name', 'N/A')
                        metadata["Experiment Description"] = getattr(exp, 'description', 'N/A')
                        metadata["Acquisition Date"] = getattr(exp, 'date', 'N/A')
                        metadata["Acquisition Time"] = getattr(exp, 'time', 'N/A')
            except:
                metadata.update({
                    "Experiment Name": "N/A",
                    "Experiment Description": "N/A",
                    "Acquisition Date": "N/A",
                    "Acquisition Time": "N/A",
                })
            
            # System information
            try:
                if hasattr(nd2, 'custom_data') and nd2.custom_data:
                    custom = nd2.custom_data
                    if isinstance(custom, dict):
                        # Look for hardware settings
                        if 'HardwareSetting' in custom:
                            hw = custom['HardwareSetting']
                            if isinstance(hw, dict):
                                metadata["System Name"] = hw.get('sCamera', 'N/A')
                                metadata["Camera Model"] = hw.get('sCameraModel', 'N/A')
            except:
                pass
            
            # CORRECTED: Objective and microscope information from metadata.channels
            try:
                if hasattr(nd2, 'metadata') and nd2.metadata:
                    meta = nd2.metadata
                    # Access channels directly from metadata object
                    if hasattr(meta, 'channels') and meta.channels:
                        channels = meta.channels
                        if len(channels) > 0:
                            first_channel = channels[0]
                            # Access microscope from channel
                            if hasattr(first_channel, 'microscope') and first_channel.microscope:
                                mic = first_channel.microscope
                                metadata["Objective Model"] = getattr(mic, 'objectiveName', 'N/A')
                                metadata["Objective Magnification"] = str(getattr(mic, 'objectiveMagnification', 'N/A'))
                                metadata["Objective NA"] = str(getattr(mic, 'objectiveNumericalAperture', 'N/A'))
                                metadata["Objective Medium"] = str(getattr(mic, 'immersionRefractiveIndex', 'N/A'))
                            else:
                                metadata.update({
                                    "Objective Model": "N/A",
                                    "Objective Magnification": "N/A",
                                    "Objective NA": "N/A",
                                    "Objective Medium": "N/A",
                                })
                    else:
                        metadata.update({
                            "Objective Model": "N/A",
                            "Objective Magnification": "N/A",
                            "Objective NA": "N/A",
                            "Objective Medium": "N/A",
                        })
            except Exception as e:
                metadata.update({
                    "Objective Model": "N/A",
                    "Objective Magnification": "N/A",
                    "Objective NA": "N/A",
                    "Objective Medium": "N/A",
                })
            
            # CORRECTED: Channel information from metadata.channels
            try:
                channel_names = []
                channel_details = []
                if hasattr(nd2, 'metadata') and nd2.metadata:
                    meta = nd2.metadata
                    # Access channels directly from metadata object
                    if hasattr(meta, 'channels') and meta.channels:
                        channels = meta.channels
                        for i, ch in enumerate(channels):
                            # Access channel metadata
                            if hasattr(ch, 'channel') and ch.channel:
                                ch_meta = ch.channel
                                name = getattr(ch_meta, 'name', f'Channel {i+1}')
                                channel_names.append(name)
                                
                                details = f"{name}"
                                em = getattr(ch_meta, 'emissionLambdaNm', None)
                                ex = getattr(ch_meta, 'excitationLambdaNm', None)
                                if em:
                                    details += f" (Em: {em}nm)"
                                if ex:
                                    details += f" (Ex: {ex}nm)"
                                channel_details.append(details)
                            else:
                                # Fallback: try to get name directly from channel object
                                name = getattr(ch, 'name', f'Channel {i+1}')
                                channel_names.append(name)
                                channel_details.append(name)
                
                metadata["Channel Names"] = channel_names if channel_names else ["N/A"]
                metadata["Channel Details"] = "\n".join(channel_details) if channel_details else "N/A"
            except Exception as e:
                metadata["Channel Names"] = ["N/A"]
                metadata["Channel Details"] = "N/A"
            
            # Pixel size information
            try:
                if hasattr(nd2, 'voxel_size') and nd2.voxel_size:
                    voxel = nd2.voxel_size
                    metadata["Pixel Size X"] = f"{voxel.x:.6f}" if hasattr(voxel, 'x') and voxel.x else "N/A"
                    metadata["Pixel Size Y"] = f"{voxel.y:.6f}" if hasattr(voxel, 'y') and voxel.y else "N/A"
                    metadata["Pixel Size Z"] = f"{voxel.z:.6f}" if hasattr(voxel, 'z') and voxel.z else "N/A"
                    metadata["Pixel Size Unit"] = "µm"
                else:
                    metadata.update({
                        "Pixel Size X": "N/A",
                        "Pixel Size Y": "N/A", 
                        "Pixel Size Z": "N/A",
                        "Pixel Size Unit": "N/A",
                    })
            except:
                metadata.update({
                    "Pixel Size X": "N/A",
                    "Pixel Size Y": "N/A", 
                    "Pixel Size Z": "N/A",
                    "Pixel Size Unit": "N/A",
                })
            
            # Additional metadata from text_info
            try:
                if hasattr(nd2, 'text_info') and nd2.text_info:
                    text_info = nd2.text_info
                    if isinstance(text_info, dict):
                        # Common text info fields
                        metadata["Document User Name"] = text_info.get('sUser', 'N/A')
                        metadata["Document Creation Date"] = text_info.get('dTimeStart', 'N/A')
                        metadata["Software Version"] = text_info.get('sSoftwareVersion', 'N/A')
                        metadata["Microscope Type"] = text_info.get('sMicroscopeType', 'N/A')
                        # ADD THIS LINE for Modality
                        metadata["Modality"] = text_info.get('Modality', 'N/A')
            except:
                pass
            
            # Format combined date/time if available
            try:
                date_str = metadata.get("Acquisition Date", "")
                time_str = metadata.get("Acquisition Time", "")
                if date_str != "N/A" and time_str != "N/A" and date_str and time_str:
                    metadata["Document Creation Date"] = f"{date_str} {time_str}"
                elif hasattr(nd2, 'attributes') and nd2.attributes:
                    # Try to get creation time from attributes
                    attrs = nd2.attributes
                    if 'textinfo' in attrs:
                        text_attrs = attrs['textinfo']
                        if 'dTimeStart' in text_attrs:
                            metadata["Document Creation Date"] = str(text_attrs['dTimeStart'])
            except:
                pass
            
            return metadata
            
    except Exception as e:
        raise Exception(f"Failed to extract ND2 metadata: {str(e)}")

def map_nd2_to_remind_fields(nd2_metadata):
    """
    Map ND2 metadata to ReMInD form fields.
    
    Args:
        nd2_metadata (dict): Metadata dictionary from extract_nd2_metadata
        
    Returns:
        dict: Dictionary with ReMInD field names as keys
    """
    remind_fields = {}
    
    # Map ND2 keys to ReMInD fields
    field_mapping = {
        "Experiment name": nd2_metadata.get("Experiment Name", ""),
        "Date and time": nd2_metadata.get("Document Creation Date", ""),
        "Experimentor Name(s)": nd2_metadata.get("Document User Name", ""),
        "Microscope name": nd2_metadata.get("System Name", ""),
        "Software": nd2_metadata.get("Software Version", ""),
        "Image format": ".nd2",
        "Notes": f"Imported from ND2 file: {nd2_metadata.get('File Name', '')}",
    }
    
    # Handle objective information
    obj_model = nd2_metadata.get("Objective Model", "")
    obj_mag = nd2_metadata.get("Objective Magnification", "")
    obj_na = nd2_metadata.get("Objective NA", "")
    
    if obj_mag != "N/A" and obj_na != "N/A":
        field_mapping["Objective"] = f"{obj_mag}x/{obj_na}"
        if obj_model != "N/A" and obj_model:
            field_mapping["Objective"] += f" {obj_model}"
    elif obj_model != "N/A":
        field_mapping["Objective"] = obj_model
    else:
        field_mapping["Objective"] = ""
    
    # Handle immersion
    immersion = nd2_metadata.get("Objective Medium", "")
    if immersion != "N/A" and immersion:
        # Convert refractive index to immersion type
        try:
            ri = float(immersion)
            if ri < 1.1:
                field_mapping["Immersion"] = "Air"
            elif ri < 1.4:
                field_mapping["Immersion"] = "Water"
            elif ri > 1.5:
                field_mapping["Immersion"] = "Oil"
            else:
                field_mapping["Immersion"] = "Other"
        except:
            field_mapping["Immersion"] = immersion
    else:
        field_mapping["Immersion"] = ""
    
    # Handle channel information
    channel_names = nd2_metadata.get("Channel Names", [])
    if isinstance(channel_names, list) and channel_names[0] != "N/A":
        field_mapping["Channel info"] = ", ".join(channel_names)
    else:
        field_mapping["Channel info"] = ""
    
    # Handle Z-stack and time series
    z_slices = nd2_metadata.get("Z Slices", "1")
    time_points = nd2_metadata.get("Time Points", "1")
    
    try:
        field_mapping["Z stack"] = "Yes" if int(z_slices) > 1 else "No"
    except:
        field_mapping["Z stack"] = "No"
    
    try:
        field_mapping["Time series"] = "Yes" if int(time_points) > 1 else "No"
    except:
        field_mapping["Time series"] = "No"
    
    # UPDATED: Set imaging mode from Modality field
    modality = nd2_metadata.get("Modality", "")
    if modality != "N/A" and modality:
        field_mapping["Imaging mode"] = modality
    else:
        field_mapping["Imaging mode"] = ""  # Will be empty if no modality found
    
    return field_mapping

# Example usage function for testing
def test_nd2_extraction(file_path):
    """Test function to extract and display ND2 metadata"""
    try:
        metadata = extract_nd2_metadata(file_path)
        remind_fields = map_nd2_to_remind_fields(metadata)
        
        print("=== ND2 METADATA ===")
        for key, value in metadata.items():
            print(f"{key}: {value}")
            
        print("\n=== REMIND FIELDS ===")
        for key, value in remind_fields.items():
            print(f"{key}: {value}")
            
        return metadata, remind_fields
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    # Test with a file path
    test_file = input("Enter ND2 file path: ")
    if test_file and os.path.exists(test_file):
        test_nd2_extraction(test_file)
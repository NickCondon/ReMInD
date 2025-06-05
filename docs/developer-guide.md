# ReMInD Developer Guide

## Project Structure
```
remind/
├── src/
│   ├── ReMInD_Lite_v2.27.py     # Main application
│   ├── CZI_MetadataGUI.py       # Zeiss CZI metadata extraction
│   ├── LIF_MetadataGUI.py       # Leica LIF metadata extraction
│   └── Nd2_v2a.py               # Nikon ND2 metadata extraction
├── docs/                        # Documentation
├── templates/                   # Example templates
└── examples/                    # Sample outputs
```

## Development Setup

### Prerequisites
- Python 3.7+
- Git

### Installation
```bash
git clone https://github.com/yourusername/remind-lite-gui.git
cd remind-lite-gui
pip install -r requirements.txt
```

### Running from Source
```bash
python src/ReMInD_Lite_v2.27.py
```

## Architecture Overview

### Main Components

#### REMBIGUI Class
- **Purpose**: Main application window and logic
- **Key Methods**:
  - `__init__()` - Window setup and initialization
  - `build_form()` - Creates the GUI form
  - `load_fields_from_image()` - Metadata extraction dispatcher
  - `generate_readme()` - Creates ReadMe.txt files
  - `export_as_json()` - JSON export functionality

#### Metadata Extractors
- **CZI_MetadataGUI.py** - Handles Zeiss CZI files using `czifile` library
- **LIF_MetadataGUI.py** - Handles Leica LIF files using `readlif` library  
- **Nd2_v2a.py** - Handles Nikon ND2 files using `nd2` library

#### ToolTip Class
- **Purpose**: Provides hover help text for form fields
- **Usage**: `ToolTip(widget, "Help text")`

### Key Features Implementation

#### Responsive Design
```python
# Screen size detection and window sizing
screen_width = self.root.winfo_screenwidth()
if screen_width >= 1920:
    window_width = 900
elif screen_width >= 1366:
    window_width = 750
else:
    window_width = 650
```

#### Metadata Extraction Pipeline
```python
def load_fields_from_image(self):
    # 1. File selection
    path = filedialog.askopenfilename(...)
    
    # 2. Format detection
    ext = os.path.splitext(path)[1].lower()
    
    # 3. Dispatch to appropriate extractor
    if ext == ".czi":
        metadata_output, _ = extract_metadata(path)
    elif ext == ".lif":
        metadata_output = extract_lif_metadata(path)[0]
    elif ext == ".nd2":
        metadata_output = extract_nd2_metadata(path)
    
    # 4. Map to form fields
    # 5. Display in metadata panel
    # 6. Store for export
```

## Adding New Features

### Adding a New File Format

1. **Create extractor module**:
```python
# src/NEW_MetadataGUI.py
def extract_new_metadata(file_path):
    """Extract metadata from NEW format files."""
    try:
        # Implementation here
        return metadata_dict
    except Exception as e:
        raise Exception(f"Failed to extract NEW metadata: {e}")
```

2. **Add to main application**:
```python
# In ReMInD_Lite_v2.27.py
from NEW_MetadataGUI import extract_new_metadata

# In load_fields_from_image():
elif ext == ".new":
    try:
        metadata_output = extract_new_metadata(path)
        # Map fields and display
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract NEW metadata:\n{e}")
```

3. **Update file dialog**:
```python
filetypes = [
    ("Image files", "*.tif *.tiff *.czi *.lif *.nd2 *.new"),  # Add *.new
    ("All files", "*.*"),
]
```

### Adding New Form Fields

1. **Add to fields list**:
```python
self.fields = [
    # ... existing fields ...
    ("New Field", "", "Help text for new field"),
]
```

2. **Handle in ReadMe generation**:
```python
# Field automatically included in generate_readme()
# No additional code needed for basic text fields
```

3. **Add dropdown options**:
```python
("New Dropdown", ["Option1", "Option2", "Option3"], "Help text"),
```

### Customizing the Interface

#### Adding New Buttons
```python
# In build_form(), add to buttons list:
buttons = [
    # ... existing buttons ...
    ("New Feature", self.new_feature_method),
]

def new_feature_method(self):
    """Implementation of new feature."""
    pass
```

#### Custom Field Types
```python
# In build_form(), add new elif condition:
elif label == "Special Field":
    # Custom widget implementation
    custom_widget = tk.Scale(parent, from_=0, to=100, orient="horizontal")
    custom_widget.grid(row=self.row_counter, column=1, sticky="ew")
    self.entries[label] = custom_widget
```

## Building Executables

### Using PyInstaller
```bash
# Install PyInstaller
pip install pyinstaller

# Basic build
pyinstaller --onefile --windowed src/ReMInD_Lite_v2.27.py

# Advanced build with dependencies
pyinstaller --onefile --windowed --name "ReMInD_Lite_v2.27" \
    --add-data "src/CZI_MetadataGUI.py;." \
    --add-data "src/LIF_MetadataGUI.py;." \
    --add-data "src/Nd2_v2a.py;." \
    src/ReMInD_Lite_v2.27.py
```

### Build Script
Create `build.bat`:
```batch
@echo off
echo Building ReMInD Lite...
pip install pyinstaller czifile readlif nd2
pyinstaller --onefile --windowed --name "ReMInD_Lite_v2.27" src/ReMInD_Lite_v2.27.py
echo Build complete! Check dist/ folder.
pause
```

## Testing

### Manual Testing Checklist
- [ ] Application launches without errors
- [ ] All form fields accept input
- [ ] Template loading works
- [ ] Metadata extraction for each format (CZI, LIF, ND2)
- [ ] ReadMe.txt generation
- [ ] JSON export
- [ ] File loading and form population
- [ ] Font size adjustment
- [ ] Help dialog displays
- [ ] Responsive design on different screen sizes

### Adding Automated Tests
```python
# tests/test_metadata.py
import unittest
from src.CZI_MetadataGUI import extract_metadata

class TestMetadataExtraction(unittest.TestCase):
    def test_czi_extraction(self):
        # Test with sample CZI file
        metadata, _ = extract_metadata("sample.czi")
        self.assertIsInstance(metadata, dict)
        self.assertIn("System Name", metadata)

if __name__ == "__main__":
    unittest.main()
```

## Code Style and Standards

### Python Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Handle exceptions appropriately

### GUI Standards
- Consistent font usage (`self.app_font`)
- Proper tooltip implementation
- Responsive design considerations
- Accessible color schemes

### Error Handling
```python
try:
    # Risky operation
    result = some_operation()
except SpecificException as e:
    messagebox.showerror("Error", f"Specific error occurred: {e}")
except Exception as e:
    messagebox.showerror("Error", f"Unexpected error: {e}")
```

## Contributing

### Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Make changes and test
4. Commit with descriptive messages
5. Push to fork and create pull request

### Pull Request Guidelines
- Include description of changes
- Test on multiple screen resolutions
- Update documentation if needed
- Add examples for new features

### Issue Reporting
When reporting bugs, include:
- ReMInD version
- Operating system
- Steps to reproduce
- Error messages
- Sample files (if applicable)

## API Reference

### Core Functions

#### extract_metadata(file_path)
Extract metadata from CZI files.
- **Parameters**: `file_path` (str) - Path to CZI file
- **Returns**: `(metadata_dict, raw_metadata)` tuple
- **Raises**: Exception if extraction fails

#### extract_lif_metadata(file_path)
Extract metadata from LIF files.
- **Parameters**: `file_path` (str) - Path to LIF file  
- **Returns**: List of metadata dictionaries (one per series)
- **Raises**: Exception if extraction fails

#### extract_nd2_metadata(file_path)
Extract metadata from ND2 files.
- **Parameters**: `file_path` (str) - Path to ND2 file
- **Returns**: Metadata dictionary
- **Raises**: Exception if extraction fails

### Utility Functions

#### map_nd2_to_remind_fields(metadata_dict)
Map ND2 metadata to ReMInD form fields.
- **Parameters**: `metadata_dict` (dict) - Raw ND2 metadata
- **Returns**: Dictionary mapping ReMInD field names to values

## Release Process

1. **Version Update**: Update `APP_VERSION` in source code
2. **Testing**: Run manual test checklist
3. **Documentation**: Update README and changelog  
4. **Build**: Create executable with PyInstaller
5. **GitHub Release**: Create release with executable attachment
6. **Announcement**: Notify users of new version

## Dependencies

### Core Dependencies
- **tkinter** - GUI framework (included with Python)
- **datetime** - Date/time handling
- **os, glob** - File system operations
- **json** - JSON export functionality

### Metadata Dependencies
- **czifile** - Zeiss CZI file reading
- **readlif** - Leica LIF file reading
- **nd2** - Nikon ND2 file reading

### Development Dependencies
- **pyinstaller** - Executable building
- **unittest** - Testing framework

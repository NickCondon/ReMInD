# ReMInD Troubleshooting Guide

## Common Issues and Solutions

### Installation and Launch Issues

#### "Python not found" error
**Problem**: Error when running from source
**Solution**: 
1. Install Python 3.7+ from python.org
2. Ensure Python is added to system PATH
3. Try `python3` instead of `python` on Linux/Mac

#### Executable won't start
**Problem**: ReMInD.exe doesn't launch
**Solutions**:
1. Check Windows Defender/antivirus - may block unknown executables
2. Right-click → "Run as administrator"
3. Download latest version from GitHub releases
4. Try running from command prompt to see error messages

#### Missing DLL errors
**Problem**: "VCRUNTIME140.dll not found" or similar
**Solution**: Install Microsoft Visual C++ Redistributable

### Metadata Extraction Issues

#### "Failed to extract CZI metadata"
**Possible Causes**:
- Corrupted CZI file
- Very old CZI format version
- File permissions issue

**Solutions**:
1. Try opening file in ZEN software first
2. Copy file to local drive (not network location)
3. Check file isn't corrupted by opening in ImageJ

#### "Failed to extract LIF metadata"  
**Possible Causes**:
- Encrypted LIF file
- Incomplete file transfer
- Unsupported LIF version

**Solutions**:
1. Re-export from LAS X software
2. Try different LIF file to test
3. Check file size - should be >1MB for typical files

#### "Failed to extract ND2 metadata"
**Possible Causes**:
- Very old ND2 format
- File created with older NIS-Elements
- Compressed/archived ND2

**Solutions**:
1. Open in NIS-Elements first to verify
2. Try "Save As" to create new ND2
3. Check ND2 isn't password protected

#### No metadata appears after extraction
**Problem**: Extraction succeeds but fields remain empty
**Causes**:
- File has minimal embedded metadata
- Metadata fields don't match expected format

**Solutions**:
1. Check "Extracted Image Metadata" panel for raw data
2. Manually enter information from acquisition software
3. Contact file creator for acquisition details

### File Operations Issues

#### Can't save ReadMe.txt
**Problem**: Permission denied when saving
**Solutions**:
1. Choose different save location (not C:\ root)
2. Run as administrator
3. Check folder isn't read-only
4. Ensure adequate disk space

#### Template not loading
**Problem**: Template doesn't appear in startup dialog
**Requirements**:
- Filename must end with `_ReadME_template.txt`
- File must be in same folder as ReMInD.exe
- File must be valid ReadMe.txt format

**Solutions**:
1. Check filename spelling and case
2. Move template to correct location
3. Test template by loading manually

#### Can't load existing ReadMe
**Problem**: Error loading previously saved ReadMe
**Possible Causes**:
- File encoding issues (non-UTF-8)
- Manually edited file with syntax errors
- File corruption

**Solutions**:
1. Open file in text editor to check format
2. Ensure consistent line endings
3. Re-create from backup if available

### Interface Issues

#### Window too large for screen
**Problem**: Application doesn't fit on screen
**Solutions**:
1. Use A- button to decrease font size
2. Resize window by dragging edges
3. Use scroll bars to navigate
4. Update to latest version (better screen handling)

#### Text too small to read
**Problem**: GUI text is hard to read
**Solutions**:
1. Use A+ button to increase font size
2. Increase Windows display scaling
3. Try different monitor resolution

#### Buttons not responding
**Problem**: Clicking buttons has no effect
**Possible Causes**:
- Application frozen
- Modal dialog hidden behind window
- System resource issues

**Solutions**:
1. Check for hidden dialog boxes
2. Restart application
3. Close other programs to free memory
4. Restart computer if persistent

### Data Issues

#### Special characters not displaying
**Problem**: Accented characters or symbols show as "?" 
**Solution**: 
1. Ensure UTF-8 encoding when saving
2. Use Windows Character Map for special symbols
3. Avoid problematic characters in filenames

#### Date format issues
**Problem**: Dates not parsing correctly
**Solution**: Use ISO format (YYYY-MM-DD HH:MM:SS)

#### Long text cut off
**Problem**: Text fields truncate long entries
**Solutions**:
1. Use Notes field for lengthy descriptions
2. Abbreviate where possible
3. Consider external documentation for very detailed info

## Error Messages

### "Could not access the network location"
**Meaning**: RDM connectivity check failed
**Action**: Enter RDM information manually in text field

### "No images found in LIF file"
**Meaning**: LIF file doesn't contain recognizable image series
**Action**: Check file in LAS X software, may be corrupted

### "Unsupported file format"
**Meaning**: File type not supported for metadata extraction
**Action**: Convert to supported format (CZI/LIF/ND2) or enter manually

### "Permission denied"
**Meaning**: Can't write to selected location
**Action**: Choose different folder or run as administrator

## Performance Issues

#### Slow metadata extraction
**Causes**: 
- Very large files (>2GB)
- Network file locations
- Limited system resources

**Solutions**:
1. Copy files to local SSD before processing
2. Close other applications
3. Process smaller file sets
4. Consider more powerful computer for routine use

#### Application freezing
**Causes**:
- Insufficient memory
- Corrupted file processing
- System resource conflicts

**Solutions**:
1. Restart application
2. Process files individually
3. Check system resources (Task Manager)
4. Update graphics drivers

## Getting Additional Help

### Before Contacting Support
1. Try restarting the application
2. Test with a different file
3. Check this troubleshooting guide
4. Review the user guide for proper procedures

### Information to Include
When reporting issues, please provide:
- ReMInD version number
- Operating system and version
- File type and approximate size
- Exact error message (screenshot helpful)
- Steps to reproduce the problem
- Whether issue is consistent or intermittent

### Contact Information
- **GitHub Issues**: Create issue at repository page
- **UQ Users**: Contact IMB Microscopy facility
- **Email**: n.condon@uq.edu.au (for University of Queensland users)

### Workarounds

#### Manual metadata entry
If automatic extraction fails:
1. Open image file in acquisition software
2. Export metadata as text file
3. Copy relevant information to ReMInD form
4. Include original metadata file with data

#### Alternative file formats
If specific format isn't supported:
1. Export images as OME-TIFF (preserves metadata)
2. Save acquisition parameters as text file
3. Use ImageJ to extract basic information
4. Consult acquisition software documentation

#### Batch processing
For multiple files:
1. Create template from first file
2. Use template for subsequent files
3. Modify only differences between experiments
4. Consider scripting for very large datasets

## Known Limitations

### File Format Support
- Only CZI, LIF, and ND2 formats supported for auto-extraction
- Some very old format versions may not work
- Encrypted or password-protected files not supported

### System Requirements
- Windows 10/11 recommended
- Minimum 4GB RAM for large files
- SSD recommended for better performance
- Network locations may be slower

### Metadata Mapping
- Not all metadata fields can be automatically mapped
- Some instrument-specific settings require manual entry
- Field mapping may vary between software versions

## Future Improvements

### Planned Features
- Additional file format support (OME-TIFF, VSI)
- Batch processing capabilities
- OMERO database integration
- Command-line interface
- Enhanced template system

### Requested Enhancements
- Dark mode interface
- Custom field definitions
- Multi-language support
- Integration with laboratory information systems
- Automated backup and versioning

Report feature requests through GitHub Issues or contact the development team.

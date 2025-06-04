import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import datetime
import os
import glob
import tkinter.ttk as ttk
from CZI_MetadataGUI import extract_metadata
from LIF_MetadataGUI import extract_lif_metadata
from Nd2_v2a import extract_nd2_metadata, map_nd2_to_remind_fields
import json

APP_VERSION = "ReMInD Lite v2.27"
APP_AUTHOR = "Nicholas Condon, IMB Microscopy, The University of Queensland, Brisbane Australia"
APP_DATE = "June 2025"

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tooltip or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class REMBIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Recommended Metadata Interface for Documentation - " + APP_VERSION)

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate appropriate window size - make it narrower
        if screen_width >= 1920:
            window_width = 900
            window_height = 700
        elif screen_width >= 1366:
            window_width = 750
            window_height = 650
        else:
            window_width = 650
            window_height = 600
    
        # Don't exceed 80% of screen size
        window_width = min(window_width, int(screen_width * 0.8))
        window_height = min(window_height, int(screen_height * 0.8))
        
        # Center the window on screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window geometry and make it resizable
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(600, 500)  # Reduced minimum size
    
        # Make the window scrollable if content exceeds window size
        self.setup_scrollable_window()

        self.entries = {}
        self.extra_fields = {}
        self.text_fields = {}

        # Font size management - adjust based on screen size
        base_size = 10 if screen_width >= 1920 else 9 if screen_width >= 1200 else 8
        self.base_font_size = base_size
        self.font_family = "Segoe UI"
        self.app_font = tkfont.Font(family=self.font_family, size=self.base_font_size)
        self.bold_font = tkfont.Font(family=self.font_family, size=self.base_font_size, weight="bold")

        self.fields = [
            ("Experiment name", "", "Title of the experiment."),
            ("RDM Info", "", "Green Indicator = connection to InstGateway successful, otherwise write the RDM project or storage info "),
            ("Date and time", "", "Date and time of acquisition. The Now button will autopopulate the fields"),
            ("Experimentor Name(s)", "", "Enter your full name."),
            ("Sample Information", "", "e.g. Sample ID, or cell line, animal strain"),
            ("Genetic Modifications", "", "e.g. eGFP- mCherry-y"),
            ("Antibody or probes", "", "e.g. Alexa488-Phalloidin, DAPI, Alexa647-GaM"),
            ("Fixation / Live Media", "", "Fixation method used, or details of live imaging reagents"),
            ("Sample mounting condition", "", "35mm Dish, #1.5 coverslip, chamber slide"),
            ("Microscope name", "", "e.g. Confocal 5"),
            ("Objective", "", "Objective lens details. e.g. Plan Apochromat 63x 1.4NA"),
            ("Immersion", ["Air", "Water", "Immersol W", "Glycerol", "Silicone", "Oil-23", "Oil-37", "Other"], "Select the immersion used."),
            ("Imaging mode", ["Confocal", "Widefield", "Spinning Disc Confocal", "Lightsheet", "Other"], "Select the imaging mode used."),
            ("Specialist modality", ["", "Airyscan", "STED", "FLIM", "2Photon", "TIRF", "Other"], "Select any specialist imaging modality used."),
            ("Environmental Conditions", "", "e.g. Temperature and CO2"),
            ("Channel info", "", "Channel names, stains or labels used."),
            ("Z-stack", ["Yes", "No", "Both"], "Was a Z-stack acquired?"),
            ("Time series", ["Yes", "No", "Both"], "Was this a time-lapse series?"),
            ("Image format", "", "Image file format (e.g., .czi, .tif, .lif)."),
            ("Notes", "", "Analysis intent or relevant notes."),
        ]

        self.build_form()
        self.root.after(200, self.select_and_load_template)

    def check_rdm_connectivity(self):
        # This method is no longer needed, but keeping it for backward compatibility
        # Remove this method entirely if you want
        pass

    def build_form(self):
        # Use self.form_root instead of self.root for all grid operations
        parent = self.form_root if hasattr(self, 'form_root') else self.root
        
        self.row_counter = 0
        for label, options, tooltip_text in self.fields:
            tk.Label(parent, text=label, font=self.app_font).grid(row=self.row_counter, column=0, sticky="e", padx=5, pady=2)

            if label == "RDM Info":
                # Simple text entry field - no LED indicator or connectivity check
                entry = tk.Entry(parent, font=self.app_font)
                entry.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")
                self.entries[label] = entry
                ToolTip(entry, tooltip_text)

            elif isinstance(options, list):
                var = tk.StringVar()
                combo = ttk.Combobox(parent, textvariable=var, values=options, state="normal", font=self.app_font, style="TCombobox")
                combo.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")
                self.entries[label] = var
                ToolTip(combo, tooltip_text)

                def handle_other(event, label=label):
                    if var.get() == "Other":
                        if label not in self.extra_fields:
                            other_row = self.row_counter + len(self.extra_fields) + 1
                            entry = tk.Entry(parent, font=self.app_font)
                            entry.grid(row=other_row, column=1, padx=5, pady=2, sticky="ew")
                            tk.Label(parent, text=f"{label} (Other)", font=self.app_font).grid(row=other_row, column=0, sticky="e")
                            self.extra_fields[label] = entry
                            ToolTip(entry, f"Specify 'Other' for {label.lower()}")
                    else:
                        if label in self.extra_fields:
                            self.extra_fields[label].destroy()
                            del self.extra_fields[label]

                combo.bind("<<ComboboxSelected>>", handle_other)

            elif label == "Date and time":
                frame = tk.Frame(parent)
                frame.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")

                date_entry = tk.Entry(frame)
                date_entry.pack(side="left", fill="x", expand=True)
                self.entries[label] = date_entry
                ToolTip(date_entry, tooltip_text)

                def insert_datetime(entry_widget=date_entry):
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, now)

                timestamp_btn = tk.Button(frame, text="Now", command=insert_datetime, font=self.app_font)
                timestamp_btn.pack(side="right", padx=5)
                ToolTip(timestamp_btn, "Insert current date and time")

            elif label == "Notes":
                frame = tk.Frame(parent)
                frame.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")

                text_box = tk.Text(frame, height=8, width=50, font=self.app_font)  # Reduced height for small screens
                text_box.pack(side="left", fill="both", expand=True)
                self.entries[label] = text_box
                self.text_fields[label] = text_box
                ToolTip(text_box, tooltip_text)

                def insert_timestamp():
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    text_box.insert(tk.END, f"\n[{now}] ")

                timestamp_btn = tk.Button(frame, text="Timestamp", command=insert_timestamp, font=self.app_font)
                timestamp_btn.pack(side="right", padx=5, pady=5)
                ToolTip(timestamp_btn, "Insert timestamp into notes")

            else:
                entry = tk.Entry(parent, font=self.app_font)
                entry.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")
                self.entries[label] = entry
                ToolTip(entry, tooltip_text)

            self.row_counter += 1

        # Configure column weights for proper resizing
        parent.grid_columnconfigure(1, weight=1)

        # Add a scrollable, read-only text widget for metadata display
        self.metadata_frame = tk.Frame(parent)
        self.metadata_frame.grid(row=self.row_counter, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0, 10))

        tk.Label(self.metadata_frame, text="Extracted Image Metadata:").pack(anchor="w")

        self.metadata_text = tk.Text(self.metadata_frame, height=8, width=80, wrap="none", state="disabled")  # Reduced height
        self.metadata_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.metadata_frame, command=self.metadata_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.metadata_text.config(yscrollcommand=scrollbar.set)

        self.row_counter += 1

        # Place the Load Fields from Image File button on its own row above the rest
        loadfields_frame = tk.Frame(parent)
        loadfields_frame.grid(row=self.row_counter + 1, column=0, columnspan=2, pady=(0, 5))
        tk.Button(loadfields_frame, text="Load Fields from Image File", command=self.load_fields_from_image, font=self.app_font).pack(side="left", padx=5)

        # Main button row - make buttons smaller for low res
        button_frame = tk.Frame(parent)
        button_frame.grid(row=self.row_counter + 2, column=0, columnspan=2, pady=10)

        # Create buttons in a more compact layout
        buttons = [
            ("Generate ReadMe.txt", self.generate_readme),
            ("Load ReadMe.txt", self.load_existing),
            ("Clear Form", self.clear_form),
            ("Help", self.show_help),
            ("Exit", self.root.quit),
            ("A+", self.increase_font_size),
            ("A-", self.decrease_font_size),
            ("Export as JSON", self.export_as_json)
        ]
        
        # Arrange buttons in two rows if screen is narrow
        screen_width = self.root.winfo_screenwidth()
        if screen_width < 1366:  # Small screen
            # First row
            row1_frame = tk.Frame(button_frame)
            row1_frame.pack(pady=2)
            for text, command in buttons[:4]:
                tk.Button(row1_frame, text=text, command=command, font=self.app_font).pack(side="left", padx=2)
            
            # Second row
            row2_frame = tk.Frame(button_frame)
            row2_frame.pack(pady=2)
            for text, command in buttons[4:]:
                tk.Button(row2_frame, text=text, command=command, font=self.app_font).pack(side="left", padx=2)
        else:
            # Single row for larger screens
            for text, command in buttons:
                tk.Button(button_frame, text=text, command=command, font=self.app_font).pack(side="left", padx=5)

        version_label = tk.Label(parent, text=f"{APP_VERSION}  —  {APP_DATE}", fg="gray")
        version_label.grid(row=self.row_counter + 3, column=0, columnspan=2, pady=(0, 5))

    def setup_scrollable_window(self):
        """Create a scrollable main window for low resolution screens"""
        # Create main canvas and scrollbar
        self.main_canvas = tk.Canvas(self.root)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas)

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.main_canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
        self.main_canvas.bind("<Button-4>", lambda e: self.main_canvas.yview_scroll(-1, "units"))  # Linux
        self.main_canvas.bind("<Button-5>", lambda e: self.main_canvas.yview_scroll(1, "units"))   # Linux

        # Update the root reference for form building
        self.form_root = self.scrollable_frame

    def generate_readme(self):
        # Get experiment name for filename
        experiment_name = self.entries["Experiment name"].get().strip()
        if experiment_name:
            # Clean filename (remove invalid characters)
            clean_name = "".join(c for c in experiment_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            default_filename = f"{clean_name}_ReadME.txt"
        else:
            default_filename = "ReadME.txt"
            
        save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 initialfile=default_filename,  # <-- Use dynamic filename
                                                 filetypes=[("Text files", "*.txt")],
                                                 title="Save ReadMe.txt as")
        if not save_path:
            return
        if os.path.exists(save_path):
            if not messagebox.askyesno("Overwrite?", "This file already exists. Overwrite?"):
                return

        lines = [f"# Generated by {APP_VERSION} — {APP_AUTHOR}, {APP_DATE}", ""]
        for label, _, _ in self.fields:
            if label in self.text_fields:
                value = self.text_fields[label].get("1.0", tk.END).strip()
                lines.append(f"{label}:\n---\n{value}\n---")
            elif isinstance(self.entries[label], tk.StringVar):
                lines.append(f"{label}: {self.entries[label].get()}")
            else: 
                lines.append(f"{label}: {self.entries[label].get()}")
            if label in self.extra_fields:
                lines.append(f"{label} (Other): {self.extra_fields[label].get()}")

        # --- Append metadata if available ---
        if hasattr(self, "last_metadata_output") and self.last_metadata_output:
            lines.append("\n# Extracted Image Metadata")
            for k, v in self.last_metadata_output.items():
                if isinstance(v, list):
                    v = ", ".join(str(i) for i in v)
                lines.append(f"{k}: {v}")

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("Success", "ReadMe.txt generated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write file: {e}")

    def load_existing(self):
        path = filedialog.askopenfilename(title="Select existing ReadMe.txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        self.parse_readme_file(path)

    def clear_form(self):
        for label, widget in self.entries.items():
            if label in self.text_fields:
                widget.delete("1.0", tk.END)
            elif isinstance(widget, tk.StringVar):
                widget.set("")
            else:
                widget.delete(0, tk.END)

        for extra in list(self.extra_fields.values()):
            extra.destroy()
        self.extra_fields.clear()

        # Clear the Extracted Image Metadata box
        self.metadata_text.config(state="normal")
        self.metadata_text.delete("1.0", tk.END)
        self.metadata_text.config(state="disabled")

    def parse_readme_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            idx = 0
            extracted_metadata = {}  # Store extracted metadata separately
            
            while idx < len(lines):
                line = lines[idx].strip()
                if line.startswith("#") or not line:
                    idx += 1
                    continue
                    
                # Check if we've reached the "Extracted Image Metadata" section
                if line == "# Extracted Image Metadata":
                    idx += 1
                    # Parse all the metadata lines that follow
                    while idx < len(lines):
                        metadata_line = lines[idx].strip()
                        if metadata_line and ": " in metadata_line:
                            key, value = metadata_line.split(": ", 1)
                            # Convert comma-separated values back to lists where appropriate
                            if ", " in value and key in ["Channel Names", "Acquisition Modes"]:
                                extracted_metadata[key] = value.split(", ")
                            else:
                                extracted_metadata[key] = value
                        idx += 1
                    break  # We've processed all metadata
                    
                # Handle multi-line fields (like Notes)
                if line.endswith(":") and idx + 1 < len(lines) and lines[idx + 1].strip() == "---":
                    label = line[:-1].strip()
                    idx += 2
                    value_lines = []
                    while idx < len(lines) and lines[idx].strip() != "---":
                        value_lines.append(lines[idx].rstrip("\n"))
                        idx += 1
                    value = "\n".join(value_lines)
                    idx += 1
                else:
                    # Handle single-line fields
                    if ": " not in line:
                        idx += 1
                        continue
                    label, value = line.split(": ", 1)
                    label = label.strip()
                    value = value.strip()
                    idx += 1

                # Populate the form fields (existing logic)
                if label in self.text_fields:
                    self.text_fields[label].delete("1.0", tk.END)
                    self.text_fields[label].insert("1.0", value)
                elif label in self.entries:
                    widget = self.entries[label]
                    if isinstance(widget, tk.StringVar):
                        widget.set(value)
                    elif isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)

            # If we found extracted metadata, reload it into the metadata panel
            if extracted_metadata:
                self.last_metadata_output = extracted_metadata  # Store for later use
                self.show_metadata_in_window(extracted_metadata)
            else:
                # Clear the metadata panel if no extracted metadata was found
                self.metadata_text.config(state="normal")
                self.metadata_text.delete("1.0", tk.END)
                self.metadata_text.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Could not load file: {e}")

    def select_and_load_template(self):
        template_files = glob.glob("*_ReadME_template.txt")
        if not template_files:
            return

        def load_template_and_close(fname):
            self.parse_readme_file(fname)
            popup.destroy()

        popup = tk.Toplevel(self.root)
        popup.title("Select a Metadata Template")
        popup.geometry("400x200")
        popup.transient(self.root)  # Keep on top of the main window
        popup.grab_set()            # Make it modal
        popup.focus_force()         # Force focus to the popup

        tk.Label(popup, text="Select a metadata template to load:", font=("Segoe UI", 10, "bold")).pack(pady=10)

        button_frame = tk.Frame(popup)
        button_frame.pack(pady=5, fill="both", expand=True)

        for fname in template_files:
            b = tk.Button(button_frame, text=fname, width=40, command=lambda f=fname: load_template_and_close(f))
            b.pack(pady=2)

        tk.Button(popup, text="Skip / Clear Form", command=popup.destroy).pack(pady=10)


    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help / Info")
        help_window.geometry("1000x650")  # Made taller to accommodate acknowledgements

        help_text = tk.Text(help_window, wrap="word", font=("Segoe UI", 10), width=80, height=35)
        help_text.pack(expand=True, fill="both", padx=10, pady=10)

        help_text.insert("1.0", "📄 ReMInD - Recommended Metadata Interface for Documentation Help\n\n", "title")
        help_text.insert("end", "This tool was created by Nicholas Condon (UQ) from IMB Microscopy in 2025.\n\n")
        help_text.insert("end", "The purpose of this tool is to help capture additional metadata to store with your RAW experimental data.\n\n")
        
        help_text.insert("end", "✒️ Entering Information \n", "subtitle")
        help_text.insert("end", "\t• Not every field needs to be filled in.\n")
        help_text.insert("end", "\t• If the tool can detect UQ-InstGateway then a list of available RDMs will be shown, if not connected it will warn you and allow free text input.\n")
        help_text.insert("end", "\t• Hover your cursor over the text box for more description for the field.\n")
        help_text.insert("end", "\t• Some fields contain drop down lists you can choose items from, if choosing 'other' provide the information in the notes box.\n")
        help_text.insert("end", "\t• The notes box can be filled in with as much detail as possible. You can use the 'Timestamp' button to generate a new line with the date and time.\n\n")
        
        help_text.insert("end", "🔬 Load Fields from Image File \n", "subtitle")
        help_text.insert("end", "\t• Click 'Load Fields from Image File' to automatically extract metadata from your image files.\n")
        help_text.insert("end", "\t• Supported formats: CZI (Zeiss), LIF (Leica), and ND2 (Nikon) files.\n")
        help_text.insert("end", "\t• The tool will automatically populate relevant fields with metadata from the image file including:\n")
        help_text.insert("end", "\t\t- Date and time of acquisition\n")
        help_text.insert("end", "\t\t- Microscope name and settings\n")
        help_text.insert("end", "\t\t- Objective lens information\n")
        help_text.insert("end", "\t\t- Channel information\n")
        help_text.insert("end", "\t\t- Imaging parameters (Z-stack, time series)\n")
        help_text.insert("end", "\t\t- Software and system information\n")
        help_text.insert("end", "\t• Extracted metadata will be displayed in the 'Extracted Image Metadata' section.\n")
        help_text.insert("end", "\t• You can review and edit the imported information before generating your ReadMe file.\n")
        help_text.insert("end", "\t• The raw metadata is also included when exporting as JSON or generating ReadMe files.\n\n")
        
        help_text.insert("end", "💾 Generate ReadMe.txt\n", "subtitle")
        help_text.insert("end", "\t• Once you have filled in the form to your liking you can save a ReadMe.txt file to any location (ideally within the data folder it's associated with).\n")
        help_text.insert("end", "\t• Save the ReadMe.txt file alongside the captured data.\n")
        help_text.insert("end", "\t• Use a filename that includes 'ReadMe' and the experiment name if needed.\n")
        help_text.insert("end", "\t• If you imported metadata from an image file, the raw metadata will be appended to the ReadMe file.\n\n")
        
        help_text.insert("end", "📂 Load ReadMe.txt\n", "subtitle")
        help_text.insert("end", "\t• The program has the ability to read a previously generated ReadMe file and repopulate the fields for quick editing/updating.\n")
        help_text.insert("end", "\t• This can be particularly useful when adding to the notes section.\n\n")
        
        help_text.insert("end", "📖 Templates \n", "subtitle")
        help_text.insert("end", "\t• The program automatically looks for any template files stored in the same location as the executable.\n")
        help_text.insert("end", "\t• Any template file must be saved as *_ReadMe_template.txt with something in place of the *.\n")
        help_text.insert("end", "\t• Multiple templates can be handled with a popup on startup allowing you to choose from a template or skip.\n\n")
        
        help_text.insert("end", "📁 Export as JSON\n", "subtitle")
        help_text.insert("end", "\t• Export all form data and extracted metadata as a structured JSON file.\n")
        help_text.insert("end", "\t• Useful for data processing, analysis workflows, or integration with other tools.\n")
        help_text.insert("end", "\t• Includes both form entries and raw extracted image metadata.\n\n")
        
        help_text.insert("end", "📌 Tips:\n", "subtitle")
        help_text.insert("end", "\t• Use a previously generated ReadMe.txt file as a template to pre-load certain fields such as RDM Info, Name, Sample information etc.\n")
        help_text.insert("end", "\t• If you're iterating on an experiment, consider labeling your files like ReadMe_exp1_v1.txt, v2, etc.\n")
        help_text.insert("end", "\t• Be descriptive: When entering experiment details, use full names, reagent IDs, microscope configurations, etc.\n")
        help_text.insert("end", "\t• Always load metadata from your original image files first, then supplement with additional information.\n")
        help_text.insert("end", "\t• Review imported metadata for accuracy - some fields may need manual correction or additional detail.\n")
        help_text.insert("end", "\t• Use the metadata extraction feature to ensure consistency across multiple experiments.\n\n")

        help_text.insert("end", "🙏 Acknowledgements\n", "subtitle")
        help_text.insert("end", "This tool uses several open-source libraries for metadata extraction:\n\n")
        help_text.insert("end", "\t• czifile by Christoph Gohlke - For reading Zeiss CZI files\n")
        help_text.insert("end", "\t\t  https://github.com/cgohlke/czifile\n\n")
        help_text.insert("end", "\t• readlif by Nimesh Khadka - For reading Leica LIF files\n")
        help_text.insert("end", "\t\t  https://github.com/nimne/readlif\n\n")
        help_text.insert("end", "\t• nd2 by Talley Lambert - For reading Nikon ND2 files\n")
        help_text.insert("end", "\t\t  https://github.com/tlambert03/nd2\n\n")
        help_text.insert("end", "\t• Python standard libraries: tkinter, json, datetime, os, glob\n\n")
        help_text.insert("end", "Special thanks to the open-source community for making microscopy metadata\n")
        help_text.insert("end", "accessible and standardized across different imaging platforms.\n\n")
        help_text.insert("end", "For support or feature requests, contact IMB Microscopy at The University of Queensland.")

        help_text.tag_configure("title", font=("Segoe UI", 12, "bold"))
        help_text.tag_configure("subtitle", font=("Segoe UI", 10, "bold"))
        help_text.config(state="disabled")


    def load_fields_from_image(self):
        filetypes = [
            ("Image files", "*.tif *.tiff *.czi *.lif *.nd2 *.jpg *.png *.bmp"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Select an image file to extract metadata",
            filetypes=filetypes
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        if ext == ".czi":
            try:
                metadata_output, _ = extract_metadata(path)

                # Map CZI metadata keys to ReMInD form fields
                field_map = {
                    "Experiment name": None,  # Do not auto-fill from file name
                    "Date and time": "Document Creation Date",
                    "Experimentor Name(s)": "Document User Name",
                    "Microscope name": "System Name",
                    "Objective": "Objective Model",
                    "Immersion": "Objective Medium",
                    "Imaging mode": "Acquisition Modes",
                    "Channel info": "Channel Names",
                    "Image format": None,
                    "Notes": None,
                }

                for remind_label, czi_key in field_map.items():
                    if czi_key is None:
                        if remind_label == "Image format":
                            widget = self.entries[remind_label]
                            if isinstance(widget, tk.StringVar):
                                widget.set(ext)
                            else:
                                widget.delete(0, tk.END)
                                widget.insert(0, ext)
                        elif remind_label == "Notes":
                            notes_widget = self.text_fields.get("Notes")
                            if notes_widget:
                                notes_widget.insert(tk.END, "\n[Imported from CZI]\n")
                        continue

                    value = metadata_output.get(czi_key, "")
                    # Special handling for Imaging mode (Acquisition Modes)
                    if remind_label == "Imaging mode":
                        if isinstance(value, list) and value:
                            value = str(value[0])  # Use only the first value
                        elif isinstance(value, list):
                            value = ""
                    elif isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    widget = self.entries.get(remind_label)
                    if widget is None:
                        continue
                    if isinstance(widget, tk.StringVar):
                        widget.set(value)
                    elif isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                    elif remind_label == "Notes" and remind_label in self.text_fields:
                        self.text_fields[remind_label].insert(tk.END, value)

                # If DataSourceTypeName is Confocal, set Imaging mode to Confocal
                if metadata_output.get("DataSourceTypeName", "").lower() == "confocal":
                    imaging_mode_widget = self.entries.get("Imaging mode")
                    if imaging_mode_widget:
                        if isinstance(imaging_mode_widget, tk.StringVar):
                            imaging_mode_widget.set("Confocal")
                        elif isinstance(imaging_mode_widget, tk.Entry):
                            imaging_mode_widget.delete(0, tk.END)
                            imaging_mode_widget.insert(0, "Confocal")

                self.show_metadata_in_window(metadata_output)
                self.last_metadata_output = metadata_output  # Store for later use

                messagebox.showinfo("Success", "Fields loaded from CZI metadata.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract CZI metadata:\n{e}")
        elif ext == ".lif":
            try:
                metadata_list = extract_lif_metadata(path)
                if not metadata_list:
                    messagebox.showerror("Error", "No images found in LIF file.")
                    return
                metadata_output = metadata_list[0]  # Use first image/series
                # Map LIF metadata keys to ReMInD form fields
                field_map = {
                    "Experiment name": None,
                    "Date and time": "Document Creation Date",
                    "Experimentor Name(s)": "Document User Name",
                    "Microscope name": "System Name",
                    "Objective": "Objective Model",
                    "Immersion": "Objective Medium",
                    "Imaging mode": "Acquisition Modes",
                    "Channel info": "Channel Names",
                    "Image format": None,
                    "Notes": None,
                }
                for remind_label, lif_key in field_map.items():
                    if lif_key is None:
                        if remind_label == "Image format":
                            widget = self.entries[remind_label]
                            if isinstance(widget, tk.StringVar):
                                widget.set(ext)
                            else:
                                widget.delete(0, tk.END)
                                widget.insert(0, ext)
                        elif remind_label == "Notes":
                            notes_widget = self.text_fields.get("Notes")
                            if notes_widget:
                                notes_widget.insert(tk.END, "\n[Imported from LIF]\n")
                        continue
                    value = metadata_output.get(lif_key, "")
                    if remind_label == "Imaging mode":
                        if isinstance(value, list) and value:
                            value = str(value[0])
                        elif isinstance(value, list):
                            value = ""
                    elif isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    widget = self.entries.get(remind_label)
                    if widget is None:
                        continue
                    if isinstance(widget, tk.StringVar):
                        widget.set(value)
                    elif isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                    elif remind_label == "Notes" and remind_label in self.text_fields:
                        self.text_fields[remind_label].insert(tk.END, value)

                self.show_metadata_in_window(metadata_output)
                self.last_metadata_output = metadata_output  # Store for later use

                messagebox.showinfo("Success", "Fields loaded from LIF metadata.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract LIF metadata:\n{e}")
        elif ext == ".nd2":
            try:
                # Extract ND2 metadata using your new functions
                metadata_output = extract_nd2_metadata(path)
                remind_fields = map_nd2_to_remind_fields(metadata_output)
                
                # Map ND2 metadata to ReMInD form fields
                for remind_label, value in remind_fields.items():
                    if not value or remind_label == "Notes":  # Skip empty values and Notes
                        continue
                        
                    widget = self.entries.get(remind_label)
                    if widget is None:
                        continue
                        
                    if isinstance(widget, tk.StringVar):
                        widget.set(value)
                    elif isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)

                # Special handling for Notes field to add import info only
                notes_widget = self.text_fields.get("Notes")
                if notes_widget:
                    notes_widget.insert(tk.END, "\n[Imported from ND2]\n")

                # Display the raw metadata in the metadata window
                self.show_metadata_in_window(metadata_output)
                self.last_metadata_output = metadata_output  # Store for later use

                messagebox.showinfo("Success", "Fields loaded from ND2 metadata.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract ND2 metadata:\n{e}")
                
        else:
            messagebox.showinfo("Not Supported", "Only CZI, LIF, and ND2 files are supported for metadata extraction at this time.")

    def show_metadata_in_window(self, metadata_dict):
        self.metadata_text.config(state="normal")
        self.metadata_text.delete("1.0", tk.END)
        for k, v in metadata_dict.items():
            if isinstance(v, list):
                v = ", ".join(str(i) for i in v)
            self.metadata_text.insert(tk.END, f"{k}: {v}\n")
        self.metadata_text.config(state="disabled")

    def toggle_dark_mode(self):
        dark_bg = "#222"
        dark_fg = "#eee"
        entry_bg = "#333"
        entry_fg = "#fff"
        highlight = "#444"

        style = ttk.Style()
        if not hasattr(self, "dark_mode") or not self.dark_mode:
            self.root.configure(bg=dark_bg)
            for widget in self.root.winfo_children():
                self._set_widget_dark(widget, dark_bg, dark_fg, entry_bg, entry_fg, highlight)
            # Use clam theme for better dark combobox support
            style.theme_use('clam')
            style.configure("TCombobox",
                            fieldbackground=entry_bg,
                            background=entry_bg,
                            foreground=entry_fg,
                            selectforeground=entry_fg,
                            selectbackground=entry_bg)
            self.dark_mode = True
        else:
            self.root.configure(bg="SystemButtonFace")
            for widget in self.root.winfo_children():
                self._set_widget_light(widget)
            style.theme_use('clam')
            style.configure("TCombobox",
                            fieldbackground="white",
                            background="white",
                            foreground="black",
                            selectforeground="black",
                            selectbackground="white")
            self.dark_mode = False

    def _set_widget_dark(self, widget, bg, fg, entry_bg, entry_fg, highlight):
        cls = widget.__class__.__name__
        if cls in ["Frame", "LabelFrame"]:
            widget.configure(bg=bg)
        elif cls == "Label":
            widget.configure(bg=bg, fg=fg)
        elif cls == "Entry":
            widget.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        elif cls == "Text":
            widget.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        elif cls == "Button":
            widget.configure(bg=highlight, fg=fg, activebackground=bg, activeforeground=fg)
        elif cls == "Toplevel":
            widget.configure(bg=bg)
        elif cls == "Scrollbar":
            widget.configure(bg=bg, troughcolor=highlight)
        # Do not try to configure ttk.Combobox here; it's handled by ttk.Style
        for child in widget.winfo_children():
            self._set_widget_dark(child, bg, fg, entry_bg, entry_fg, highlight)

    def _set_widget_light(self, widget):
        # Recursively reset to default colors
        cls = widget.__class__.__name__
        if cls in ["Frame", "LabelFrame", "Toplevel"]:
            widget.configure(bg="SystemButtonFace")
        elif cls == "Label":
            widget.configure(bg="SystemButtonFace", fg="black")
        elif cls == "Entry":
            widget.configure(bg="white", fg="black", insertbackground="black")
        elif cls == "Text":
            widget.configure(bg="white", fg="black", insertbackground="black")
        elif cls == "Button":
            widget.configure(bg="SystemButtonFace", fg="black", activebackground="SystemButtonFace", activeforeground="black")
        elif cls == "Scrollbar":
            widget.configure(bg="SystemButtonFace")
        # Recursively apply to children
        for child in widget.winfo_children():
            self._set_widget_light(child)

    def increase_font_size(self):
        self.base_font_size += 1
        self.app_font.configure(size=self.base_font_size)
        self.bold_font.configure(size=self.base_font_size)

    def decrease_font_size(self):
        if self.base_font_size > 6:
            self.base_font_size -= 1
            self.app_font.configure(size=self.base_font_size)
            self.bold_font.configure(size=self.base_font_size)

    def export_as_json(self):
        data = {}
        for label, _, _ in self.fields:
            if label in self.text_fields:
                value = self.text_fields[label].get("1.0", tk.END).strip()
                data[label] = value
            elif isinstance(self.entries[label], tk.StringVar):
                data[label] = self.entries[label].get()
            else:
                data[label] = self.entries[label].get()
            if label in self.extra_fields:
                data[f"{label} (Other)"] = self.extra_fields[label].get()

        # Add extracted metadata if available
        if hasattr(self, "last_metadata_output") and self.last_metadata_output:
            data["Extracted Image Metadata"] = self.last_metadata_output

        # Get experiment name for filename
        experiment_name = self.entries["Experiment name"].get().strip()
        if experiment_name:
            # Clean filename (remove invalid characters)
            clean_name = "".join(c for c in experiment_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            default_filename = f"{clean_name}_metadata.json"
        else:
            default_filename = "metadata.json"

        save_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 initialfile=default_filename,  # <-- Use dynamic filename
                                                 filetypes=[("JSON files", "*.json")],
                                                 title="Save as JSON")
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Success", "Metadata exported as JSON successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write JSON file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = REMBIGUI(root)
    root.mainloop()


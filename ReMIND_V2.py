# Version 2.0
# Made by Nicholas Condon (n.condon@uq.edu.au) from IMB Microscopy @ The University of Queensland
# May 2025

# The intention of this tool is to help users make readME.txt files associated with their experimental datasets for better data practices

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import os
import scyjava
import jpype
from tkinter import filedialog, messagebox
import json


# Add Bio-Formats JARs (downloads from SciJava Maven repo)
scyjava.config.add_repositories({'scijava.public': 'https://maven.scijava.org/content/groups/public'})
scyjava.config.add_endpoints([
    'ome:formats-gpl:7.3.0',  # Adjust version as needed
])


def get_bioformats_metadata(image_path):
    if not jpype.isJVMStarted():
        scyjava.start_jvm()
    ImageReader = scyjava.jimport('loci.formats.ImageReader')
    OMEXMLService = scyjava.jimport('loci.common.services.ServiceFactory').getInstance().getInstance(
        scyjava.jimport('loci.formats.services.OMEXMLService'))
    reader = ImageReader()
    omeMeta = OMEXMLService.createOMEXMLMetadata()
    reader.setMetadataStore(omeMeta)
    reader.setId(image_path)

    def safe_get(callable_, *args):
        try:
            return callable_(*args)
        except Exception:
            return ""

    def flatten_and_str(val):
        # Recursively flattens any nested lists/tuples and converts everything to string
        def _flatten(v):
            if isinstance(v, (list, tuple)):
                for item in v:
                    yield from _flatten(item)
            elif v is None:
                return
            else:
                yield str(v)
        return ", ".join(list(_flatten(val)))

    size_c = safe_get(reader.getSizeC) or 0

    metadata = {
        "Microscope name": flatten_and_str(safe_get(omeMeta.getInstrumentID, 0)) if safe_get(omeMeta.getInstrumentCount) > 0 else "",
        "Image format": flatten_and_str(safe_get(reader.getFormat)),
        "Channel info": f"{size_c} channel(s)",
        "Date and time": flatten_and_str(safe_get(omeMeta.getImageAcquisitionDate, 0)) if safe_get(omeMeta.getImageCount) > 0 else "",
        "Pixel count X": flatten_and_str(safe_get(reader.getSizeX)),
        "Pixel count Y": flatten_and_str(safe_get(reader.getSizeY)),
        "Pixel count Z": flatten_and_str(safe_get(reader.getSizeZ)),
        "Time series": flatten_and_str(safe_get(reader.getSizeT)),
        "Pixel size X (um)": flatten_and_str(safe_get(lambda: omeMeta.getPixelsPhysicalSizeX(0).value())) if safe_get(omeMeta.getPixelsPhysicalSizeX, 0) else "",
        "Pixel size Y (um)": flatten_and_str(safe_get(lambda: omeMeta.getPixelsPhysicalSizeY(0).value())) if safe_get(omeMeta.getPixelsPhysicalSizeY, 0) else "",
        "Pixel size Z (um)": flatten_and_str(safe_get(lambda: omeMeta.getPixelsPhysicalSizeZ(0).value())) if safe_get(omeMeta.getPixelsPhysicalSizeZ, 0) else "",
        "Objective": flatten_and_str(safe_get(omeMeta.getObjectiveID, 0, 0)) if safe_get(omeMeta.getObjectiveCount, 0) > 0 else "",
        "Objective Magnification": flatten_and_str(safe_get(omeMeta.getObjectiveNominalMagnification, 0, 0)) if safe_get(omeMeta.getObjectiveCount, 0) > 0 else "",
        "Objective NA": flatten_and_str(safe_get(omeMeta.getObjectiveLensNA, 0, 0)) if safe_get(omeMeta.getObjectiveCount, 0) > 0 else "",
        "Instrument Manufacturer": flatten_and_str(safe_get(omeMeta.getInstrumentManufacturer, 0)) if safe_get(omeMeta.getInstrumentCount) > 0 else "",
        "Instrument Model": flatten_and_str(safe_get(omeMeta.getInstrumentModel, 0)) if safe_get(omeMeta.getInstrumentCount) > 0 else "",
        "Channel Names": ", ".join([flatten_and_str(safe_get(omeMeta.getChannelName, 0, c)) for c in range(size_c)]),
        "Channel Excitation Wavelengths": ", ".join([flatten_and_str(safe_get(omeMeta.getChannelExcitationWavelength, 0, c)) for c in range(size_c)]),
        "Channel Emission Wavelengths": ", ".join([flatten_and_str(safe_get(omeMeta.getChannelEmissionWavelength, 0, c)) for c in range(size_c)]),
    }
    reader.close()
    return metadata


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
        self.root.title("ReMInD - Recommended Metadata Interface for Documentation")

        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)

        self.entries = {}
        self.extra_fields = {}
        self.text_fields = {}

        self.fields = [
            ("Experiment name", "", "Title of the experiment."),
            ("RDM Info", "", "RDM Project Name or storage location (e.g. Q1234)"),
            ("Date and time", "", "Date and time of acquisition."),
            ("Experimentor Name(s)", "", "Enter your full name."),
            ("Sample Information", "", "e.g. Sample ID, or cell line, animal strain"),
            ("Genetic Modifications", "", "e.g. eGFP- mCherry-y"),
            ("Antibody or probes", "", "e.g. Alexa488-Phalloidin, DAPI, Alexa647-GaM"),
            ("Fixation / Live Media", "", "Fixation method used, or details of live imaging reagents"),
            ("Sample mounting condition", "", "35mm Dish, #1.5 coverslip, chamber slide"),
            ("Microscope name", "", "e.g. Confocal 5"),
            ("Objective", ["1x", "4x", "5x", "10x", "20x", "25x", "40x", "60x", "63x", "100x", "Other"], "Objective lens details. e.g. Plan Apochromat 63x 1.4NA"),
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
        self.load_template()

    def build_form(self):
        self.row_counter = 0
        for label, options, tooltip_text in self.fields:
            tk.Label(self.root, text=label).grid(row=self.row_counter, column=0, sticky="e")

            if isinstance(options, list):
                var = tk.StringVar()
                combo = ttk.Combobox(self.root, textvariable=var, values=options, state="readonly")
                combo.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")
                self.entries[label] = var
                ToolTip(combo, tooltip_text)

                def handle_other(event, label=label):
                    if var.get() == "Other":
                        if label not in self.extra_fields:
                            other_row = self.row_counter + len(self.extra_fields) + 1
                            entry = tk.Entry(self.root)
                            entry.grid(row=other_row, column=1, padx=5, pady=2, sticky="ew")
                            tk.Label(self.root, text=f"{label} (Other)").grid(row=other_row, column=0, sticky="e")
                            self.extra_fields[label] = entry
                            ToolTip(entry, f"Specify 'Other' for {label.lower()}")
                    else:
                        if label in self.extra_fields:
                            self.extra_fields[label].destroy()
                            del self.extra_fields[label]

                combo.bind("<<ComboboxSelected>>", handle_other)

            elif label == "Notes":
                frame = tk.Frame(self.root)
                frame.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")
                text_box = tk.Text(frame, height=10, width=50)
                text_box.pack(side="left", fill="both", expand=True)
                self.entries[label] = text_box
                self.text_fields[label] = text_box
                ToolTip(text_box, tooltip_text)

                def insert_timestamp():
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    text_box.insert(tk.END, f"\n[{now}] ")

                timestamp_btn = tk.Button(frame, text="Timestamp", command=insert_timestamp)
                timestamp_btn.pack(side="right", padx=5, pady=5)
                ToolTip(timestamp_btn, "Insert timestamp into notes")

            else:
                entry = tk.Entry(self.root)
                entry.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")
                self.entries[label] = entry
                ToolTip(entry, tooltip_text)

            self.row_counter += 1

        button_frame = tk.Frame(self.root)
        button_frame.grid(row=self.row_counter + 1, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Generate ReadMe.txt", command=self.generate_readme).pack(side="left", padx=5)
        tk.Button(button_frame, text="Load ReadMe.txt", command=self.load_existing).pack(side="left", padx=5)
        tk.Button(button_frame, text="Help", command=self.show_help).pack(side="left", padx=5)
        tk.Button(button_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)
        tk.Button(button_frame, text="Autofill from Bio-Formats", command=self.autofill_from_bioformats).pack(side="left", padx=5)

    def generate_readme(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 initialfile="ReadME.txt",
                                                 filetypes=[("Text files", "*.txt")],
                                                 title="Save ReadMe.txt as")
        if not save_path:
            return
        if os.path.exists(save_path):
            if not messagebox.askyesno("Overwrite?", "This file already exists. Overwrite?"):
                return

        lines = []
        for label, _, _ in self.fields:
            if label in self.text_fields:
                value = self.text_fields[label].get("1.0", tk.END).strip()
                lines.append(f"{label}:\n---\n{value}\n---")
            elif isinstance(self.entries[label], tk.StringVar):
                value = self.entries[label].get()
                lines.append(f"{label}: {value}")
            else:
                value = self.entries[label].get()
                lines.append(f"{label}: {value}")
            if label in self.extra_fields:
                lines.append(f"{label} (Other): {self.extra_fields[label].get()}")

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
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            idx = 0
            while idx < len(lines):
                line = lines[idx].strip()
                if not line:
                    idx += 1
                    continue

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
                    if ": " not in line:
                        idx += 1
                        continue
                    label, value = line.split(": ", 1)
                    label = label.strip()
                    value = value.strip()
                    idx += 1

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

        except Exception as e:
            messagebox.showerror("Error", f"Could not load file: {e}")

    def load_template(self):
        if os.path.exists("ReadMe_template.txt"):
            try:
                with open("ReadMe_template.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()

                idx = 0
                while idx < len(lines):
                    line = lines[idx].strip()
                    if not line:
                        idx += 1
                        continue

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
                        if ": " not in line:
                            idx += 1
                            continue
                        label, value = line.split(": ", 1)
                        label = label.strip()
                        value = value.strip()
                        idx += 1

                    if label in self.text_fields:
                        self.text_fields[label].delete("1.0", tk.END)
                        self.text_fields[label].insert("1.0", value)
                    elif label in self.entries:
                        widget = self.entries[label]
                        if isinstance(widget, tk.StringVar):
                            widget.set(value)
                        elif isinstance(widget, tk.Entry):
                            widget.insert(0, value)
            except Exception:
                pass

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help / Info")
        help_window.geometry("1000x400")

        help_text = tk.Text(help_window, wrap="word", font=("Segoe UI", 10), width=80, height=25)
        help_text.pack(expand=True, fill="both", padx=10, pady=10)

        help_text.insert("1.0", "📄 ReMInD - Recommended Metadata Interface for Documentation Help\n\n", "title")
        help_text.insert("end", "This tool was created by Nicholas Condon (UQ) in from IMB Microscopy in 2025.\n\n")
        help_text.insert("end", "The purpose of this tool is to help capture additional metadata to store with your RAW experimental data.\n\n")
        help_text.insert("end", "✒️ Entering information \n", "subtitle")
        help_text.insert("end", "\t Not every field needs to be filled in.\n")
        help_text.insert("end", "\t Hover your cursor over the text box for more description for the field.\n")
        help_text.insert("end", "\t Some fields contain drop down lists you can choose items from, if choosing 'other' provide the information in the notes box.\n")
        help_text.insert("end", "\t The notes box can be filled in with as much detail as possible. You can use the 'Timestamp' button to generate a new line with the date and time.\n\n")
        help_text.insert("end", "💾 Generate ReadME.txt\n", "subtitle")
        help_text.insert("end", "\t Once you have filled in the form to your liking you can save a ReadME.txt file to any location (ideally within the data folder it's associated with.\n")
        help_text.insert("end", "\t Save the ReadME.txt file alongside the captured data.\n")
        help_text.insert("end", "\t Use a filename that includes 'ReadME' and the experiment name if needed.\n\n")
        help_text.insert("end", "📂 Load ReadME.txt\n", "subtitle")
        help_text.insert("end", "\t The program has the ability to read a prevously generated ReadME file and repopulate the fields for quick editing/updating.\n")
        help_text.insert("end", "\t This can be particularly useful when adding to the notes section.\n")
        help_text.insert("end", "📌 Tips:\n", "subtitle")
        help_text.insert("end", "\t Use a previously generated ReadME.txt file as a template to pre-load certain fields such as RDM Info, Name, Sample information etc. \n")
        help_text.insert("end", "\t If you're iterating on an experiment, consider labeling your files like ReadMe_exp1_v1.txt, v2, etc \n")
        help_text.insert("end", "\t Be descriptive: When entering experiment details, use full names, reagent IDs, microscope configurations, etc.\n")


        help_text.tag_configure("title", font=("Segoe UI", 12, "bold"))
        help_text.tag_configure("subtitle", font=("Segoe UI", 10, "bold"))
        help_text.config(state="disabled")

    # Add this method to your REMBIGUI class:
    def autofill_from_bioformats(self):
        file_path = filedialog.askopenfilename(title="Select image file")
        if not file_path:
            return
        try:
            metadata = get_bioformats_metadata(file_path)
            # DEBUG: Output metadata to a file for inspection
            with open("bioformats_metadata_debug.json", "w", encoding="utf-8") as debug_file:
                json.dump(metadata, debug_file, indent=2, ensure_ascii=False)
            for field, value in metadata.items():
                entry = self.entries.get(field)
                if entry:
                    if isinstance(entry, tk.StringVar):
                        entry.set(str(value))
                    elif isinstance(entry, tk.Entry):
                        entry.delete(0, tk.END)
                        entry.insert(0, str(value))
            messagebox.showinfo("Success", "Metadata imported from Bio-Formats.")
        except Exception as e:
            messagebox.showerror("Error", f"Bio-Formats import failed:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = REMBIGUI(root)
    root.mainloop()

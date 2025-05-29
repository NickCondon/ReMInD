import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import os
import glob

APP_VERSION = "ReMInD v2.19"
APP_AUTHOR = "Nicholas Condon, IMB Microscopy, The University of Queensland, Brisbane Australia"
APP_DATE = "May 2025"

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
        self.root.title("IMB Experiment Metadata Capture Tool - " + APP_VERSION)

        self.entries = {}
        self.extra_fields = {}
        self.text_fields = {}

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
        network_path = r"\\UQ-ADSTL02.uq.edu.au\UQ-Inst-Gateway2"  # Adjust if needed
        try:
            dirs = [name for name in os.listdir(network_path) if os.path.isdir(os.path.join(network_path, name))]
            return True, dirs
        except Exception as e:
            print(f"Could not access the network location: {e}")
            return False, []

    def build_form(self):
        self.row_counter = 0
        for label, options, tooltip_text in self.fields:
            tk.Label(self.root, text=label).grid(row=self.row_counter, column=0, sticky="e", padx=5, pady=2)

            if label == "RDM Info":
                self.rdm_connected, self.rdm_dirs = self.check_rdm_connectivity()

                # Create a frame for both indicator and input side-by-side
                rdm_frame = tk.Frame(self.root)
                rdm_frame.grid(row=self.row_counter, column=1, sticky="ew", padx=5, pady=2)

                # Indicator canvas inside rdm_frame
                indicator = tk.Canvas(rdm_frame, width=15, height=15, highlightthickness=0)
                color = "green" if self.rdm_connected else "red"
                indicator.create_oval(2, 2, 13, 13, fill=color)
                indicator.pack(side="left", padx=(0,5))

                # Input widget (Combobox or Entry)
                self.rdm_var = tk.StringVar()
                if self.rdm_connected:
                    combo = ttk.Combobox(rdm_frame, textvariable=self.rdm_var, values=self.rdm_dirs)
                    combo.pack(side="left", fill="x", expand=True)
                else:
                    entry = tk.Entry(rdm_frame, textvariable=self.rdm_var)
                    entry.pack(side="left", fill="x", expand=True)

                self.entries[label] = self.rdm_var
                ToolTip(rdm_frame, tooltip_text)

            elif isinstance(options, list):
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

            elif label == "Date and time":
                frame = tk.Frame(self.root)
                frame.grid(row=self.row_counter, column=1, padx=5, pady=2, sticky="ew")

                date_entry = tk.Entry(frame)
                date_entry.pack(side="left", fill="x", expand=True)
                self.entries[label] = date_entry
                ToolTip(date_entry, tooltip_text)

                def insert_datetime(entry_widget=date_entry):
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, now)

                timestamp_btn = tk.Button(frame, text="Now", command=insert_datetime)
                timestamp_btn.pack(side="right", padx=5)
                ToolTip(timestamp_btn, "Insert current date and time")

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
        tk.Button(button_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=5)
        tk.Button(button_frame, text="Help", command=self.show_help).pack(side="left", padx=5)
        tk.Button(button_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)

        version_label = tk.Label(self.root, text=f"{APP_VERSION}  —  {APP_DATE}", fg="gray")
        version_label.grid(row=self.row_counter + 2, column=0, columnspan=2, pady=(0, 5))

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

    def parse_readme_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            idx = 0
            while idx < len(lines):
                line = lines[idx].strip()
                if line.startswith("#") or not line:
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
        help_window.geometry("1000x500")

        help_text = tk.Text(help_window, wrap="word", font=("Segoe UI", 10), width=80, height=25)
        help_text.pack(expand=True, fill="both", padx=10, pady=10)

        help_text.insert("1.0", "📄 ReMInD - Recommended Metadata Interface for Documentation Help\n\n", "title")
        help_text.insert("end", "This tool was created by Nicholas Condon (UQ) in from IMB Microscopy in 2025.\n\n")
        help_text.insert("end", "The purpose of this tool is to help capture additional metadata to store with your RAW experimental data.\n\n")
        help_text.insert("end", "✒️ Entering information \n", "subtitle")
        help_text.insert("end", "\t Not every field needs to be filled in.\n")
        help_text.insert("end", "\t If the tool can detect UQ-InstGateway then a list of available RDMs will be shown, if not connected it will warn you and allow free text input\n")
        help_text.insert("end", "\t Hover your cursor over the text box for more description for the field.\n")
        help_text.insert("end", "\t Some fields contain drop down lists you can choose items from, if choosing 'other' provide the information in the notes box.\n")
        help_text.insert("end", "\t The notes box can be filled in with as much detail as possible. You can use the 'Timestamp' button to generate a new line with the date and time.\n\n")
        help_text.insert("end", "💾 Generate ReadME.txt\n", "subtitle")
        help_text.insert("end", "\t Once you have filled in the form to your liking you can save a ReadME.txt file to any location (ideally within the data folder it's associated with.\n")
        help_text.insert("end", "\t Save the ReadME.txt file alongside the captured data.\n")
        help_text.insert("end", "\t Use a filename that includes 'ReadME' and the experiment name if needed.\n\n")
        help_text.insert("end", "📂 Load ReadME.txt\n", "subtitle")
        help_text.insert("end", "\t The program has the ability to read a prevously generated ReadME file and repopulate the fields for quick editing/updating.\n")
        help_text.insert("end", "\t This can be particularly useful when adding to the notes section.\n\n")
        help_text.insert("end", "📖 Templates \n", "subtitle")
        help_text.insert("end", "\t The program automatically looks for any template files stored in the same location as the executable.\n")
        help_text.insert("end", "\t Any template file must be saved as *ReadME_template.txt with something inplace of the *.\n")
        help_text.insert("end", "\t Multiple templates can be handled with a popup on startup allowing you to choose from a template or skip.\n\n")
        help_text.insert("end", "📌 Tips:\n", "subtitle")
        help_text.insert("end", "\t Use a previously generated ReadME.txt file as a template to pre-load certain fields such as RDM Info, Name, Sample information etc. \n")
        help_text.insert("end", "\t If you're iterating on an experiment, consider labeling your files like ReadMe_exp1_v1.txt, v2, etc \n")
        help_text.insert("end", "\t Be descriptive: When entering experiment details, use full names, reagent IDs, microscope configurations, etc.\n")


        help_text.tag_configure("title", font=("Segoe UI", 12, "bold"))
        help_text.tag_configure("subtitle", font=("Segoe UI", 10, "bold"))
        help_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = REMBIGUI(root)
    root.mainloop()

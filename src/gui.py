
"""
GUI Interface
"""

import tkinter as tk

from tkinter import font
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from utils.utils import load_templates
from utils.utils import validate
from utils.utils import normalize_lookback
from utils.query_builder import build_query

class QueryGui:
    TIME_RANGES = ["5 MINUTES", "10 MINUTES", "30 MINUTES", "1 HOUR", "3 HOURS", "12 HOURS", "1 DAY"] 

    def __init__(self, root: tk.Tk):

        """
        Initialization of UI
        """
        self.root = root
        self.root.title("ThreatQueryX - Multi-Platform Threat Hunting Query Builder")
        self.root.minsize(500,400) # Optional minimum size
        self.root.resizable(False, False)

        self.platforms = ["qradar", "defender", "elastic"]
        self.platform = "qradar"
        self.templates = {}
        self.fields = {}

        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.update_field_visibility()

    def create_widgets(self):

        """
        Create and layout all necessary widgets with consistent styling
        """
        # === Platform Selector ===
        ttk.Label(self.frame, text="Platform:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.platform_var = tk.StringVar(value=self.platform)

        self.platform_menu = ttk.Combobox(
            self.frame,
            textvariable=self.platform_var,
            state="readonly",
            values=[p.upper() for p in self.platforms]
        )

        self.platform_menu.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.platform_menu.bind("<<ComboboxSelected>>", self.on_platform_change)

        # === Template Selector ===
        ttk.Label(self.frame, text="Template:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.template_var = tk.StringVar()
        self.template_menu = ttk.Combobox(self.frame, textvariable=self.template_var, state="readonly")
        self.template_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.template_menu.bind("<<ComboboxSelected>>", self.render_fields)

        # === Parameters Frame ===
        self.inputs_frame = ttk.LabelFrame(self.frame, text="Parameters")

        # Configure two columns: labels and entry widgets
        self.inputs_frame.columnconfigure(0, weight=1)
        self.inputs_frame.columnconfigure(1, weight=2)
        
        # Init empty lists for field tracking
        self.param_rows = []
        self.fields = {}

        # === Time Range ===
        ttk.Label(self.frame, text="Time Range:").grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

        time_frame = ttk.Frame(self.frame)
        time_frame.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)

        self.lookback_var = tk.StringVar(value=self.TIME_RANGES[1])
        self.time_entry = ttk.Entry(time_frame, textvariable=self.lookback_var, width=15)
        self.time_entry.pack(side="left")

        self.btn_time_prev = ttk.Button(time_frame, text="❮", width=2, command=lambda: self.change_time_range(-1))
        self.btn_time_prev.pack(side="left", padx=2)

        self.btn_time_next = ttk.Button(time_frame, text="❯", width=2, command=lambda: self.change_time_range(1))
        self.btn_time_next.pack(side="left", padx=2)

        # Defender button for post_pipeline
        self.include_post_pipeline_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
                self.frame, 
                text="Include summarisation",
                variable=self.include_post_pipeline_var
                )

        # === Generate Button ===
        generate_btn = ttk.Button(self.frame, text="Generate Query", command=self.generate)
        generate_btn.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew", padx=5)

        # === Output Text Box ===
        self.output_text = ScrolledText(self.frame, height=10, wrap=tk.WORD)
        self.output_text.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # === Copy Button ===
        copy_btn = ttk.Button(self.frame, text="Copy to Clipboard", command=self.copy)
        copy_btn.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # === Separator ===
        separator = ttk.Separator(self.frame, orient="horizontal")
        separator.grid(row=8, column=0, columnspan=2, sticky="nsew", pady=(10, 5))

        # === Info Label ===
        self.platform_info_label = ttk.Label(self.frame, text="")
        self.platform_info_label.grid(row=9, column=0, columnspan=2, sticky="nsew", pady=5, padx=5)
        self.platform_info_label.config(anchor="center", justify="center")

        # === Copyright Label ===
        self.copyright_label = ttk.Label(
            self.frame, text="© 2025 olofmagn", font=("Segoe UI", 8, "italic"), foreground="gray50"
        )
        self.copyright_label.grid(row=10, column=2, sticky="w", pady=(0, 10), padx=5)
        
        # === Load templates initially ===
        self.load_templates_for_platform(self.platform)

    def get_platform_info_text(self) -> str:

        """
        Get the current platform in use and returns a str of the SIEM in use.
        """
        platform = self.platform_var.get().lower()

        match platform:
            case "qradar":
                return "Using QRadar AQL query mode."

            case "elastic":
                return "Using Elastic Search query mode."

            case "defender":
                return "Using Microsoft Defender query mode."

            case _:
                return "Using unknown platform."

    def update_field_visibility(self) -> None:

        """
        Update field visiblity info label for all platforms
        """
        self.platform_info_label.config(text=self.get_platform_info_text())


        if self.platform == "defender":
            self.checkbox.grid(row=4, column=0, columnspan=2,padx=5, pady=5, sticky="nsew")
        else:
            self.checkbox.grid_forget()  # hide checkbox

    def on_platform_change(self, event: tk.Event = None) -> None:

        """
        Used to detect platform change so templates gets correctly loaded
        """
        plat = self.platform_var.get().lower()
        if plat != self.platform:
            self.platform = plat
            self.load_templates_for_platform(plat)

        self.update_field_visibility()

    def load_templates_for_platform(self, platform: str) -> None: 

        """
        Loads templates for a given platform
        """
        try:
            self.templates = load_templates(platform)
        except Exception as e:
            messagebox.showerror("Error loading templates", str(e))
            self.templates = {}

        self.template_var.set("")
        self.template_menu["values"] = list(self.templates.keys())
        self.clear_fields()

    def clear_fields(self) -> None:

        """
        Destroy all parameter widgets and clear state.
        """
        for widget in self.inputs_frame.winfo_children():
            widget.destroy()

        self.param_rows.clear()  # clear stored refs
        self.fields.clear()
        self.output_text.delete("1.0", tk.END)


    def render_fields(self, event=None) -> None:

        """
        Renders fields based on events
        """
        self.clear_fields()

        name = self.template_var.get()
        if not name or name not in self.templates:
            return 0

        template = self.templates[name]

        optional_fields = template.get("optional_fields", {})
        if optional_fields:
            self.inputs_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=10)
        else:
            self.inputs_frame.grid_remove()

        for i, (field, meta) in enumerate(optional_fields.items()):
            label_text = field
            help_text = ""

            if isinstance(meta, dict):
                help_text = meta.get("help", "")

            if help_text:
                label_text += f" ({help_text})"

            label = ttk.Label(self.inputs_frame, text=label_text + ":")
            entry_var = tk.StringVar()
            entry = ttk.Entry(self.inputs_frame, textvariable=entry_var)

            label.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)

            self.param_rows.append((label, entry, entry_var))

            self.fields[field] = (
                entry_var,
                meta.get("validation") if isinstance(meta, dict) else None
            )

        # Add spacer row after all input rows
        ttk.Label(self.inputs_frame, text="").grid(
            row=len(optional_fields), column=0, columnspan=2, pady=(5, 0)
        )


    def generate(self) -> None:

        """
        Builds an query
        """
        template_name = self.template_var.get()

        if not template_name:
            messagebox.showerror("Error", "Choose a template.")
            return 0

        template = self.templates[template_name]
        lookback = self.lookback_var.get()
        duration = normalize_lookback(lookback, self.platform)

        inputs = {}
        for field, (var, validation_type) in self.fields.items():
            value = var.get().strip()

            if value:
                valid, msg = validate(value, validation_type)

                if not valid:
                    messagebox.showerror("Invalid input", f"{field}: {msg}")
                    return 0

                inputs[field] = value
        
        if self.platform == "defender":
            include_post = self.include_post_pipeline_var.get()
        else:
            include_post = False

        try:
            query = build_query(template, inputs, duration, self.platform, include_post)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, query)
        except Exception as e:
            messagebox.showerror("Build Error", str(e))

    def copy(self) -> None:

        """
        Copy query to clipboard
        """
        query = self.output_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(query)
        messagebox.showinfo("Copied", "Query copied to clipboard!")

    def change_time_range(self, direction: int) -> None:

        """
        Change time range based on the direction.
        """
        current = self.lookback_var.get()

        if current in self.TIME_RANGES:
            idx = self.TIME_RANGES.index(current)
            new_idx = (idx + direction) % len(self.TIME_RANGES)
            self.lookback_var.set(self.TIME_RANGES[new_idx])

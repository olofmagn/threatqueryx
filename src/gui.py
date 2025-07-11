
"""
GUI Interface
"""

import re
import tkinter as tk

from typing import List, Optional

from tkinter import font
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import StringVar

from utils.configuration import load_templates
from utils.configuration import validate
from utils.configuration import normalize_lookback
from utils.generate_queries import build_query

class QueryGui:
    def __init__(self, root: tk.Tk) -> None:
        """
        Internal/external time ranges
        """

        self.INTERNAL_TIME_RANGES = ["5m", "10m", "30m", "1h", "3h", "12h", "1d"]
        self.DISPLAY_TIME_RANGES = ["5 MINUTES", "10 MINUTES", "30 MINUTES", "1 HOUR", "3 HOURS", "12 HOURS", "1 DAY"]

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

        self._create_widgets()
        self._update_field_visibility()

        # Mapping internal <-> display
        self.internal_to_display = dict(zip(self.INTERNAL_TIME_RANGES, self.DISPLAY_TIME_RANGES))
        self.display_to_internal = dict(zip(self.DISPLAY_TIME_RANGES, self.INTERNAL_TIME_RANGES))

    def _create_widgets(self) -> None:

        """
        Create and layout all necessary widgets with consistent styling
        """
        # === Platform Selector ===
        ttk.Label(self.frame, text="Platform:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.platform_var = tk.StringVar(value=self.platform)

        self.platform_menu = ttk.Combobox(
            self.frame,
            textvariable=self.platform_var,
            values=[p for p in self.platforms],
            state = "readonly"
        )

        self.platform_menu.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.platform_menu.bind("<<ComboboxSelected>>", self._on_platform_change)

        # === Template Selector ===
        ttk.Label(self.frame, text="Template:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.template_var = tk.StringVar()
        self.autocomplete_entry = ttk.Combobox(self.frame, textvariable=self.template_var)
        self.autocomplete_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.autocomplete_entry.bind("<<ComboboxSelected>>", self._render_fields)

        # Setup autocomplete
        self._setup_template_autocomplete()

        # === Parameters Frame ===
        self.inputs_frame = ttk.LabelFrame(self.frame, text="Parameters")

        # Configure two columns: labels and entry widgets
        self.inputs_frame.columnconfigure(0, weight=1)
        self.inputs_frame.columnconfigure(1, weight=2)
        
        # Init empty lists for field tracking
        self.param_rows = []
        self.fields = {}

        # === Time Range ===
        ttk.Label(self.frame, text="Time Range:").grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

        time_frame = ttk.Frame(self.frame)
        time_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)

        self.lookback_var = tk.StringVar(value=self.DISPLAY_TIME_RANGES[1])
        self.time_entry = ttk.Entry(time_frame, textvariable=self.lookback_var, width=15)
        self.time_entry.pack(side="left")

        self.btn_time_prev = ttk.Button(time_frame, text="❮", width=2, command=lambda: self._change_time_range(-1))
        self.btn_time_prev.pack(side="left", padx=2)

        self.btn_time_next = ttk.Button(time_frame, text="❯", width=2, command=lambda: self._change_time_range(1))
        self.btn_time_next.pack(side="left", padx=2)

        # Defender button for post_pipeline
        self.include_post_pipeline_var = tk.BooleanVar(value=False)

        self.checkbox = tk.Checkbutton(
                self.frame, 
                text="Include summarisation",
                variable=self.include_post_pipeline_var
                )

        # === Generate Button ===
        btn = ttk.Button(self.frame, text="Generate Query", command=self.generate)
        btn.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew", padx=5)

        # === Output Text Box ===
        self.output_text = ScrolledText(self.frame, height=10, wrap=tk.WORD)
        self.output_text.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # === Copy Button ===
        copy_btn = ttk.Button(self.frame, text="Copy to Clipboard", command=self._copy)
        copy_btn.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # === Separator ===
        separator = ttk.Separator(self.frame, orient="horizontal")
        separator.grid(row=9, column=0, columnspan=2, sticky="nsew", pady=(10, 5))

        # === Info Label ===
        self.platform_info_label = ttk.Label(self.frame, text="")
        self.platform_info_label.grid(row=10, column=0, columnspan=2, sticky="nsew", pady=5, padx=5)
        self.platform_info_label.config(anchor="center", justify="center")

        # === Copyright Label ===
        self.copyright_label = ttk.Label(
            self.frame, text="© 2025 olofmagn", font=("Segoe UI", 8, "italic"), foreground="gray50"
        )

        self.copyright_label.grid(row=13, column=2, sticky="e", pady=(0, 10), padx=5)
        
        # === Load templates initially ===
        self._load_templates_for_platform(self.platform)

    def _get_platform_info_text(self) -> str:

        """
        Get the current platform in use and returns a str of the SIEM in use.
        """
        platform = self.platform_var.get()

        match platform:
            case "qradar":
                return "Using QRadar AQL query mode."

            case "elastic":
                return "Using Elastic Search query mode."

            case "defender":
                return "Using Microsoft Defender query mode."

            case _:
                return None

    def _update_field_visibility(self) -> None:

        """
        Update field visiblity info label for all platforms
        """
        self.platform_info_label.config(text=self._get_platform_info_text())


        if self.platform.lower() == "defender":
            self.checkbox.grid(row=5, column=0, columnspan=2,padx=5, pady=5, sticky="nsew")

        else:
            self.checkbox.grid_forget()  # hide checkbox

    def _on_platform_change(self, event: tk.Event = None) -> None:

        """
        Used to detect platform change so templates gets correctly loaded
        """
        plat = self.platform_var.get()
        if plat != self.platform:
            self.platform = plat
            self._load_templates_for_platform(plat)

        self._update_field_visibility()

    def _load_templates_for_platform(self, platform: str) -> None: 

        """
        Loads templates for a given platform
        """
        try:
            self.templates = load_templates(platform)
        except Exception as e:
            messagebox.showerror("Error loading templates", str(e))
            self.templates = {}

        self.template_var.set("")
        self.autocomplete_entry["values"] = list(self.templates.keys())
        self._clear_fields()

    def _clear_fields(self) -> None:

        """
        Destroy all parameter widgets and clear state.
        """
        for widget in self.inputs_frame.winfo_children():
            widget.destroy()

        self.param_rows.clear()  # clear stored refs
        self.fields.clear()
        self.output_text.delete("1.0", tk.END)

    def _render_fields(self, event: Optional[tk.Event] = None) -> None:

        """
        Renders fields based on events
        """
        self._clear_fields()

        name = self.template_var.get()
        template = self.templates[name]
        optional_fields = template.get("optional_fields", {})

        if optional_fields:
            self.inputs_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=10)

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

        # Normalize
        template_name = self.template_var.get().lower()
        platform = self.platform_var.get().lower()

        lookback = self.lookback_var.get()

        # Not possible but if use not readonly this solves
        if not platform or platform not in self.platforms:
            messagebox.showerror("Error", "Invalid platform choice")
            return 0

        if not template_name or template_name not in self.templates:
            messagebox.showerror("Error", "Invalid template choice.")
            return 0

        template = self.templates[template_name]
        duration = normalize_lookback(lookback, self.platform)

        if duration is None:
            messagebox.showerror("Error", "Invalid time range")
            return 0

        inputs = {}
        for field, (var, validation_type) in self.fields.items():
            value = var.get().strip()

            if value:
                valid, msg = validate(value, validation_type)

                if not valid:
                    messagebox.showerror("Invalid input", f"{field}: {msg}")
                    return 0

                inputs[field] = value

        include_post = self.include_post_pipeline_var.get() if platform == "defender" else False

        try:
            query = build_query(template, inputs, duration, platform, include_post)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, query)
        except Exception as e:
            messagebox.showerror("Build Error", str(e))

    def _copy(self) -> None:

        """
        Copy query to clipboard
        """
        query = self.output_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(query)
        messagebox.showinfo("Copied", "Query copied to clipboard!")

    def _change_time_range(self, direction: int) -> None:
        current = self.lookback_var.get().strip().upper()

        if current in self.display_to_internal:
            internal = self.display_to_internal[current]

        else:
            internal = current.lower()

            if internal in self.internal_to_display:
                pass

            else:
                internal = self.INTERNAL_TIME_RANGES[0]

        # Find index in internal list for cycling
        idx = self.INTERNAL_TIME_RANGES.index(internal)
        new_idx = (idx + direction) % len(self.INTERNAL_TIME_RANGES)

        # Update display label in entry
        new_display = self.internal_to_display[self.INTERNAL_TIME_RANGES[new_idx]]
        self.lookback_var.set(new_display)


    def _setup_template_autocomplete(self) -> None:
        self.listbox = None

        def _on_select_commit(event: Optional[tk.Event] = None) -> None:

            if self.listbox and self.listbox.curselection():

                try:
                    index= self.listbox.curselection()[0]
                    selected = self.listbox.get(index)
                    self.template_var.set(selected)
                    self._render_fields()  
                except IndexError:
                    pass

            if self.listbox:
                self.listbox.destroy()
                self.listbox = None

            # Refocus entry for further typing
            self.autocomplete_entry.focus_set()
            self.autocomplete_entry.icursor(tk.END)
            return "break"

        def _update_suggestions(event: Optional[tk.Event] = None) -> None:
            typed = self.template_var.get().lower()
            matches = self._fuzzy_match(typed, list(self.templates.keys()))

            if self.listbox:
                self.listbox.destroy()
                self.listbox = None

            if not typed or not matches:
                return

            self.listbox = tk.Listbox(self.frame, height=min(5, len(matches)))
            self.listbox.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

            for match in matches:
                self.listbox.insert(tk.END, match)

            self.listbox.select_set(0)
            self.listbox.activate(0)
            
            self.listbox.bind("<ButtonRelease-1>", _on_select_commit)
            self.listbox.bind("<Return>", on_return)

        def _on_listbox_nav(event: Optional[tk.Event] = None) -> None:
            if not self.listbox:
                return

            curr = self.listbox.curselection()
            total = self.listbox.size()

            if not total:
                return "break"

            current_index = curr[0] if curr else -1

            direction = {"Up": -1, "Down": -1}.get(event.keysym)

            if direction is None:
                return 0

            next_index = (current_index + direction) % total

            self.listbox.select_clear(0, tk.END)
            self.listbox.select_set(next_index)
            self.listbox.activate(next_index)
            self.listbox.focus_set()
            return "break"

        def _on_return(event: Optional[tk.Event] = None) -> str: 
            return _on_select_commit()

        self.autocomplete_entry.bind("<Return>", _on_return)
        self.autocomplete_entry.bind("<KeyRelease>", _update_suggestions)
        self.autocomplete_entry.bind("<Down>", _on_listbox_nav)
        self.autocomplete_entry.bind("<Up>", _on_listbox_nav)
        self.autocomplete_entry.bind("<FocusIn>", _update_suggestions)

    def _fuzzy_match(self, input_text: str, options: List[str]) -> List[str]:

        """
        Args:
        - input_text (str): An input string.
        - options (List[str]) : A list of possible options.

        Returns:
        - A list of options that contain all characters in order from input_text.

        """
        return [opt for opt in options if self._is_subsequence(input_text, opt)]


    def _is_subsequence(self, small: str, large: str) -> bool:
        """
        Args:
        - small (str): The input string to match.
        - large (str): The string to search within.

        Returns:
        - bool: True if 'small' is prefix of any part of 'large'. 
        """

        small = small.lower()
        parts = re.split(r'[_\s]', large.lower())
        return any(part.startswith(small) for part in parts)


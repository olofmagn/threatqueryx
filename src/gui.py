"""
GUI Interface
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional

from utils.generate_queries import build_query

from utils.configuration import load_templates, normalize_lookback, validate

from utils.ui_constants import (
    DEFAULT_MODE,
    DEFAULT_TIME_RANGE_INDEX,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_OUTPUT_HEIGHT,
    DEFAULT_PADDING,
    OUTPUT_FRAME_PADDING,
    FRAME_SIZE_MINIMUM,
    WINDOW_PADDING,
    WINDOW_TITLE,
    GRID_STICKY_EW,
    GRID_STICKY_NSEW,
    GRID_STICKY_E,
    WIDGET_PADDING_X,
    WIDGET_PADDING_Y,
    PLATFORMS,
    COMBOBOX_WIDTH,
    TIME_RANGES,
    TIME_ENTRY_WIDTH,
    COPYRIGHT_TEXT,
    COPYRIGHT_FONT,
    COPYRIGHT_COLOR,
    ARROW_BUTTON_WIDTH,
    ARROW_BUTTON_PADDING,
)


# =============================================================================
# UI STATE MANAGEMENT METHODS
# =============================================================================


def is_subsequence(small: str, large: str) -> bool:
    """
    Args:
    - small (str): The input string to match
    - large (str): The string to search within

    Returns:
    - bool: True if 'small' is prefix of any part of 'large'
    """

    small = small.lower()
    parts = re.split(r"[_\s]", large.lower())

    return any(part.startswith(small) for part in parts)


def fuzzy_match(input_text: str, options: List[str]) -> List[str]:
    """
    Args:
    - input_text (str): An input string
    - options (List[str]) : A list of possible options

    Returns:
    - A list of options that contain all characters in order from input_text
    """

    return [opt for opt in options if is_subsequence(input_text, opt)]


# =============================================================================
# TIME RANGE UTILITIES
# =============================================================================


def get_display_values() -> List[str]:
    """
    Get display values

    Returns:
    - List[str]: List of display values for time ranges
    """

    return [display for _, display in TIME_RANGES]


def get_default_time_display() -> str:
    """
    Get default time range display value

    Returns:
    - str: Default time range display value
    """

    return get_display_values()[DEFAULT_TIME_RANGE_INDEX]


def cycle_time_range_value(
    current_value: str, direction: int, display_values: List[str]
) -> str:
    """
    Cycle time range value

    Args:
    - current_value (str): Current time range value
    - direction (int): Direction to cycle (-1 or 1)
    - display_values (List[str]): Available display values

    Returns:
    - str: New time range value
    """

    try:
        current_idx = display_values.index(current_value)
    except ValueError:
        current_idx = DEFAULT_TIME_RANGE_INDEX

    new_idx = (current_idx + direction) % len(display_values)

    return display_values[new_idx]


# =============================================================================
# MAIN GUI CLASS
# =============================================================================


class QueryGui:
    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the main application window and its widgets

        Args:
        - root (tk.Tk): The root Tkinter window passed by the caller
        """

        # Initialize core attributes
        self.platforms = PLATFORMS
        self.platform = DEFAULT_MODE
        self.templates = {}
        self.base_queries = {}
        self.fields = {}

        # Window size constants
        self.MAX_WIDTH = DEFAULT_WINDOW_WIDTH
        self.MAX_HEIGHT = DEFAULT_WINDOW_HEIGHT
        self.OUTPUT_HEIGHT = DEFAULT_OUTPUT_HEIGHT

        # Time ranges
        self.time_ranges = TIME_RANGES
        self.display_values = get_display_values()

        # Template cache loading
        self.template_cache = {}

        # Setup window
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.minsize(self.MAX_HEIGHT, self.MAX_WIDTH)  # Optional minimum size
        self.root.resizable(False, False)

        self.frame = ttk.Frame(self.root, padding=WINDOW_PADDING)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.rowconfigure(7, weight=1)

        # Initialize GUI
        self._create_widgets()
        self._update_field_visibility()

    # =========================================================================
    # PROPERTY METHODS (CACHED ACCESS)
    # =========================================================================

    @property
    def current_template(self) -> str:
        """
        Current mode

        Returns:
        - str: Current mode in lowercase
        """

        return self.template_var.get().lower()

    @property
    def current_platform(self) -> str:
        """
        Current type

        Returns:
        - str: Current type selection
        """

        return self.platform_var.get()

    @property
    def current_lookback(self) -> str:
        """
        Current hash type

        Returns:
        - str: Current hash type selection
        """

        return self.lookback_var.get()

    # =========================================================================
    # WIDGET CREATION METHODS
    # =========================================================================

    def _create_widgets(self) -> None:
        """
        Create and layout all necessary widgets with consistent styling
        """

        self.frame.columnconfigure(
            0, weight=0, minsize=FRAME_SIZE_MINIMUM
        )  # Labels column
        self.frame.columnconfigure(1, weight=1)  # Controls column

        # === Platform Selector ===
        ttk.Label(self.frame, text="Platform:").grid(
            row=0,
            column=0,
            sticky=GRID_STICKY_E,
            padx=(WIDGET_PADDING_X, DEFAULT_PADDING),
            pady=WIDGET_PADDING_Y,
        )
        self.platform_var = tk.StringVar(value=self.platform)

        self.platform_menu = ttk.Combobox(
            self.frame,
            textvariable=self.platform_var,
            values=[p for p in self.platforms],
            state="readonly",
            width=COMBOBOX_WIDTH,
        )

        self.platform_menu.grid(
            row=0,
            column=1,
            sticky=GRID_STICKY_NSEW,
            padx=WIDGET_PADDING_X,
            pady=WIDGET_PADDING_Y,
        )
        self.platform_menu.bind("<<ComboboxSelected>>", self._on_platform_change)

        # === Template Selector ===
        ttk.Label(self.frame, text="Template:").grid(
            row=1,
            column=0,
            sticky=GRID_STICKY_E,
            padx=(WIDGET_PADDING_X, DEFAULT_PADDING),
            pady=WIDGET_PADDING_Y,
        )
        self.template_var = tk.StringVar()
        self.autocomplete_entry = ttk.Combobox(
            self.frame, textvariable=self.template_var, width=COMBOBOX_WIDTH
        )
        self.autocomplete_entry.grid(
            row=1,
            column=1,
            sticky=GRID_STICKY_NSEW,
            padx=WIDGET_PADDING_X,
            pady=WIDGET_PADDING_Y,
        )
        self.autocomplete_entry.bind("<<ComboboxSelected>>", self._render_fields)
        self._setup_template_autocomplete()

        # === Parameters Frame ===
        self.inputs_frame = ttk.LabelFrame(
            self.frame, text="Parameters", padding=DEFAULT_PADDING
        )

        # Init empty lists for field tracking
        self.param_rows = []
        self.fields = {}

        # === Time Range ===
        ttk.Label(self.frame, text="Time Range:").grid(
            row=4,
            column=0,
            sticky=GRID_STICKY_E,
            padx=(WIDGET_PADDING_X, DEFAULT_PADDING),
            pady=WIDGET_PADDING_Y,
        )

        time_frame = ttk.Frame(self.frame)
        time_frame.grid(
            row=4,
            column=1,
            sticky=GRID_STICKY_NSEW,
            padx=WIDGET_PADDING_X,
            pady=WIDGET_PADDING_Y,
        )

        self.lookback_var = tk.StringVar(
            value=self.display_values[DEFAULT_TIME_RANGE_INDEX]
        )
        self.time_entry = ttk.Entry(
            time_frame, textvariable=self.lookback_var, width=TIME_ENTRY_WIDTH
        )
        self.time_entry.pack(side="left")

        self.btn_time_prev = ttk.Button(
            time_frame,
            text="❮",
            style="Arrow.TButton",
            padding=ARROW_BUTTON_PADDING,
            width=ARROW_BUTTON_WIDTH,
            command=lambda: self._change_time_range(-1),
        )
        self.btn_time_prev.pack(side="left", padx=(5, 2))

        self.btn_time_next = ttk.Button(
            time_frame,
            text="❯",
            style="Arrow.TButton",
            padding=ARROW_BUTTON_PADDING,
            width=ARROW_BUTTON_WIDTH,
            command=lambda: self._change_time_range(1),
        )
        self.btn_time_next.pack(side="left", padx=(2, 0))

        # Defender button for post_pipeline
        self.include_post_pipeline_var = tk.BooleanVar(value=False)

        self.checkbox = tk.Checkbutton(
            self.frame,
            text="Apply field selection",
            variable=self.include_post_pipeline_var,
        )

        # === Generate Button ===
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=15, sticky=GRID_STICKY_EW)
        btn_frame.columnconfigure(0, weight=1)

        btn = ttk.Button(btn_frame, text="Generate Query", command=self._generate)
        btn.grid(row=0, column=0, sticky="")

        # === Output Text Box ===
        output_frame = ttk.LabelFrame(
            self.frame, text="Generated Query", padding=OUTPUT_FRAME_PADDING
        )
        output_frame.grid(row=7, column=0, columnspan=2, sticky=GRID_STICKY_NSEW)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_text = ScrolledText(
            output_frame, height=self.OUTPUT_HEIGHT, wrap=tk.WORD
        )
        self.output_text.grid(row=0, column=0, sticky=GRID_STICKY_NSEW)

        # === Copy Button ===
        copy_btn = ttk.Button(self.frame, text="Copy to Clipboard", command=self._copy)
        copy_btn.grid(row=8, column=0, columnspan=2, sticky="", pady=WIDGET_PADDING_Y)

        # === Separator ===
        separator = ttk.Separator(self.frame, orient="horizontal")
        separator.grid(
            row=9,
            column=0,
            columnspan=2,
            sticky=GRID_STICKY_NSEW,
            pady=(DEFAULT_PADDING, 5),
        )

        # === Info Label ===
        self.platform_info_label = ttk.Label(self.frame, text="")
        self.platform_info_label.grid(
            row=10,
            column=0,
            columnspan=2,
            sticky=GRID_STICKY_NSEW,
            pady=WIDGET_PADDING_Y,
            padx=WIDGET_PADDING_X,
        )
        self.platform_info_label.config(anchor="center", justify="center")

        # === Copyright Label ===
        self.copyright_label = ttk.Label(
            self.frame,
            text=COPYRIGHT_TEXT,
            font=COPYRIGHT_FONT,
            foreground=COPYRIGHT_COLOR,
        )

        self.copyright_label.grid(
            row=12,
            column=2,
            sticky=GRID_STICKY_E,
            pady=(0, DEFAULT_PADDING),
            padx=WIDGET_PADDING_X,
        )

        # === Load templates initially ===
        self.load_templates_for_platform(self.platform)

    def _change_time_range(self, direction: int) -> None:
        """
        Change time range

        Args:
        - direction (int): Direction to navigate (-1 for prev, 1 for next)
        """

        current_value = self.current_lookback
        new_value = cycle_time_range_value(
            current_value, direction, self.display_values
        )
        self.lookback_var.set(new_value)

    def _setup_template_autocomplete(self) -> None:
        """
        Setup autocomplete
        """

        self.listbox = None

        def _on_select_commit(event: Optional[tk.Event] = None) -> str:
            """
            Handler for when a suggestion is selected from the listbox

            Args:
            - event (Optional[tk.Event]): The Tkinter event that triggered the handler
            """

            if self.listbox and self.listbox.curselection():
                try:
                    index = self.listbox.curselection()[0]
                    selected = self.listbox.get(index)
                    self.template_var.set(selected)
                    self._render_fields()
                except IndexError:
                    pass
            if self.listbox:
                self._hide_listbox()

            # Refocus entry for further typing
            self.autocomplete_entry.focus_set()
            self.autocomplete_entry.icursor(tk.END)
            return "break"

        def _on_return(event: Optional[tk.Event] = None) -> str:
            """
            Handler for the Return (Enter) key press event

            Args:
            - event (Optional[tk.Event]): The Tkinter event that triggered the handler

            Returns:
            - str: "break" to prevent default behavior
            """

            return _on_select_commit()

        def _update_suggestions(event: Optional[tk.Event] = None) -> str:
            """
            Handler for update suggestions

            Args:
            - event (Optional[tk.Event]): The Tkinter event that triggered the handler
            """

            typed = self.template_var.get().lower()
            matches = (
                fuzzy_match(typed, list(self.templates.keys()))
                if typed
                else list(self.templates.keys())
            )

            if self.listbox:
                self._hide_listbox()

            if not matches:
                return "break"

            self.listbox = tk.Listbox(self.frame, height=min(5, len(matches)))
            self.listbox.grid(
                row=2,
                column=1,
                sticky=GRID_STICKY_EW,
                pady=WIDGET_PADDING_Y,
                padx=WIDGET_PADDING_X,
            )

            for match in matches:
                self.listbox.insert(tk.END, match)

            self.listbox.select_set(0)
            self.listbox.activate(0)

            self.listbox.bind("<ButtonRelease-1>", _on_select_commit)
            self.listbox.bind("<Return>", _on_return)
            self.listbox.bind("Escape", self._hide_listbox)

            return "break"

        def _on_listbox_nav(event: Optional[tk.Event] = None) -> str:
            """
            Handler for navigating the autocomplete listbox using keyboard arrows

            Args:
            - event (Optional[tk.Event]): The Tkinter event that triggered the handler
            """

            if not self.listbox:
                return "break"

            curr = self.listbox.curselection()
            total = self.listbox.size()

            if not total:
                return "break"

            current_index = curr[0] if curr else -1

            direction = {"Up": -1, "Down": +1}.get(event.keysym)
            if direction is None:
                return "break"

            next_index = (current_index + direction) % total

            self.listbox.select_clear(0, tk.END)
            self.listbox.select_set(next_index)
            self.listbox.activate(next_index)
            self.listbox.focus_set()
            return "break"

        self.autocomplete_entry.bind("<Return>", _on_return)
        self.autocomplete_entry.bind("<KeyRelease>", _update_suggestions)
        self.autocomplete_entry.bind("<Down>", _on_listbox_nav)
        self.autocomplete_entry.bind("<Up>", _on_listbox_nav)

    def _update_field_visibility(self) -> None:
        """
        Update field visibility info label for all platforms
        """

        self.platform_info_label.config(text=self._get_platform_info_text())

        if self.platform.lower() == "defender":
            self.checkbox.grid(
                row=5,
                column=0,
                columnspan=2,
                padx=WIDGET_PADDING_X,
                pady=WIDGET_PADDING_Y,
                sticky=GRID_STICKY_NSEW,
            )
        else:
            self.checkbox.grid_forget()  # hide checkbox

    # ==========================================
    # TEMPLATE & DATA MANAGEMENT
    # ==========================================

    def load_templates_for_platform(self, platform: str) -> None:
        """
        Loads templates for a given platform

        Args:
        - platform: the platform, e.g., 'qradar', 'defender' or 'elastic'
        """

        if platform in self.template_cache:
            self.templates, self.base_queries = self.template_cache[platform]
        else:
            try:
                config = load_templates(platform)
                self.base_queries = config.get("base_queries", {})
                self.templates = {
                    k: v for k, v in config.items() if k != "base_queries"
                }
                self.template_cache[platform] = (self.templates, self.base_queries)
            except Exception as e:
                messagebox.showerror("Error loading templates", str(e))
                self.templates = {}

        self.template_var.set("")
        self.autocomplete_entry["values"] = list(self.templates.keys())
        self._clear_fields()

    def _clear_fields(self) -> None:
        """
        Destroy all parameter widgets and clear state
        """

        for widget in self.inputs_frame.winfo_children():
            widget.destroy()

        self.param_rows.clear()  # clear stored refs
        self.fields.clear()
        self.output_text.delete("1.0", tk.END)

    def _render_fields(self, event: Optional[tk.Event] = None) -> None:
        """
        Renders fields event handler

        Args:
        - event (Optional[tk.Event]): The Tkinter event that triggered the handler
        """

        self._clear_fields()

        template_name = self.current_template
        if not template_name in self.templates:
            messagebox.showerror(
                "Invalid template", f"Template {template_name} not found"
            )
            return

        template = self.templates[template_name]
        optional_fields = template.get("optional_fields", {})

        if optional_fields:
            self.inputs_frame.grid(
                row=3,
                column=0,
                columnspan=2,
                sticky=GRID_STICKY_NSEW,
                padx=WIDGET_PADDING_X,
                pady=WIDGET_PADDING_Y,
            )
        else:
            self.inputs_frame.grid_remove()

        self.inputs_frame.columnconfigure(0, weight=0, minsize=120)
        self.inputs_frame.columnconfigure(1, weight=1)

        for i, (field, meta) in enumerate(optional_fields.items()):
            label_text = field
            help_text = ""

            if isinstance(meta, dict):
                help_text = meta.get("help", "")

            if help_text:
                label_text += f" ({help_text})"

            # Optional fields layout
            label = ttk.Label(self.inputs_frame, text=label_text + ":")
            entry_var = tk.StringVar()
            entry = ttk.Entry(self.inputs_frame, textvariable=entry_var)

            label.grid(
                row=i,
                column=0,
                sticky=GRID_STICKY_E,
                padx=WIDGET_PADDING_X,
                pady=WIDGET_PADDING_Y,
            )
            entry.grid(
                row=i,
                column=1,
                sticky=GRID_STICKY_EW,
                padx=WIDGET_PADDING_X,
                pady=WIDGET_PADDING_Y,
            )

            self.param_rows.append((label, entry, entry_var))

            self.fields[field] = (
                entry_var,
                meta.get("validation") if isinstance(meta, dict) else None,
            )

    # ==========================================
    # CORE BUSINESS LOGIC
    # ==========================================

    def _generate(self) -> int | None:
        """
        Builds a query for a given platform
        """

        template_name = self.current_template
        platform = self.current_platform
        lookback = self.current_lookback

        if not template_name:
            messagebox.showerror("Error", "Invalid template choice.")
            return 0

        if template_name not in self.templates:
            messagebox.showerror(
                "Error", "Template '{}' not found.".format(template_name)
            )

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

        include_post = (
            self.include_post_pipeline_var.get() if platform == "defender" else False
        )

        try:
            query = build_query(
                template, inputs, duration, platform, self.base_queries, include_post
            )
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

    # ==========================================
    # EVENT HANDLERS
    # ==========================================

    def _on_platform_change(self, event: tk.Event = None) -> None:
        """
        Used to detect platform change so templates gets correctly loaded
        """

        plat = self.current_platform
        if plat:
            self.platform = plat
            self.load_templates_for_platform(plat)

        # Clear the template input field and hide suggestions
        self.template_var.set("")
        if self.listbox:
            self._hide_listbox()

        self._update_field_visibility()

    def _hide_listbox(self, event: Optional[tk.Event] = None) -> str:
        """
        Hides the suggestion listbox if it exists

        Args:
        - event (Optional[tk.Event]): The Tkinter event that triggered the action
        """

        if hasattr(self, "listbox") and self.listbox:
            self.listbox.destroy()
            self.listbox = None
        return "break"

    # ==========================================
    # UTILITY METHODS
    # ==========================================

    def _get_platform_info_text(self) -> str | None:
        """
        Get the current platform in use.

        Returns:
        - str: The display platform in use.
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

import os
import queue
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from core.batchProcessor.batch_processor_factory import BatchProcessorFactory
from core.batchProcessor.Ibatch_processor import ProcessingObserver
from core.plugin_manager import PluginManager
from model.Iprocessor import IProcessor, ProcessorCategory


class MainWindow(tk.Tk, ProcessingObserver):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Set window properties
        self.title("Batch File Processor")
        self.geometry("1080x720")
        self.minsize(800, 600)

        # Set up default output path
        default_output_dir = Path("results").resolve()
        # Create the directory if it doesn't exist
        default_output_dir.mkdir(exist_ok=True)

        # Initialize state
        self.selected_files: List[str] = []
        self.output_path = default_output_dir
        self.plugin_manager = PluginManager()
        self.batch_processor_factory = BatchProcessorFactory()
        self.selected_processor: Optional[IProcessor] = None
        self.max_workers_var = tk.IntVar(value=os.cpu_count())
        self.save_format_var = tk.StringVar()
        self.batch_size = 8  # Number of results to process at once
        self.result_queue = queue.Queue()
        self.processed_files = 0
        self.total_files = 0

        # Load plugins
        self.processors = self.plugin_manager.get_processor_instances()
        if self.processors:
            self.selected_processor = self.processors[0]
            # Initialize save format with the first processor's formats
            save_formats = self.selected_processor.save_format
            if save_formats:
                self.save_format_var.set(
                    f"{save_formats[0][0]} (*.{save_formats[0][1]})"
                )

        # Create UI components
        self._create_ui()

        # Initialize save format combobox with values from the selected processor
        if self.processors and self.selected_processor:
            save_formats = self.selected_processor.save_format
            self.save_format_combo.config(
                values=[f"{desc} (*.{ext})" for desc, ext in save_formats]
            )
            if save_formats:
                self.save_format_combo.current(0)

            # Configure UI based on processor type
            self._update_ui_for_processor_type()

        # Show warning if no processors found
        if not self.processors:
            self.selected_processor = None
            self.description_var.set("")
            self.status_var.set("No processing plugins found")
            messagebox.showwarning(
                "No Processors Found",
                "No processing plugins were found. Please add plugins to the 'plugins' directory.",
            )

    def _create_ui(self):
        """Create the user interface components."""
        # Create main frame with some padding for better spacing
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create top, middle, and bottom sections
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True)

        # Create a PanedWindow for resizable split
        self.paned_window = ttk.PanedWindow(middle_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create left and right panes for the file list and results
        left_pane = ttk.Frame(self.paned_window)
        right_pane = ttk.Frame(self.paned_window)

        # Add the panes to the PanedWindow with equal weights
        self.paned_window.add(left_pane, weight=1)
        self.paned_window.add(right_pane, weight=1)

        # Top section components (processor selection and output settings)
        top_left_frame = ttk.Frame(top_frame)
        top_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        top_right_frame = ttk.Frame(top_frame)
        top_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self._create_processor_frame(top_left_frame)
        self._create_file_operations_frame(top_right_frame)

        # Middle section components
        self._create_files_frame(left_pane)

        # Right pane with progress and results
        right_content_frame = ttk.Frame(right_pane)
        right_content_frame.pack(fill=tk.BOTH, expand=True)

        self._create_progress_frame(right_content_frame)
        self._create_results_frame(right_content_frame)

        # Create status bar
        self._create_status_bar()

    def _create_processor_frame(self, parent):
        """Create the processor selection frame."""
        frame = ttk.LabelFrame(parent, text="Select Processing Tool")
        frame.pack(fill=tk.BOTH, expand=True)

        # Create a grid layout for better organization
        frame.columnconfigure(1, weight=1)  # Make description column expandable

        # Row 1: Processor selection and refresh button
        ttk.Label(frame, text="Processor:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )

        processor_frame = ttk.Frame(frame)
        processor_frame.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Processor combobox
        self.processor_var = tk.StringVar()
        self.processor_combo = ttk.Combobox(
            processor_frame,
            textvariable=self.processor_var,
            values=[p.name for p in self.processors if p.name],
            state="readonly" if self.processors else "disabled",
            width=30,
        )

        self.processor_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if self.processors:
            self.processor_combo.current(0)
        self.processor_combo.bind("<<ComboboxSelected>>", self._on_processor_selected)

        # Refresh button
        self.refresh_btn = ttk.Button(
            processor_frame, text="Refresh", command=self._refresh_plugins
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Row 2: Description
        ttk.Label(frame, text="Description:").grid(
            row=1, column=0, sticky=tk.NW, padx=5, pady=5
        )

        self.description_var = tk.StringVar()
        if self.selected_processor:
            self.description_var.set(self.selected_processor.description)
        self.description_label = ttk.Label(
            frame, textvariable=self.description_var, wraplength=400, justify=tk.LEFT
        )
        self.description_label.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

    def _create_file_operations_frame(self, parent):
        """Create the file operations frame."""
        frame = ttk.LabelFrame(parent, text="Output Settings")
        frame.pack(fill=tk.BOTH, expand=True)

        # Use grid layout for better alignment
        frame.columnconfigure(1, weight=1)

        # Row 1: Output selector (directory or file based on processor type)
        self.output_label = ttk.Label(frame, text="Output Path:")
        self.output_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        output_dir_frame = ttk.Frame(frame)
        output_dir_frame.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        self.output_path_var = tk.StringVar(value=self.output_path)
        self.output_path_entry = ttk.Entry(
            output_dir_frame, textvariable=self.output_path_var
        )
        self.output_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Browse button
        self.browse_btn = ttk.Button(
            output_dir_frame, text="Browse...", command=self._browse_output
        )
        self.browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Row 2: Save format and workers
        ttk.Label(frame, text="Save Format:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )

        options_frame = ttk.Frame(frame)
        options_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        self.save_format_combo = ttk.Combobox(
            options_frame, textvariable=self.save_format_var, state="readonly", width=20
        )
        self.save_format_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.save_format_combo.bind(
            "<<ComboboxSelected>>", self._on_save_format_selected
        )

        ttk.Label(options_frame, text="Parallel Cores:").pack(
            side=tk.LEFT, padx=(15, 5)
        )
        self.workers_spinbox = ttk.Spinbox(
            options_frame,
            from_=1,
            to=os.cpu_count() * 2,
            width=5,
            textvariable=self.max_workers_var,
        )
        self.workers_spinbox.pack(side=tk.LEFT)

    def _create_files_frame(self, parent):
        """Create the files list frame."""
        frame = ttk.LabelFrame(parent, text="Selected Files")
        frame.pack(fill=tk.BOTH, expand=True)

        # Top control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.select_files_btn = ttk.Button(
            control_frame, text="Select Files", command=self._select_files, width=12
        )
        self.select_files_btn.pack(side=tk.LEFT)

        self.delete_selected_btn = ttk.Button(
            control_frame,
            text="Delete Selected",
            command=self._delete_selected_files,
            width=14,
        )
        self.delete_selected_btn.pack(side=tk.LEFT, padx=5)

        self.clear_all_btn = ttk.Button(
            control_frame, text="Clear All", command=self._clear_all_files, width=10
        )
        self.clear_all_btn.pack(side=tk.LEFT)

        # Process button in a separate row
        process_frame = ttk.Frame(frame)
        process_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.process_btn = ttk.Button(
            process_frame,
            text="Process Files",
            command=self._process_files,
            state=tk.DISABLED,
            padding=5,
        )
        self.process_btn.pack(fill=tk.X, expand=True)

        # File count indicator
        self.file_count_var = tk.StringVar(value="0 files selected")
        self.file_count_label = ttk.Label(frame, textvariable=self.file_count_var)
        self.file_count_label.pack(anchor=tk.W, padx=10, pady=(0, 5))

        # Files listbox with border frame
        listbox_frame = ttk.Frame(frame, relief=tk.SUNKEN, borderwidth=1)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.files_listbox = tk.Listbox(
            listbox_frame, selectmode=tk.EXTENDED, borderwidth=0, highlightthickness=0
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=scrollbar.set)

    def _create_progress_frame(self, parent):
        """Create the progress frame."""
        frame = ttk.LabelFrame(parent, text="Processing Progress")
        frame.pack(fill=tk.X, pady=(0, 5))

        # Use a container with padding
        inner_frame = ttk.Frame(frame, padding=5)
        inner_frame.pack(fill=tk.X)

        # Progress bar and percentage in one row
        progress_frame = ttk.Frame(inner_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            length=100,
            mode="determinate",
            variable=self.progress_var,
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Progress percentage
        self.progress_percent_var = tk.StringVar(value="0%")
        self.progress_percent_label = ttk.Label(
            progress_frame, textvariable=self.progress_percent_var, width=5
        )
        self.progress_percent_label.pack(side=tk.RIGHT)

        # Status message
        self.process_status_var = tk.StringVar(value="Ready to process")
        self.process_status_label = ttk.Label(
            inner_frame, textvariable=self.process_status_var, foreground="blue"
        )
        self.process_status_label.pack(anchor=tk.W, pady=(5, 0))

    def _create_results_frame(self, parent):
        """Create the results frame."""
        frame = ttk.LabelFrame(parent, text="Processing Results")
        frame.pack(fill=tk.BOTH, expand=True)

        # Results treeview with padding
        results_frame = ttk.Frame(frame, padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("file", "result_file", "status")
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Results.Treeview",
        )

        # Create a style
        style = ttk.Style()
        style.configure("Results.Treeview", rowheight=25)

        self.results_tree.heading("file", text="Input File")
        self.results_tree.heading("result_file", text="Output File")
        self.results_tree.heading("status", text="Status")

        # Better proportions
        self.results_tree.column("file", width=200, minwidth=150)
        self.results_tree.column("result_file", width=200, minwidth=150)
        self.results_tree.column("status", width=150, minwidth=100)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            results_frame, orient=tk.VERTICAL, command=self.results_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.config(yscrollcommand=scrollbar.set)

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _refresh_plugins(self):
        """Refresh the list of available plugins."""
        self.processors = self.plugin_manager.get_processor_instances()

        # Update the combobox
        self.processor_combo.config(
            values=[p.name for p in self.processors],
            state="readonly" if self.processors else "disabled",
        )

        if self.processors:
            self.processor_combo.current(0)
            self.selected_processor = self.processors[0]
            self.description_var.set(self.selected_processor.description)
            self.status_var.set(f"Selected tool: {self.selected_processor.name}")

            # Update save format options
            save_formats = self.selected_processor.save_format
            self.save_format_combo.config(
                values=[f"{desc} (*.{ext})" for desc, ext in save_formats]
            )
            if save_formats:
                self.save_format_combo.current(0)
                self.save_format_var.set(
                    f"{save_formats[0][0]} (*.{save_formats[0][1]})"
                )
        else:
            self.selected_processor = None
            self.description_var.set("")
            self.status_var.set("No processing plugins found")
            messagebox.showwarning(
                "No Processors Found",
                "No processing plugins were found. Please add plugins to the 'plugins' directory.",
            )
            self.save_format_combo.config(values=[])

    def _on_save_format_selected(self, event):
        """Handle save format selection change."""
        selected_format = self.save_format_var.get()

        # Extract the extension from the format string (e.g., "CSV (*.csv)" -> ".csv")
        extension = ""
        if "(*." in selected_format:
            extension = "." + selected_format.split("*.")[-1].split(")")[0]

        # Make sure the result path is updated to the new format
        if extension:
            self.output_path_var.set(
                str(self.output_path.with_suffix(extension).resolve())
            )

    def _on_processor_selected(self, event):
        """Handle processor selection change."""
        selected_name = self.processor_var.get()
        for processor in self.processors:
            if processor.name == selected_name:
                self.selected_processor = processor
                self.description_var.set(processor.description)
                self.status_var.set(f"Selected tool: {processor.name}")

                # Update save format options
                save_formats = processor.save_format
                self.save_format_combo.config(
                    values=[f"{desc} (*.{ext})" for desc, ext in save_formats]
                )
                if save_formats:
                    self.save_format_combo.current(0)
                    self.save_format_var.set(
                        f"{save_formats[0][0]} (*.{save_formats[0][1]})"
                    )

                # Update UI based on processor type
                self._update_ui_for_processor_type()
                break

    def _update_ui_for_processor_type(self):
        """Update UI elements based on the type of selected processor."""
        if not self.selected_processor:
            return

        # Update output label and tooltip based on processor type
        if self.selected_processor.category == ProcessorCategory.INDIVIDUAL:
            self.output_label.config(text="Output Directory:")

            # Reset output path if it's a file (from previous Adjoint processor)
            if self.output_path.is_file():
                default_output_dir = Path("results").resolve()
                default_output_dir.mkdir(exist_ok=True)
                self.output_path = default_output_dir
                self.output_path_var.set(str(default_output_dir))

        elif self.selected_processor.category == ProcessorCategory.ADJOINT:
            self.output_label.config(text="Output File:")

            # If current output is a directory, suggest a file in that directory
            if self.output_path.is_dir():
                default_ext = ""
                if self.selected_processor.save_format:
                    default_ext = self.selected_processor.save_format[0][1]

                default_file = (
                    self.output_path / f"{self.selected_processor.name}_results"
                )
                if default_ext:
                    default_file = default_file.with_suffix(f".{default_ext}")

                # Don't automatically set the path, just update the display
                self.output_path_var.set(str(default_file))

    def _browse_output(self):
        """Browse for output directory or file, depending on processor type."""
        if not self.selected_processor:
            messagebox.showinfo(
                "No Tool Selected", "Please select a processing tool first."
            )
            return

        if self.selected_processor.category == ProcessorCategory.INDIVIDUAL:
            self._browse_output_directory()
        elif self.selected_processor.category == ProcessorCategory.ADJOINT:
            self._browse_output_file()
        else:
            # Default to directory browsing for unknown processor types
            self._browse_output_directory()

    def _browse_output_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory", initialdir=self.output_path
        )
        if directory:
            self.output_path = Path(directory)
            self.output_path_var.set(directory)

    def _browse_output_file(self):
        """Browse for output file."""
        if not self.selected_processor:
            return

        # Get file extensions from the processor
        save_formats = self.selected_processor.save_format
        if not save_formats:
            save_formats = [("All files", "*.*")]

        # Create file types tuple for dialog
        filetypes = [(desc, f"*.{ext}") for desc, ext in save_formats]

        # Get default extension from currently selected format
        default_ext = ""
        if self.save_format_var.get() and "(*." in self.save_format_var.get():
            default_ext = self.save_format_var.get().split("*.")[-1].split(")")[0]

        # Default filename based on processor name
        default_name = f"{self.selected_processor.name}_results"
        if default_ext:
            default_name = f"{default_name}.{default_ext}"

        file_path = filedialog.asksaveasfilename(
            title="Select Output File",
            initialdir=self.output_path.parent,
            initialfile=default_name,
            filetypes=filetypes,
            defaultextension=f".{default_ext}" if default_ext else None,
        )

        if file_path:
            self.output_path = Path(file_path)
            self.output_path_var.set(file_path)

    def _select_files(self):
        """Select files to process."""
        if not self.selected_processor:
            messagebox.showinfo(
                "No Tool Selected", "Please select a processing tool first."
            )
            return

        filetypes = self.selected_processor.file_types

        files = filedialog.askopenfilenames(title="Select files", filetypes=filetypes)

        if files:
            self.selected_files.extend(list(files))
            self._update_files_listbox()
            self._update_process_button_state()
            self.file_count_var.set(f"{len(self.selected_files)} files selected")
            self.status_var.set(
                f"Added {len(files)} files. Total: {len(self.selected_files)} files"
            )
            self.progress_var.set(0)
            self.progress_percent_var.set("0%")
            self.process_status_var.set("Ready to process")

    def _delete_selected_files(self):
        """Remove selected files from the list."""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            return

        # Convert to list and sort in reverse order to avoid index shifting
        indices_to_remove = sorted(selected_indices, reverse=True)

        # Remove the files from the list
        for index in indices_to_remove:
            del self.selected_files[index]

        self._update_files_listbox()
        self._update_process_button_state()
        self.file_count_var.set(f"{len(self.selected_files)} files selected")
        self.status_var.set(
            f"Removed {len(selected_indices)} files. Remaining: {len(self.selected_files)} files"
        )

    def _clear_all_files(self):
        """Clear all files from the list."""
        if not self.selected_files:
            return

        file_count = len(self.selected_files)
        self.selected_files.clear()
        self._update_files_listbox()
        self._update_process_button_state()
        self.file_count_var.set("0 files selected")
        self.status_var.set(f"Cleared {file_count} files from the list")

    def _update_process_button_state(self):
        """Update the state of the process button based on file selection."""
        if self.selected_files:
            self.process_btn.config(state=tk.NORMAL)
        else:
            self.process_btn.config(state=tk.DISABLED)

    def _update_files_listbox(self):
        """Update the files listbox with selected files."""
        self.files_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.files_listbox.insert(tk.END, os.path.basename(file))

    def _process_files(self):
        """Process the selected files."""
        if not self.selected_files:
            messagebox.showinfo("No Files", "Please select files to process first.")
            return

        if not self.selected_processor:
            messagebox.showinfo(
                "No Tool Selected", "Please select a processing tool first."
            )
            return

        # Validate output path based on processor type
        output_path = Path(self.output_path_var.get())
        if self.selected_processor.category == ProcessorCategory.INDIVIDUAL:
            # Ensure output path is a directory for individual processors
            if output_path.exists() and not output_path.is_dir():
                messagebox.showerror(
                    "Invalid Output Path",
                    "For this processor type, the output path must be a directory.",
                )
                return
            # Create directory if it doesn't exist
            if not output_path.exists():
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                except Exception as error:
                    messagebox.showerror(
                        "Error Creating Directory",
                        f"Could not create output directory: {error}",
                    )
                    return

        elif self.selected_processor.category == ProcessorCategory.ADJOINT:
            # For adjoint processors, ensure the output path is a file
            if output_path.exists() and output_path.is_dir():
                messagebox.showerror(
                    "Invalid Output Path",
                    "For this processor type, the output path must be a file, not a directory.",
                )
                return
            # Ensure parent directory exists
            if not output_path.parent.exists():
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as error:
                    messagebox.showerror(
                        "Error Creating Directory",
                        f"Could not create parent directory: {error}",
                    )
                    return

        # Update output path with validated path
        self.output_path = output_path

        # Get selected save format
        save_format = ""
        if self.save_format_var.get():
            # Extract extension from the format string like "Text (*.txt)"
            format_str = self.save_format_var.get()
            if "(*." in format_str:
                save_format = format_str.split("*.")[-1].split(")")[0]

        # Get number of workers
        try:
            max_workers = self.max_workers_var.get()
            if max_workers < 1:
                max_workers = None
        except (ValueError, TypeError) as error:
            print(f"Error getting max workers: {error}")
            max_workers = None

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Reset progress bar
        self.progress_var.set(0)
        self.progress_percent_var.set("0%")
        self.process_status_var.set(
            f"Processing with {self.selected_processor.name}..."
        )

        # Disable buttons during processing
        self._set_controls_state(tk.DISABLED)

        self.status_var.set(f"Processing files with {self.selected_processor.name}...")
        self.update()

        try:
            # Create batch processor and start processing
            self.batch_processor = self.batch_processor_factory.create_batch_processor(
                self.selected_processor, self.output_path
            )
            self.batch_processor.add_observer(self)
            self.batch_processor.process_files(
                self.selected_files, max_workers, save_format
            )
        except Exception as error:
            # Re-enable buttons
            self._set_controls_state(tk.NORMAL)
            self.process_status_var.set(f"Error: {error}")
            self.status_var.set(f"Error: {error}")
            messagebox.showerror("Processing Error", f"An error occurred: {error}")
            print(f"Error in processing: {error}")

    def _set_controls_state(self, state):
        """Set the state of control buttons."""
        self.select_files_btn.config(state=state)
        self.process_btn.config(state=state)
        self.browse_btn.config(state=state)
        self.workers_spinbox.config(state=state)
        self.processor_combo.config(state="readonly" if state == tk.NORMAL else state)
        self.refresh_btn.config(state=state)
        self.save_format_combo.config(state="readonly" if state == tk.NORMAL else state)
        self.delete_selected_btn.config(state=state)
        self.clear_all_btn.config(state=state)

    # ProcessingObserver implementation
    def on_start(self, total_files):
        """Called when processing starts."""
        self.processed_files = 0
        self.total_files = total_files

    def on_file_complete(self, file, result, success, message=""):
        """Called when a file is processed."""
        # Extract just the filename for display
        filename = os.path.basename(file)
        result_filename = os.path.basename(result) if result else ""

        # Update results treeview
        if success:
            self.results_tree.insert(
                "",
                tk.END,
                values=(
                    filename,
                    result_filename,
                    "Success",
                ),
                tags=("success",),
            )
        else:
            error_message = message if message else "Unknown error"
            self.results_tree.insert(
                "",
                tk.END,
                values=(filename, "", f"Error: {error_message}"),
                tags=("error",),
            )
            # Log the error
            print(f"Error processing file {filename}: {error_message}")

        # Configure tag colors
        self.results_tree.tag_configure("success", foreground="green")
        self.results_tree.tag_configure("error", foreground="red")

        # Update progress
        self.processed_files += 1
        progress_percent = (self.processed_files / self.total_files) * 100
        self.progress_var.set(progress_percent)
        self.progress_percent_var.set(f"{int(progress_percent)}%")

        # Update status messages
        status_text = f"Processed {self.processed_files} of {self.total_files} files"
        self.process_status_var.set(status_text)
        self.status_var.set(status_text)

        # Make sure UI updates are applied
        self.update_idletasks()

    def on_complete(self):
        """Called when all processing is complete."""
        self.progress_var.set(100)
        self.progress_percent_var.set("100%")
        self.process_status_var.set(
            f"Processing complete: {self.total_files} files processed"
        )
        self.status_var.set(f"Processed {self.total_files} files")

        # Re-enable buttons
        self._set_controls_state(tk.NORMAL)

        # Show completion message
        messagebox.showinfo(
            "Processing Complete", f"Processed {self.total_files} files."
        )

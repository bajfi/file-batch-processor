import os
import queue
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from core.batch_processor import BatchProcessor, ProcessingObserver
from core.plugin_manager import PluginManager
from model.processor import Processor


class MainWindow(tk.Tk, ProcessingObserver):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Set window properties
        self.title("Batch File Processor")
        self.geometry("1080x720")
        self.minsize(800, 600)

        # Initialize state
        self.selected_files: List[str] = []
        self.output_dir = Path("results").resolve()
        self.plugin_manager = PluginManager()
        self.selected_processor: Optional[Processor] = None
        self.max_workers_var = tk.IntVar(value=os.cpu_count())
        self.batch_size = 8  # Number of results to process at once
        self.result_queue = queue.Queue()

        # Load plugins
        self.processors = self.plugin_manager.get_processor_instances()
        if self.processors:
            self.selected_processor = self.processors[0]

        # Create UI components
        self._create_ui()

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
        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create processor selection frame
        self._create_processor_frame(main_frame)

        # Create file operations frame
        self._create_file_operations_frame(main_frame)

        # Create files list frame
        self._create_files_frame(main_frame)

        # Create progress frame
        self._create_progress_frame(main_frame)

        # Create results frame
        self._create_results_frame(main_frame)

        # Create status bar
        self._create_status_bar()

    def _create_processor_frame(self, parent):
        """Create the processor selection frame."""
        frame = ttk.LabelFrame(parent, text="Select Processing Tool")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Processor combobox
        self.processor_var = tk.StringVar()
        self.processor_combo = ttk.Combobox(
            frame,
            textvariable=self.processor_var,
            values=[p.name for p in self.processors],
            state="readonly" if self.processors else "disabled",
            width=30,
        )
        self.processor_combo.pack(side=tk.LEFT, padx=10, pady=10)
        if self.processors:
            self.processor_combo.current(0)
        self.processor_combo.bind("<<ComboboxSelected>>", self._on_processor_selected)

        # Refresh button
        self.refresh_btn = ttk.Button(
            frame, text="Refresh Plugins", command=self._refresh_plugins
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=10)

        # Description
        self.description_var = tk.StringVar()
        if self.selected_processor:
            self.description_var.set(self.selected_processor.description)
        self.description_label = ttk.Label(
            frame, textvariable=self.description_var, wraplength=500
        )
        self.description_label.pack(
            side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True
        )

    def _create_file_operations_frame(self, parent):
        """Create the file operations frame."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 10))

        # Select files button
        self.select_files_btn = ttk.Button(
            frame, text="Select Files", command=self._select_files
        )
        self.select_files_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Process button
        self.process_btn = ttk.Button(
            frame, text="Process Files", command=self._process_files, state=tk.DISABLED
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Output directory
        ttk.Label(frame, text="Output Directory:").pack(side=tk.LEFT, padx=(10, 5))
        self.output_dir_var = tk.StringVar(value=self.output_dir)
        self.output_dir_entry = ttk.Entry(
            frame, textvariable=self.output_dir_var, width=20
        )
        self.output_dir_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Browse button
        self.browse_dir_btn = ttk.Button(
            frame, text="Browse...", command=self._browse_output_dir
        )
        self.browse_dir_btn.pack(side=tk.LEFT)

        # Workers control
        ttk.Label(frame, text="Parallel Cores:").pack(side=tk.LEFT, padx=(10, 5))
        self.workers_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=os.cpu_count() * 2,
            width=5,
            textvariable=self.max_workers_var,
        )
        self.workers_spinbox.pack(side=tk.LEFT)

    def _create_files_frame(self, parent):
        """Create the files list frame."""
        frame = ttk.LabelFrame(parent, text="Selected Files")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Files listbox
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.files_listbox = tk.Listbox(listbox_frame)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=scrollbar.set)

    def _create_progress_frame(self, parent):
        """Create the progress frame."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 10))

        # Progress bar
        ttk.Label(frame, text="Progress:").pack(side=tk.LEFT, padx=(0, 5))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame,
            orient=tk.HORIZONTAL,
            length=100,
            mode="determinate",
            variable=self.progress_var,
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Progress percentage
        self.progress_percent_var = tk.StringVar(value="0%")
        self.progress_percent_label = ttk.Label(
            frame, textvariable=self.progress_percent_var, width=5
        )
        self.progress_percent_label.pack(side=tk.LEFT, padx=(5, 0))

    def _create_results_frame(self, parent):
        """Create the results frame."""
        frame = ttk.LabelFrame(parent, text="Processing Results")
        frame.pack(fill=tk.BOTH, expand=True)

        # Results treeview
        results_frame = ttk.Frame(frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("file", "result_file", "status")
        self.results_tree = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )
        self.results_tree.heading("file", text="Input File")
        self.results_tree.heading("result_file", text="Output File")
        self.results_tree.heading("status", text="Status")

        self.results_tree.column("file", width=250)
        self.results_tree.column("result_file", width=250)
        self.results_tree.column("status", width=200)

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
            self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
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
        else:
            self.selected_processor = None
            self.description_var.set("")
            self.status_var.set("No processing plugins found")
            messagebox.showwarning(
                "No Processors Found",
                "No processing plugins were found. Please add plugins to the 'plugins' directory.",
            )

    def _on_processor_selected(self, event):
        """Handle processor selection change."""
        selected_name = self.processor_var.get()
        for processor in self.processors:
            if processor.name == selected_name:
                self.selected_processor = processor
                self.description_var.set(processor.description)
                self.status_var.set(f"Selected tool: {processor.name}")
                break

    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory", initialdir=self.output_dir
        )
        if directory:
            self.output_dir = Path(directory)
            self.output_dir_var.set(directory)

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
            self.selected_files = list(files)
            self._update_files_listbox()
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Selected {len(self.selected_files)} files")
            self.progress_var.set(0)
            self.progress_percent_var.set("0%")

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

        # Get output directory
        output_dir = self.output_dir_var.get()
        if not output_dir:
            output_dir = "results"

        # Get number of workers
        try:
            max_workers = self.max_workers_var.get()
            if max_workers < 1:
                max_workers = None
        except Exception as e:
            print(f"Error getting max workers: {e}")
            max_workers = None

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Reset progress bar
        self.progress_var.set(0)
        self.progress_percent_var.set("0%")

        # Disable buttons during processing
        self._set_controls_state(tk.DISABLED)

        self.status_var.set(f"Processing files with {self.selected_processor.name}...")
        self.update()

        # Create batch processor and start processing
        self.batch_processor = BatchProcessor(self.selected_processor, output_dir)
        self.batch_processor.add_observer(self)
        self.batch_processor.process_files(self.selected_files, max_workers)

    def _set_controls_state(self, state):
        """Set the state of control buttons."""
        self.select_files_btn.config(state=state)
        self.process_btn.config(state=state)
        self.browse_dir_btn.config(state=state)
        self.workers_spinbox.config(state=state)
        self.processor_combo.config(state="readonly" if state == tk.NORMAL else state)
        self.refresh_btn.config(state=state)

    # ProcessingObserver implementation
    def on_start(self, total_files):
        """Called when processing starts."""
        self.processed_files = 0
        self.total_files = total_files

    def on_file_complete(self, file, result, success, message=""):
        """Called when a file is processed."""
        # Update results treeview
        if success:
            self.results_tree.insert(
                "",
                tk.END,
                values=(
                    os.path.basename(file),
                    os.path.basename(result) if result else "",
                    "Success",
                ),
            )
        else:
            self.results_tree.insert(
                "", tk.END, values=(os.path.basename(file), "", f"Error: {message}")
            )

        # Update progress
        self.processed_files += 1
        progress_percent = (self.processed_files / self.total_files) * 100
        self.progress_var.set(progress_percent)
        self.progress_percent_var.set(f"{int(progress_percent)}%")
        self.status_var.set(
            f"Processed {self.processed_files} of {self.total_files} files"
        )
        self.update()

    def on_complete(self):
        """Called when all processing is complete."""
        self.progress_var.set(100)
        self.progress_percent_var.set("100%")
        self.status_var.set(f"Processed {self.total_files} files")

        # Re-enable buttons
        self._set_controls_state(tk.NORMAL)

        # Show completion message
        messagebox.showinfo(
            "Processing Complete", f"Processed {self.total_files} files."
        )

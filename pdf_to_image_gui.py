import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz
from pdf_to_image import convert_pdf, parse_pages


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Image Converter")
        self.root.resizable(False, False)

        self._running = False
        self._progress_val = 0
        self._progress_max = 1
        self._input_widgets = []

        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        # --- input file ---
        ttk.Label(main, text="Input PDF").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(main, textvariable=self.input_var, width=50)
        self.input_entry.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        self.input_entry.bind("<KeyRelease>", self._on_input_changed)
        self._input_widgets.append(self.input_entry)
        ttk.Button(main, text="Browse", command=self._browse_input).grid(row=1, column=1)

        # --- output dir ---
        ttk.Label(main, text="Output Folder").grid(row=2, column=0, sticky="w", pady=(8, 2))
        self.output_var = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
        self.output_entry = ttk.Entry(main, textvariable=self.output_var, width=50)
        self.output_entry.grid(row=3, column=0, sticky="ew", padx=(0, 4))
        self._input_widgets.append(self.output_entry)
        ttk.Button(main, text="Browse", command=self._browse_output).grid(row=3, column=1)

        # --- height + width ---
        ttk.Label(main, text="Size (px)  —  leave empty for auto").grid(
            row=4, column=0, sticky="w", pady=(8, 2))
        sf = ttk.Frame(main)
        sf.grid(row=5, column=0, columnspan=2, sticky="ew")
        ttk.Label(sf, text="Width").pack(side="left")
        self.width_var = tk.StringVar()
        self.width_entry = ttk.Entry(sf, textvariable=self.width_var, width=7)
        self.width_entry.pack(side="left", padx=(2, 0))
        self._input_widgets.append(self.width_entry)
        ttk.Label(sf, text="Height").pack(side="left", padx=(12, 2))
        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(sf, textvariable=self.height_var, width=7)
        self.height_entry.pack(side="left", padx=(2, 0))
        self._input_widgets.append(self.height_entry)

        # --- pages ---
        ttk.Label(main, text="Pages  —  e.g. 1-3 or 1,2,5, empty = all").grid(
            row=6, column=0, sticky="w", pady=(8, 2))
        self.pages_var = tk.StringVar()
        self.pages_entry = ttk.Entry(main, textvariable=self.pages_var, width=20)
        self.pages_entry.grid(row=7, column=0, sticky="w")
        self._input_widgets.append(self.pages_entry)

        # --- quality ---
        ttk.Label(main, text="Quality").grid(row=8, column=0, sticky="w", pady=(8, 2))
        qf = ttk.Frame(main)
        qf.grid(row=9, column=0, columnspan=2, sticky="ew")
        self.quality_var = tk.IntVar(value=85)
        self.quality_scale = ttk.Scale(
            qf, from_=1, to=100, variable=self.quality_var, orient="horizontal",
            command=self._on_quality_changed
        )
        self.quality_scale.pack(side="left", fill="x", expand=True)
        self.quality_label = ttk.Label(qf, text="85", width=3, anchor="e")
        self.quality_label.pack(side="left", padx=(6, 0))
        self._input_widgets.append(self.quality_scale)

        # --- format + prefix ---
        ttk.Label(main, text="Output").grid(row=10, column=0, sticky="w", pady=(8, 2))
        of = ttk.Frame(main)
        of.grid(row=11, column=0, columnspan=2, sticky="ew")
        self.format_var = tk.StringVar(value="jpg")
        format_combo = ttk.Combobox(
            of, textvariable=self.format_var, values=["jpg", "png"],
            state="readonly", width=6
        )
        format_combo.pack(side="left")
        self._input_widgets.append(format_combo)
        ttk.Label(of, text="File Name Prefix").pack(side="left", padx=(16, 4))
        self.prefix_var = tk.StringVar(value="page")
        self.prefix_entry = ttk.Entry(of, textvariable=self.prefix_var, width=12)
        self.prefix_entry.pack(side="left")
        self._input_widgets.append(self.prefix_entry)
        self.compress_var = tk.BooleanVar(value=False)
        self.compress_cb = ttk.Checkbutton(of, text="Compress", variable=self.compress_var)
        self.compress_cb.pack(side="left", padx=(12, 0))
        self._input_widgets.append(self.compress_cb)

        # --- convert button ---
        self.convert_btn = ttk.Button(main, text="Convert", command=self._start_conversion)
        self.convert_btn.grid(row=12, column=0, columnspan=2, pady=(16, 8), sticky="ew")
        self.convert_btn.config(state="disabled")

        # --- progress bar ---
        self.progress = ttk.Progressbar(main, mode="determinate", maximum=1)
        self.progress.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        # --- status ---
        self.status_var = tk.StringVar(value="Select a PDF to begin.")
        self.status_label = ttk.Label(main, textvariable=self.status_var, foreground="gray")
        self.status_label.grid(row=14, column=0, columnspan=2, sticky="w")

        self._poll_progress()

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Select PDF", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if path:
            self.input_var.set(path)
            self._on_input_changed()

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_var.set(path)

    def _on_input_changed(self, *_):
        if os.path.isfile(self.input_var.get()):
            self.convert_btn.config(state="normal")
        else:
            self.convert_btn.config(state="disabled")

    def _on_quality_changed(self, *_):
        self.quality_label.config(text=str(self.quality_var.get()))

    @staticmethod
    def _parse_int_or_none(s):
        s = s.strip()
        if not s:
            return None
        return int(s)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    def _start_conversion(self):
        input_path = self.input_var.get()
        if not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return

        try:
            height = self._parse_int_or_none(self.height_var.get())
            width = self._parse_int_or_none(self.width_var.get())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be integers or empty.")
            return

        pages_raw = self.pages_var.get()
        try:
            page_list = parse_pages(pages_raw)
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid page format. Use e.g. 1-3 or 1,2,5")
            return

        fmt = self.format_var.get()
        quality = self.quality_var.get()
        prefix = self.prefix_var.get().strip()
        if not prefix:
            prefix = "page"
        compress = self.compress_var.get()
        output_dir = self.output_var.get()

        # Pre-count pages for progress bar
        doc = fitz.open(input_path)
        all_count = len(doc)
        if page_list:
            page_list = [p for p in page_list if 1 <= p <= all_count]
            if not page_list:
                doc.close()
                messagebox.showerror("Error", "No valid pages selected (out of range).")
                return
            total = len(page_list)
        else:
            total = all_count
        doc.close()

        self._progress_val = 0
        self._progress_max = total
        self.progress.config(maximum=total, value=0)
        self._set_running(True)

        thread = threading.Thread(
            target=self._run_conversion,
            args=(input_path, output_dir, fmt, quality, prefix,
                  height, width, page_list, compress),
            daemon=True
        )
        thread.start()

    def _run_conversion(self, input_path, output_dir, fmt, quality, prefix,
                        height, width, page_list, compress):
        try:
            out_paths = convert_pdf(
                input_path, output_dir, fmt, quality, prefix,
                height=height, width=width, pages=page_list,
                compress=compress,
                progress_callback=lambda cur, tot: setattr(self, "_progress_val", cur)
            )
            self._progress_val = ("ok", out_paths)
        except Exception as exc:
            self._progress_val = ("error", str(exc))

    def _set_running(self, running):
        self._running = running
        state = "disabled" if running else "normal"
        self.convert_btn.config(state=state, text="Converting..." if running else "Convert")
        for w in self._input_widgets:
            w.config(state=state)
        self.status_label.config(foreground="black" if running else "gray")

    def _poll_progress(self):
        if self._running:
            val = self._progress_val
            if isinstance(val, tuple):
                self._set_running(False)
                self.progress.config(value=self._progress_max)
                status, payload = val
                if status == "error":
                    self.status_var.set(f"Error: {payload}")
                    self.status_label.config(foreground="red")
                else:
                    out_paths = payload
                    first = os.path.dirname(out_paths[0]) if out_paths else ""
                    self.status_var.set(
                        f"Done — {len(out_paths)} page(s) saved to {first}"
                    )
                    self.status_label.config(foreground="green")
            else:
                self.progress.config(value=val)
                self.status_var.set(f"Converting page {val} of {self._progress_max}...")

        self.root.after(100, self._poll_progress)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

# ui_ttk.py
import asyncio
import io
import os
import threading
import queue
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, simpledialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from dateutil import parser as date_parser

from .core import TGWCCore, logger

try:
    import win32clipboard

    HAVE_WIN_CLIPBOARD = True
except ImportError:
    HAVE_WIN_CLIPBOARD = False

APP_TITLE = "TelegramWordCloud — Modern UI"
VERSION = "1.2.0"   # UI-only bump; your logic/versioning can stay as-is
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
STOPWORDS_PATH = PROJECT_ROOT / "stopwords.txt"
THEME_PATH = PROJECT_ROOT / "themes" / "forest-light" / "forest-light.tcl"


class CancelledError(Exception):
    """Raised when the user cancels a running job."""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        if THEME_PATH.exists():
            try:
                self.tk.call("source", str(THEME_PATH))
                ttk.Style().theme_use("forest-light")
            except tk.TclError as exc:
                logger.warning("Unable to load Forest theme (%s); falling back to default.", exc)
        self.title(APP_TITLE)
        self.minsize(980, 640)
        self.core = TGWCCore()
        self.log_queue = queue.Queue()
        self.last_wordcloud_image = None
        self.cancel_event = threading.Event()
        self.current_thread = None
        self._build_styles()
        self._build_layout()
        self._load_env()
        self._pump_log_queue()

    # ---------- UI Structure ----------
    def _build_styles(self):
        self.style = ttk.Style(self)
        # use a built-in theme for consistency across platforms
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    def _build_layout(self):
        # Top header
        header = ttk.Frame(self, padding=(12, 8))
        header.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(header, text="TelegramWordCloud", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text=f" v{VERSION}", foreground="#666").pack(side=tk.LEFT, padx=(4, 0))

        # Body: left controls (Notebook) + right preview
        body = ttk.Frame(self, padding=8)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.nb = ttk.Notebook(body)
        self.nb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self._build_csv_tab()
        self._build_telethon_tab()

        right = ttk.Frame(body)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Preview (Matplotlib)
        preview_group = ttk.LabelFrame(right, text="Preview")
        preview_group.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("off")
        self.canvas = FigureCanvasTkAgg(self.fig, master=preview_group)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._build_preview_menu()

        # Console
        console_group = ttk.LabelFrame(right, text="Log")
        console_group.pack(side=tk.TOP, fill=tk.BOTH, expand=False, pady=(8, 0))
        self.console = tk.Text(console_group, height=8, wrap="word", state="disabled")
        self.console.pack(fill=tk.BOTH, expand=True)
        self._log("UI started.")

        # Bottom bar
        bottom = ttk.Frame(self, padding=(8, 8))
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress = ttk.Progressbar(bottom, mode="indeterminate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.status = ttk.Label(bottom, text="Ready")
        self.status.pack(side=tk.LEFT)

        # Top command bar
        cmd = ttk.Frame(self, padding=(8, 0))
        cmd.pack(side=tk.TOP, fill=tk.X)
        self.run_button = ttk.Button(cmd, text="Run", command=self.on_run, width=12)
        self.run_button.pack(side=tk.LEFT)
        ttk.Button(cmd, text="Help", command=self.on_help).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(cmd, text="Edit stopwords", command=self.on_edit_stopwords).pack(side=tk.LEFT, padx=(8, 0))
        self.cancel_button = ttk.Button(cmd, text="Cancel", command=self.on_cancel, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))

    def _build_csv_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="CSV/JSON")
        self.csv_tab = tab

        # Inputs
        frm = ttk.LabelFrame(tab, text="Local export")
        frm.pack(fill=tk.X)
        self.csv_path = tk.StringVar()
        self.json_path = tk.StringVar()
        self.csv_mode = tk.StringVar(value="csv")

        mode_row = ttk.Frame(frm)
        mode_row.pack(fill=tk.X, padx=6, pady=(6, 0))
        ttk.Label(mode_row, text="Source type:").pack(side=tk.LEFT)
        ttk.Radiobutton(
            mode_row, text="CSV export", value="csv", variable=self.csv_mode, command=self._update_csv_inputs
        ).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Radiobutton(
            mode_row, text="Telegram JSON (result.json)", value="json", variable=self.csv_mode, command=self._update_csv_inputs
        ).pack(side=tk.LEFT, padx=(6, 0))

        row_csv = ttk.Frame(frm)
        row_csv.pack(fill=tk.X, padx=6, pady=(6, 3))
        ttk.Label(row_csv, text="CSV path:").pack(side=tk.LEFT)
        self.csv_entry = ttk.Entry(row_csv, textvariable=self.csv_path, width=50)
        self.csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.csv_browse = ttk.Button(row_csv, text="Browse", command=self._pick_csv)
        self.csv_browse.pack(side=tk.LEFT)

        row_json = ttk.Frame(frm)
        row_json.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Label(row_json, text="JSON path:").pack(side=tk.LEFT)
        self.json_entry = ttk.Entry(row_json, textvariable=self.json_path, width=50, state="disabled")
        self.json_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.json_browse = ttk.Button(row_json, text="Browse", command=self._pick_json, state="disabled")
        self.json_browse.pack(side=tk.LEFT)

        out = ttk.LabelFrame(tab, text="Output")
        out.pack(fill=tk.X, pady=(8, 0))
        self.out_dir = tk.StringVar(value=os.getcwd())
        row = ttk.Frame(out); row.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(row, text="Save images/messages to:").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.out_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row, text="Browse", command=self._pick_out_dir).pack(side=tk.LEFT)

        opts = ttk.LabelFrame(tab, text="Processing options")
        opts.pack(fill=tk.X, pady=(8, 0))
        self.save_image = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Save wordcloud image", variable=self.save_image).pack(anchor="w", padx=6, pady=6)
        self._update_csv_inputs()

    def _build_telethon_tab(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Telethon")

        creds = ttk.LabelFrame(tab, text="Credentials")
        creds.pack(fill=tk.X)
        self.api_id = tk.StringVar()
        self.api_hash = tk.StringVar()
        self.phone = tk.StringVar()

        r = ttk.Frame(creds); r.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(r, text="API ID:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Entry(r, textvariable=self.api_id, width=24).pack(side=tk.LEFT)

        r = ttk.Frame(creds); r.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(r, text="API Hash:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Entry(r, textvariable=self.api_hash, width=32, show="*").pack(side=tk.LEFT)
        ttk.Button(r, text="Save to .env", command=self.on_save_env).pack(side=tk.LEFT, padx=(8, 0))

        r = ttk.Frame(creds); r.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(r, text="Phone (+countrycode):").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Entry(r, textvariable=self.phone, width=24).pack(side=tk.LEFT)

        chan = ttk.LabelFrame(tab, text="Channel & Output")
        chan.pack(fill=tk.X, pady=(8, 0))
        self.channel = tk.StringVar()
        r = ttk.Frame(chan); r.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(r, text="Channel username or invite link:").pack(side=tk.LEFT)
        ttk.Entry(r, textvariable=self.channel, width=42).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        r = ttk.Frame(chan); r.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(r, text="Save images/messages to:").pack(side=tk.LEFT)
        ttk.Entry(r, textvariable=self.out_dir, width=50).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        ttk.Button(r, text="Browse", command=self._pick_out_dir).pack(side=tk.LEFT)

        opts = ttk.LabelFrame(tab, text="Processing options")
        opts.pack(fill=tk.X, pady=(8, 0))
        self.download_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Download channel messages only (skip wordcloud)",
                        variable=self.download_only).pack(anchor="w", padx=6, pady=6)
        ttk.Checkbutton(opts, text="Save wordcloud image", variable=self.save_image).pack(anchor="w", padx=6, pady=(0,6))

        range_frame = ttk.LabelFrame(tab, text="Download scope")
        range_frame.pack(fill=tk.X, pady=(8, 0))
        self.download_mode = tk.StringVar(value="all")
        modes = ttk.Frame(range_frame)
        modes.pack(fill=tk.X, padx=6, pady=4)
        ttk.Radiobutton(modes, text="All posts", variable=self.download_mode, value="all",
                        command=self._update_date_widgets).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(modes, text="Date range", variable=self.download_mode, value="range",
                        command=self._update_date_widgets).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(modes, text="Last N posts", variable=self.download_mode, value="last",
                        command=self._update_date_widgets).pack(side=tk.LEFT)

        self.date_frame = ttk.Frame(range_frame)
        self.date_frame.pack(fill=tk.X, padx=6, pady=(4, 0))
        ttk.Label(self.date_frame, text="From (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        self.date_from = tk.StringVar()
        ttk.Entry(self.date_frame, textvariable=self.date_from, width=18).grid(row=0, column=1, padx=4, pady=2, sticky="w")
        ttk.Label(self.date_frame, text="To (YYYY-MM-DD):").grid(row=0, column=2, sticky="w")
        self.date_to = tk.StringVar()
        ttk.Entry(self.date_frame, textvariable=self.date_to, width=18).grid(row=0, column=3, padx=4, pady=2, sticky="w")

        self.last_frame = ttk.Frame(range_frame)
        self.last_frame.pack(fill=tk.X, padx=6, pady=(4, 6))
        ttk.Label(self.last_frame, text="Last N posts:").grid(row=0, column=0, sticky="w")
        self.last_n = tk.StringVar()
        ttk.Entry(self.last_frame, textvariable=self.last_n, width=10).grid(row=0, column=1, padx=4, pady=2, sticky="w")

        self._update_date_widgets()

        ttk.Label(tab, text="Note: Telethon required; get API ID/hash at my.telegram.org").pack(anchor="w", padx=6, pady=(8,0))

    # ---------- Event handlers ----------
    def _build_preview_menu(self):
        self.preview_menu = tk.Menu(self, tearoff=0)
        self.preview_menu.add_command(label="Copy image to clipboard", command=self.copy_preview_to_clipboard)
        self.preview_menu.add_command(label="Save image as...", command=self.save_preview_as)
        widget = self.canvas.get_tk_widget()
        widget.bind("<Button-3>", self._show_preview_menu)
        widget.bind("<Control-Button-1>", self._show_preview_menu)

    def _show_preview_menu(self, event):
        try:
            self.preview_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.preview_menu.grab_release()

    def _pick_csv(self):
        path = filedialog.askopenfilename(
            title="Select Telegram export CSV",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if path:
            self.csv_path.set(path)

    def _pick_json(self):
        path = filedialog.askopenfilename(
            title="Select Telegram export JSON (result.json)",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if path:
            self.json_path.set(path)

    def copy_preview_to_clipboard(self):
        if not self.last_wordcloud_image:
            messagebox.showinfo("TelegramWordCloud", "Generate a word cloud first.")
            return
        if not HAVE_WIN_CLIPBOARD:
            messagebox.showerror("TelegramWordCloud", "Image clipboard copy is only supported on Windows with pywin32 installed.")
            return
        try:
            output = io.BytesIO()
            self.last_wordcloud_image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            self._log("Copied preview image to clipboard.")
        except CancelledError:
            self._set_status("Cancelled.")
            self._log("Operation cancelled by user.")
        except Exception as exc:
            win32clipboard.CloseClipboard()
            messagebox.showerror("TelegramWordCloud", f"Unable to copy image to clipboard: {exc}")

    def save_preview_as(self):
        if not self.last_wordcloud_image:
            messagebox.showinfo("TelegramWordCloud", "Generate a word cloud first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save image as...",
            defaultextension=".png",
            filetypes=(
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("All files", "*.*"),
            ),
        )
        if not path:
            return
        try:
            self.last_wordcloud_image.save(path)
            self._log(f"Saved preview image -> {path}")
        except Exception as exc:
            messagebox.showerror("TelegramWordCloud", f"Unable to save image: {exc}")

    def _update_csv_inputs(self):
        json_mode = self.csv_mode.get() == "json"
        csv_state = "disabled" if json_mode else "normal"
        json_state = "normal" if json_mode else "disabled"
        self.csv_entry.configure(state=csv_state)
        self.csv_browse.configure(state=csv_state)
        self.json_entry.configure(state=json_state)
        self.json_browse.configure(state=json_state)

    def _pick_out_dir(self):
        d = filedialog.askdirectory(title="Select output directory", initialdir=self.out_dir.get())
        if d:
            self.out_dir.set(d)

    def _update_date_widgets(self):
        mode = self.download_mode.get()
        state_range = "normal" if mode == "range" else "disabled"
        for child in self.date_frame.winfo_children():
            child.configure(state=state_range)

        state_last = "normal" if mode == "last" else "disabled"
        for child in self.last_frame.winfo_children():
            child.configure(state=state_last)

    def on_cancel(self):
        if not self.current_thread or not self.current_thread.is_alive():
            return
        self.cancel_event.set()
        self.cancel_button.config(state="disabled")
        self._set_status("Cancelling...")
        self._log("Cancellation requested...")

    def _load_env(self):
        creds = self.core.read_env_credentials()
        if creds:
            self.api_id.set(creds.get("TELEGRAM_API_ID", ""))
            self.api_hash.set(creds.get("TELEGRAM_API_HASH", ""))
            self.phone.set(creds.get("TELEGRAM_PHONE", ""))
            self._log("Loaded credentials from .env.")
        else:
            self._log("No .env found.")

    def on_save_env(self):
        aid, ah, ph = self.api_id.get().strip(), self.api_hash.get().strip(), self.phone.get().strip()
        if not (aid and ah and ph):
            messagebox.showerror("TelegramWordCloud", "Enter API ID, API hash, and phone number before saving.")
            return
        try:
            self.core.write_env_credentials({
                "TELEGRAM_API_ID": aid, "TELEGRAM_API_HASH": ah, "TELEGRAM_PHONE": ph
            })
        except OSError as exc:
            self._log(f"Saving credentials failed: {exc}")
            messagebox.showerror("TelegramWordCloud", str(exc))
            return
        self._log("Credentials saved to .env.")
        messagebox.showinfo("TelegramWordCloud", "Credentials saved to .env.")

    def on_help(self):
        txt = "help.txt could not be found."
        try:
            with open("help.txt", "r", encoding="utf-8") as f:
                txt = f.read()
        except FileNotFoundError:
            pass
        messagebox.showinfo("Help", txt)

    def on_edit_stopwords(self):
        path = STOPWORDS_PATH
        if not path.exists():
            with path.open("w", encoding="utf-8") as f:
                f.write("")
        editor = tk.Toplevel(self)
        editor.title("Edit stopwords.txt")
        txt = tk.Text(editor, wrap="word")
        txt.pack(fill=tk.BOTH, expand=True)
        with path.open("r", encoding="utf-8") as f:
            txt.insert("1.0", f.read())

        def save():
            with path.open("w", encoding="utf-8") as f:
                f.write(txt.get("1.0", "end-1c"))
            self._log("stopwords.txt saved.")
            editor.destroy()

        ttk.Button(editor, text="Save", command=save).pack(pady=6)

    def on_run(self):
        selected_id = self.nb.select()
        tab_text = self.nb.tab(selected_id, "text")
        if tab_text == "CSV/JSON" or selected_id == str(getattr(self, "csv_tab", "")):
            if self.csv_mode.get() == "json":
                source = self.json_path.get().strip()
                if not source:
                    messagebox.showerror("TelegramWordCloud", "Select a Telegram JSON export (result.json) first.")
                    return
            else:
                source = self.csv_path.get().strip()
                if not source:
                    messagebox.showerror("TelegramWordCloud", "Select a CSV export file first.")
                    return
            args = ("csv", self.csv_mode.get(), source, self.out_dir.get().strip(), self.save_image.get())
        else:
            channel_value = self.channel.get().strip()
            if not channel_value:
                messagebox.showerror("TelegramWordCloud", "Enter the channel username or invite link before running.")
                self._log("Error: channel username/invite is required.")
                return
            args = ("telethon",
                    self.api_id.get().strip(),
                    self.api_hash.get().strip(),
                    self.phone.get().strip(),
                    channel_value,
                    self.out_dir.get().strip(),
                    self.download_only.get(),
                    self.save_image.get(),
                    self.download_mode.get(),
                    self.date_from.get().strip(),
                    self.date_to.get().strip(),
                    self.last_n.get().strip())
        self._run_background(args)

    # ---------- Worker thread ----------
    def _run_background(self, args_tuple):
        self.progress.config(mode="indeterminate")
        self.progress["value"] = 0
        self.progress.start(10)
        self.status.config(text="Working...")
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showinfo("TelegramWordCloud", "A job is already running. Cancel it before starting another.")
            return
        self.cancel_event.clear()
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        t = threading.Thread(target=self._worker, args=(args_tuple,), daemon=True)
        t.start()
        self.current_thread = t

    def _call_on_main_thread(self, func, *args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            return func(*args, **kwargs)
        result = queue.Queue(maxsize=1)

        def wrapper():
            try:
                result.put((True, func(*args, **kwargs)))
            except Exception as exc:
                result.put((False, exc))

        self.after(0, wrapper)
        success, payload = result.get()
        if success:
            return payload
        raise payload

    def _worker(self, args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            mode = args[0]
            if mode == "csv":
                _, file_format, source_path, out_dir, save_img = args
                if file_format == "json":
                    self._log("Reading JSON export...")
                    df = self.core.load_json_export(source_path)
                else:
                    self._log("Reading CSV...")
                    df = self.core.load_csv(source_path)
                self._raise_if_cancelled()
                tokens = self.core.flatten_text_columns(df)
                if not tokens:
                    raise ValueError("No text messages were found to process.")
                stop = self.core.load_stopwords(str(STOPWORDS_PATH))
                self._raise_if_cancelled()
                self._log("Generating word cloud...")
                wc = self.core.build_wordcloud(tokens, stop)
                self._render_cloud(wc)
                if save_img:
                    out = self.core.ensure_dir(out_dir)
                    self._raise_if_cancelled()
                    fn = self.core.save_wordcloud_image(wc, out)
                    self._log(f"Saved image -> {fn}")
                else:
                    self._log("Preview only (not saved).")

            elif mode == "telethon":
                _, aid, ah, ph, channel, out_dir, dl_only, save_img, scope_mode, scope_from, scope_to, scope_last = args
                if not (aid and ah and ph):
                    raise ValueError("Enter API ID, API hash, and phone number before running Telethon downloads.")
                try:
                    aid_int = int(aid)
                except ValueError as exc:
                    raise ValueError("Enter a numeric API ID.") from exc
                def code_provider(two_factor=False):
                    prompt = "Enter your Telegram 2FA password:" if two_factor else "Enter the verification code Telegram sent to your phone:"
                    kwargs = {"parent": self}
                    if two_factor:
                        kwargs["show"] = "*"
                    return self._call_on_main_thread(simpledialog.askstring, "Telegram", prompt, **kwargs)

                def progress_callback(done, total):
                    if self.cancel_event.is_set():
                        raise CancelledError()
                    self._update_download_progress(done, total)
                date_from = date_to = None
                last_n = None
                if scope_mode == "range":
                    date_from = self._parse_date(scope_from)
                    date_to = self._parse_date(scope_to)
                elif scope_mode == "last":
                    try:
                        last_n = int(scope_last)
                    except ValueError:
                        raise ValueError("Enter a numeric value for last N posts.")
                self._raise_if_cancelled()
                self._log("Downloading channel messages...")
                df = self.core.download_channel(
                    aid_int,
                    ah,
                    ph,
                    channel,
                    code_provider,
                    progress_callback=progress_callback,
                    date_from=date_from,
                    date_to=date_to,
                    last_n=last_n,
                )
                self._raise_if_cancelled()
                export_dir = self.core.build_export_dir(out_dir, channel)
                csv_fn = self.core.save_messages_csv(df, str(export_dir), channel, filename="messages.csv")
                self._log(f"Exported messages -> {csv_fn}")
                if not dl_only:
                    tokens = self.core.flatten_text_columns(df)
                    stop = self.core.load_stopwords(str(STOPWORDS_PATH))
                    self._raise_if_cancelled()
                    self._log("Generating word cloud...")
                    wc = self.core.build_wordcloud(tokens, stop)
                    self._render_cloud(wc)
                    if save_img:
                        self._raise_if_cancelled()
                        img_fn = self.core.save_wordcloud_image(wc, str(export_dir), filename="wordcloud.jpg")
                        self._log(f"Saved image -> {img_fn}")
                else:
                    self._log("Download-only mode (no word cloud).")
            else:
                raise ValueError("Unknown mode.")
            self._set_status("Done.")
        except Exception as exc:
            self._set_status("Error.")
            self._log(f"Error: {exc}")
            logger.exception("Worker error: %s", exc)
            self._call_on_main_thread(messagebox.showerror, "TelegramWordCloud", str(exc))
        finally:
            loop.close()
            self.after(0, self._reset_progress_bar)
            self.after(0, self._finalize_worker)

    # ---------- UI helpers ----------
    def _render_cloud(self, wc):
        def draw():
            self.ax.clear()
            self.ax.axis("off")
            self.ax.imshow(wc, interpolation="bilinear")
            self.canvas.draw_idle()
        self.last_wordcloud_image = wc.to_image()
        self.after(0, draw)

    def _set_status(self, text):
        self.after(0, lambda: self.status.config(text=text))

    def _update_download_progress(self, processed, total):
        def update():
            if total and total > 0:
                self.progress.stop()
                self.progress.config(mode="determinate", maximum=total)
                self.progress["value"] = min(processed, total)
                self.status.config(text=f"Downloading... {processed}/{total}")
            else:
                if self.progress["mode"] != "indeterminate":
                    self.progress.config(mode="indeterminate")
                    self.progress.start(10)
                self.status.config(text=f"Downloading... {processed}")
        self.after(0, update)

    def _reset_progress_bar(self):
        self.progress.stop()
        self.progress.config(mode="indeterminate")
        self.progress["value"] = 0

    def _finalize_worker(self):
        self.current_thread = None
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")

    def _raise_if_cancelled(self):
        if self.cancel_event.is_set():
            raise CancelledError()

    def _parse_date(self, value: str):
        value = value.strip()
        if not value:
            return None
        try:
            return date_parser.parse(value)
        except (ValueError, TypeError):
            raise ValueError(f"Could not parse date '{value}'. Use YYYY-MM-DD format.")

    def _log(self, msg: str):
        self.log_queue.put(msg)

    def _pump_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                logger.info(msg)
                self.console.configure(state="normal")
                self.console.insert("end", msg + "\n")
                self.console.configure(state="disabled")
                self.console.see("end")
        except queue.Empty:
            pass
        self.after(120, self._pump_log_queue)


def run_app():
    App().mainloop()


if __name__ == "__main__":
    run_app()

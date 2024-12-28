""" HytekValidate Main Screen """

import os
import logging
import customtkinter as ctk  # type: ignore
import webbrowser
import tkinter as tk
from tkinter import filedialog, BooleanVar, StringVar, HORIZONTAL
from typing import Any
from platformdirs import user_config_dir
from swimrankings import SwimRankings
from sign_config import verify_config
import pathlib

# Appliction Specific Imports
from config import appConfig
from version import APP_VERSION, ADMIN_MODE
from hytekvalidate_core import HyTekValidateTimes
from hytekvalidate_config import generate_meet_config, verify_meet_config

tkContainer = Any


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state="normal")
            self.text.insert(tk.END, msg + "\n")
            self.text.configure(state="disabled")
            # Autoscroll to the bottom
            self.text.yview(tk.END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class _Entry_Validation_Tab(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    """Entry Validation"""

    def __init__(self, container: tkContainer, config: appConfig):
        super().__init__(container)
        self._config = config

        self._hytek_db = StringVar(value=self._config.get_str("hytek_db"))
        self._ev3_file = StringVar(value=self._config.get_str("ev3_file"))
        self._meet_config_file = StringVar(value=self._config.get_str("meet_config_file"))
        self._report_file = StringVar(value=self._config.get_str("report_file"))
        self._opt_ignore_existing_bonus = BooleanVar(value=self._config.get_bool("opt_ignore_existing_bonus"))
        self._opt_ignore_cache = BooleanVar(value=self._config.get_bool("opt_ignore_cache"))
        self._opt_allow_2_percent = BooleanVar(value=self._config.get_bool("opt_allow_2_percent"))

        self._swimrankings = SwimRankings()

        # self is a vertical container that will contain 3 frames
        self.columnconfigure(0, weight=1)
        # Options Frame - Left and Right Panels

        optionsframe = ctk.CTkFrame(self)
        optionsframe.grid(column=0, row=2, sticky="news")

        filesframe = ctk.CTkFrame(optionsframe)
        filesframe.grid(column=0, row=0, sticky="new", padx=10, pady=10)
        filesframe.rowconfigure(0, weight=1)
        filesframe.rowconfigure(1, weight=1)
        filesframe.rowconfigure(2, weight=1)

        right_optionsframe = ctk.CTkFrame(optionsframe)
        right_optionsframe.grid(column=1, row=0, sticky="new", padx=10, pady=10)
        right_optionsframe.rowconfigure(0, weight=1)

        buttonsframe = ctk.CTkFrame(self)
        buttonsframe.grid(column=0, row=4, sticky="news", padx=10, pady=10)
        buttonsframe.rowconfigure(0, weight=0)

        cacheframe = ctk.CTkFrame(self)
        cacheframe.grid(column=0, row=6, sticky="news", padx=10, pady=10)
        cacheframe.rowconfigure(0, weight=0)

        # Files Section
        ctk.CTkLabel(filesframe, text="Files").grid(column=0, row=0, sticky="w", padx=10)

        btn1 = ctk.CTkButton(filesframe, text="Database", command=self._handle_hytek_db_browse)
        btn1.grid(column=0, row=1, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._hytek_db).grid(column=1, row=1, sticky="w", padx=(0, 10))

        if ADMIN_MODE == True:
            btn2 = ctk.CTkButton(filesframe, text="EV3 File", command=self._handle_ev3_file_browse)
            btn2.grid(column=0, row=2, padx=20, pady=10)
            ctk.CTkLabel(filesframe, textvariable=self._ev3_file).grid(column=1, row=2, sticky="w", padx=(0, 10))

        btn3 = ctk.CTkButton(filesframe, text="Meet Config File", command=self._handle_meet_config_file_browse)
        btn3.grid(column=0, row=3, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._meet_config_file).grid(column=1, row=3, sticky="w", padx=(0, 10))

        btn4 = ctk.CTkButton(filesframe, text="Report File", command=self._handle_report_file_browse)
        btn4.grid(column=0, row=4, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._report_file).grid(column=1, row=4, sticky="w", padx=(0, 10))

        # Right options frame for status options

        ctk.CTkLabel(right_optionsframe, text="Program Options").grid(column=0, row=0, sticky="nw", padx=10)


        ctk.CTkSwitch(
            right_optionsframe,
            text="Allow 2% Time Conversion",
            variable=self._opt_allow_2_percent,
            onvalue=True,
            offvalue=False,
            command=self._handle_opt_allow_2_percent,
        ).grid(column=0, row=2, sticky="w", padx=20, pady=10)

        # Add Command Buttons

        ctk.CTkLabel(buttonsframe, text="Report Generation").grid(column=0, row=0, sticky="w", padx=10, pady=10)

        self.qb_report_btn = ctk.CTkButton(buttonsframe, text="Time Validation", command=self._handle_reports_btn)
        self.qb_report_btn.grid(column=0, row=1, sticky="news", padx=20, pady=10)

        if ADMIN_MODE == True:  
            self.meet_config_btn = ctk.CTkButton(
                buttonsframe, text="Generate Config File", command=self._handle_generate_config_btn
            )   
            self.meet_config_btn.grid(column=1, row=1, sticky="news", padx=20, pady=10)

        # Add Cache Control Buttons (Clear current meet, Clear all meets, Reset Cache)
        ctk.CTkLabel(cacheframe, text="Swim Rankings Cache Control").grid(column=0, row=0, sticky="w", padx=10, pady=10)
        self.clear_current_best_times_btn = ctk.CTkButton(cacheframe, text="Clear Current Best Times", command=self._handle_clear_current_meet)
        self.clear_current_best_times_btn.grid(column=0, row=1, sticky="w", padx=10, pady=10)
        self.clear_all_best_times_btn = ctk.CTkButton(cacheframe, text="Clear All Best Times", command=self._handle_clear_all_meets)
        self.clear_all_best_times_btn.grid(column=1, row=1, sticky="w", padx=10, pady=10)
        self.reset_cache_btn = ctk.CTkButton(cacheframe, text="Reset Cache (Full)", command=self._handle_reset_cache)
        self.reset_cache_btn.grid(column=2, row=1, sticky="w", padx=10, pady=10)
        self.cache_stats_btn = ctk.CTkButton(cacheframe, text="Cache Stats", command=self._handle_cache_stats)
        self.cache_stats_btn.grid(column=3, row=1, sticky="w", padx=10, pady=10)

    def _handle_hytek_db_browse(self) -> None:
        hytek_db = filedialog.askopenfilename(
            filetypes=[("Hytek Database", "*.mdb")],
            defaultextension=".mdb",
            title="Hytek Database",
            initialfile=os.path.basename(self._hytek_db.get()),
            initialdir=os.path.dirname(self._hytek_db.get()),
        )
        if len(hytek_db) == 0:
            return
        self._config.set_str("hytek_db", hytek_db)
        self._hytek_db.set(hytek_db)

    def _handle_ev3_file_browse(self) -> None:
        ev3_file = filedialog.askopenfilename(
            filetypes=[("EV3 File", "*.ev3")],
            defaultextension=".ev3",
            title="EV3 File",
            initialfile=os.path.basename(self._ev3_file.get()),
            initialdir=os.path.dirname(self._ev3_file.get()),
        )
        if len(ev3_file) == 0:
            return
        self._config.set_str("ev3_file", ev3_file)
        self._ev3_file.set(ev3_file)

    def _handle_meet_config_file_browse(self) -> None:
        if ADMIN_MODE == False:
            meet_config_file = filedialog.askopenfilename(
                filetypes=[("Meet Config File", "*.json")],
                defaultextension=".json",
                title="Meet Config File",
                initialfile=os.path.basename(self._meet_config_file.get()),
                initialdir=os.path.dirname(self._meet_config_file.get()),
            )
        else:
            meet_config_file = filedialog.asksaveasfilename(
                filetypes=[("Meet Config File", "*.json")],
                defaultextension=".json",
                title="Meet Config File",
                initialfile="meet_config.json",
                initialdir=os.path.dirname(self._meet_config_file.get()),
            )
        if len(meet_config_file) == 0:
            return
        self._config.set_str("meet_config_file", meet_config_file)
        self._meet_config_file.set(meet_config_file)

    def _handle_report_file_browse(self) -> None:
        report_file = filedialog.asksaveasfilename(
            filetypes=[("Excel Files", "*.xlsx")],
            defaultextension=".xlsx",
            title="Report File",
            initialfile=os.path.basename(self._report_file.get()),
            initialdir=os.path.dirname(self._report_file.get()),
        )
        if len(report_file) == 0:
            return
        self._config.set_str("report_file", report_file)
        self._report_file.set(report_file)

    def _handle_opt_allow_2_percent(self, *_arg) -> None:
        self._config.set_bool("opt_allow_2_percent", self._opt_allow_2_percent.get())

    def buttons(self, newstate) -> None:
        """Enable/disable all buttons"""
        self.qb_report_btn.configure(state=newstate)
        self.clear_current_best_times_btn.configure(state=newstate)
        self.clear_all_best_times_btn.configure(state=newstate)
        self.reset_cache_btn.configure(state=newstate)
        self.cache_stats_btn.configure(state=newstate)
        if ADMIN_MODE == True:
           self.meet_config_btn.configure(state=newstate)

    def _handle_reports_btn(self) -> None:
        self.buttons("disabled")
        
        # Pass the existing SwimRankings instance to the thread
        reports_thread = HyTekValidateTimes(self._config, self._swimrankings)
        reports_thread.start()
        self.monitor_reports_thread(reports_thread)

    def _handle_generate_config_btn(self) -> None:
        self.buttons("disabled")
        meet_config = generate_meet_config(self._config)
        
        if meet_config is not None and verify_meet_config(self._config):
            logging.info("Meet configuration file generated successfully")
        else:
            logging.error("Meet configuration file generation failed")
        self.buttons("enabled")
 
    def monitor_reports_thread(self, thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitor_reports_thread(thread))
        else:
            self.buttons("enabled")
            thread.join()

    def _handle_clear_current_meet(self) -> None:
        # Load, validate and read the config file to get the meet UUID
        self.buttons("disabled")
        config_data = verify_config(self._config.get_str("meet_config_file"), "public_key.pem")
        if config_data is None:
            logging.error("Invalid configuration file")
            self.buttons("enabled")
            return
        try:
            self._swimrankings.clear_cache('meet', config_data['meet_uuid'])
        except Exception as e:
            logging.error(f"Error clearing cache: {str(e)}")
        finally:
            self.buttons("enabled")

    def _handle_clear_all_meets(self) -> None:
        self.buttons("disabled")
        self._swimrankings.clear_cache('meets')
        self.buttons("enabled")

    def _handle_reset_cache(self) -> None:
        self.buttons("disabled")
        self._swimrankings.clear_cache('all')
        self.buttons("enabled")

    def _handle_cache_stats(self) -> None:
        self.buttons("disabled")
        self._swimrankings.cache_stats()
        self.buttons("enabled")

class _Configuration_Tab(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    """Configuration Tab"""

    def __init__(self, container: tkContainer, config: appConfig):
        super().__init__(container)
        self._config = config

        self._ctk_theme = StringVar(value=self._config.get_str("Theme"))
        self._ctk_size = StringVar(value=self._config.get_str("Scaling"))
        self._ctk_colour = StringVar(value=self._config.get_str("Colour"))

        # self is a vertical container that will contain 3 frames
        self.columnconfigure(0, weight=1)

        optionsframe = ctk.CTkFrame(self)
        optionsframe.grid(column=0, row=2, sticky="news")

        # Options Frame - Left and Right Panels

        left_optionsframe = ctk.CTkFrame(optionsframe)
        left_optionsframe.grid(column=0, row=0, sticky="news", padx=10, pady=10)
        left_optionsframe.rowconfigure(0, weight=1)

        # Program Options on the left frame

        ctk.CTkLabel(left_optionsframe, text="UI Appearance").grid(column=0, row=0, sticky="w", padx=10)

        ctk.CTkLabel(left_optionsframe, text="Appearance Mode", anchor="w").grid(row=1, column=1, sticky="w")
        ctk.CTkOptionMenu(
            left_optionsframe,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
            variable=self._ctk_theme,
        ).grid(row=1, column=0, padx=20, pady=10)

        ctk.CTkLabel(left_optionsframe, text="UI Scaling", anchor="w").grid(row=2, column=1, sticky="w")
        ctk.CTkOptionMenu(
            left_optionsframe,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event,
            variable=self._ctk_size,
        ).grid(row=2, column=0, padx=20, pady=10)

        ctk.CTkLabel(left_optionsframe, text="Colour (Restart Required)", anchor="w").grid(row=3, column=1, sticky="w")
        ctk.CTkOptionMenu(
            left_optionsframe,
            values=["blue", "green", "dark-blue"],
            command=self.change_colour_event,
            variable=self._ctk_colour,
        ).grid(row=3, column=0, padx=20, pady=10)


    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self._config.set_str("Theme", new_appearance_mode)

    def change_scaling_event(self, new_scaling: str) -> None:
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        self._config.set_str("Scaling", new_scaling)

    def change_colour_event(self, new_colour: str) -> None:
        logging.info("Changing colour to : " + new_colour)
        ctk.set_default_color_theme(new_colour)
        self._config.set_str("Colour", new_colour)


class _Logging(ctk.CTkFrame):  # pylint: disable=too-many-ancestors,too-many-instance-attributes
    """Logging Window"""

    def __init__(self, container: ctk.CTk, config: appConfig):
        super().__init__(container)
        self._config = config
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)

        ctk.CTkLabel(self, text="Messages").grid(column=0, row=0, sticky="ws", padx=(10,0), pady=10)

        self.logwin = ctk.CTkTextbox(self, state="disabled")
        self.logwin.grid(column=0, row=2, sticky="new", padx=(10, 10), pady=(0, 10))
        self.logwin.configure(height=100, wrap="word")
        # Logging configuration
        userconfdir = user_config_dir("TimeValidate", "Swimming Canada")
        pathlib.Path(userconfdir).mkdir(parents=True, exist_ok=True)
        logfile = os.path.join(userconfdir, "timevalidate.log")

        logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        # Create textLogger
        text_handler = TextHandler(self.logwin)
        text_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)


class mainApp(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    """Main Appliction"""

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, container: ctk.CTk, config: appConfig):
        super().__init__(container)
        self._config = config

        self.grid(column=0, row=0, sticky="news")
        self.columnconfigure(0, weight=1)
        # Odd rows are empty filler to distribute vertical whitespace
        for i in [1, 3]:
            self.rowconfigure(i, weight=1)

        self.tabview = ctk.CTkTabview(self, width=container.winfo_width())
        self.tabview.grid(row=0, column=0, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.tabview.add("Entry Validation")
        self.tabview.add("Configuration")

        # Generate Documents Tab
        self.tabview.tab("Entry Validation").grid_columnconfigure(0, weight=1)
        self.entryValidationTab = _Entry_Validation_Tab(self.tabview.tab("Entry Validation"), self._config)
        self.entryValidationTab.grid(column=0, row=0, sticky="news")

        self.tabview.tab("Configuration").grid_columnconfigure(0, weight=1)
        self.configinfo = _Configuration_Tab(self.tabview.tab("Configuration"), self._config)
        self.configinfo.grid(column=0, row=0, sticky="news")

        # Logging Window
        loggingwin = _Logging(self, self._config)
        loggingwin.grid(column=0, row=2, padx=(20, 20), pady=(20, 0), sticky="new")

        # Info panel
        fr8 = ctk.CTkFrame(self)
        fr8.grid(column=0, row=4, sticky="news", pady=(10,0))
        fr8.rowconfigure(0, weight=1)
        fr8.columnconfigure(0, weight=1)
        link_label = ctk.CTkLabel(fr8, text="Documentation: Not likely!")
        link_label.grid(column=0, row=0, sticky="w", padx=10)
        # Custom Tkinter clickable label example https://github.com/TomSchimansky/CustomTkinter/issues/1208
        link_label.bind(
            "<Button-1>", lambda event: webbrowser.open("https://www.swimmontario.com")
        )  # link the command function
        link_label.bind("<Enter>", lambda event: link_label.configure(font=("", 13, "underline"), cursor="hand2"))
        link_label.bind("<Leave>", lambda event: link_label.configure(font=("", 13), cursor="arrow"))
        version_label = ctk.CTkLabel(fr8, text="Version " + APP_VERSION)
        version_label.grid(column=1, row=0, sticky="nes", padx=(0,10))


def main():
    """testing"""
    root = ctk.CTk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.resizable(True, True)
    options = appConfig()
    settings = mainApp(root, options)
    settings.grid(column=0, row=0, sticky="news")
    logging.info("Hello World")
    root.mainloop()


if __name__ == "__main__":
    main()

import PySimpleGUI as Gui
from pytube import YouTube
import pytube.request
import datetime
import sys
import os.path
from inc.helper import *

# Author: HishamDalal
# Publish date: 2024-02-04

# Thanks to: Sven-Bo
# --- YouTube: https://www.youtube.com/watch?v=LzCfNanQ_9c
# --- Githup: https://github.com/Sven-Bo/advanced-gui-with-usersettings-and-menubar

class YTD_Settings:
    def __init__(self, settings, parent_window):
        self.settings = settings
        self.parent_window = parent_window

        col_1_size = 13
        col_2_size = 35
        col_3_size = 8
        # default_downloads_dir = self.settings["GUI"].get("downloads_dir", '.')
        default_theme = self.settings["GUI"].get("theme", 'SystemDefaultForReal')
        theme_list = Gui.theme_list()
        theme_list.sort()

        layout = [
            # [
            #     Gui.Text(text="Downloads folder:", size=col_1_size),
            #     Gui.Input(key="-OUT-", default_text=default_downloads_dir, size=col_2_size),
            #     Gui.FolderBrowse(size=col_3_size)
            # ],
            [
                Gui.Text(text="Current theme:", size=col_1_size),
                Gui.Combo(theme_list, key="-THEME-", enable_events=True, default_value=default_theme, size=col_2_size)
            ],
            [
                Gui.Button("Save")
            ]
        ]
        window = Gui.Window("Settings", layout, modal=True)
        while True:
            event, values = window.read()
            print(event)
            if event in (Gui.WINDOW_CLOSED, "Save"):
                self.settings['GUI']['theme'] = values['-THEME-']
                Gui.theme(values['-THEME-'])
                window.refresh()
                self.parent_window.refresh()

                window.close()
                break

            elif event == "-THEME-":
                Gui.theme(values['-THEME-'])
                window.refresh()
                self.parent_window.refresh()
                Gui.popup_auto_close(values['-THEME-'], title="Test", auto_close=True, auto_close_duration=2)

class YTD:
    def __init__(self, settings):
        # progress bar chunk size
        pytube.request.default_range_size = 200000

        self.settings = settings
        # init vars
        self.title = "None"
        self.filename = "test"
        self.ext = "mp4"
        self.download_path = self.settings["GUI"]["downloads_dir"]
        self.streams = {}
        self.resource = "480"
        self.url = ""
        self.window = {}
        self.info = {}
        self.resolutions = []
        self.cancel = False
        self.type = ''
        self.use_oauth = False
        self.allow_oauth_cache = False

        Gui.theme(self.settings['GUI']['theme'])

    def layout(self):
        col_1_size = 13
        col_2_size = 35
        col_3_size = 8

        # default values
        default_downloads_dir = self.settings["GUI"].get("downloads_dir", '.')
        default_type = self.settings["GUI"].get("type", 'Video')
        default_res = self.settings["GUI"].get("resolution", '360')

        default_video = False
        default_audio = False

        if default_type == 'Audio':
            default_audio = True
        else:
            default_video = True

        layout = [
            [
                Gui.Text(text="Downloads folder:", size=col_1_size),
                Gui.Input(key="-OUT-", default_text=default_downloads_dir, size=col_2_size),
                Gui.FolderBrowse(size=col_3_size)
            ],
            [
                Gui.Text(text="Type:", size=col_1_size),
                Gui.Radio(key="-TYPE-VIDEO-", text="Video", group_id='RADIO1', default=default_video, enable_events=True),
                Gui.Radio(key="-TYPE-AUDIO-", text="Audio", group_id='RADIO1', default=default_audio, enable_events=True),

            ],
            [
                Gui.Text(text="YouTube URL:", size=col_1_size),
                Gui.Input(key="-URL-", size=col_2_size, enable_events=True),
                Gui.Button(key="-FETCH-", button_text="Fetch", size=col_3_size)
            ],
            [
                Gui.Text(text="File Info:", size=col_1_size),
                # Gui.Text('_' * int( col_2_size + col_3_size + 3) )
                # Gui.Listbox(key="-INFO-", size=(int(col_2_size-2), 4), values=[], horizontal_scroll=True),
                Gui.Multiline(key='-INFO-', size=(int(col_2_size-2), 5), horizontal_scroll=True, write_only=True)
            ],
            [
                Gui.Text(text="Resolutions:", size=col_1_size),
                Gui.Listbox(key="-RES-LIST-", values=['2160', '1440', '1080', '740', '480', '360', '240', '144'],
                            size=(int(col_2_size-2), 4), default_values=default_res, disabled=True)
            ],
            [
                Gui.Text(text="Progress:", size=col_1_size),
                Gui.ProgressBar(max_value=100, orientation='h', size=(int((col_2_size/2)+2), 26), key='-BAR-'),
                Gui.Text(key="-BAR-TXT-", text="0%", size=col_3_size)
            ],
            [
                Gui.Text("", size=col_1_size),
                Gui.Button(key="-DOWNLOAD-", button_text="Download", disabled=True), Gui.Cancel(), Gui.Button('Settings'), Gui.Exit()
            ],
        ]
        return layout

    def save_user_setting(self, values):
        # Save user inputs to config file
        self.settings["GUI"]["downloads_dir"] = values["-OUT-"]
        self.settings["GUI"]["type"] = "Audio" if values["-TYPE-AUDIO-"] else "Video"
        self.settings["GUI"]["resolution"] = values["-RES-LIST-"]

    def store_file_data(self, yt):
        self.info['title'] = yt.title
        self.info['video_id'] = yt.video_id
        # self.info['length1'] = yt.length
        self.info['length'] = str(datetime.timedelta(seconds=yt.length))
        self.info['rating'] = yt.rating
        self.info['views'] = yt.views
        self.info['publish_date'] = yt.publish_date
        self.info['author'] = yt.author
        self.info['thumbnail_url'] = yt.thumbnail_url
        self.info['description'] = yt.description

    def change_inputs_state(self, window, state=False):
        window["-INFO-"].Update(disabled=state)
        window["-RES-LIST-"].Update(disabled=state)
        window["-DOWNLOAD-"].Update(disabled=state)

    def disable_inputs(self, window):
        self.change_inputs_state(window, True)

    def enable_inputs(self, window):
        self.change_inputs_state(window, False)

    def fetch_quality(self, values):
        self.resolutions = []

        if is_valid_path(values["-OUT-"], is_dir=True) and values['-URL-']:

            yt = YouTube(values["-URL-"], on_progress_callback=self.download_progress,
                                            on_complete_callback=self.complete_progress,
                                            use_oauth=self.use_oauth,
                                            allow_oauth_cache=self.allow_oauth_cache)

            yt.register_on_progress_callback(self.download_progress)
            yt.register_on_complete_callback(self.complete_progress)

            # PyTube Can't get exception correctly
            try:
                yt.bypass_age_gate()
            except Exception as e:
                raise AgeRestrictionError(e)

            try:
                yt.check_availability()
            except Exception as e:
                raise UnavailableError(e)

            if yt.age_restricted:
                raise AgeRestrictionError("This video has age restrictions.")

            self.store_file_data(yt)

            # Get stream
            if values["-TYPE-VIDEO-"]:
                self.streams = yt.streams.filter(only_audio=False, progressive=True).desc()
                self.ext = '.mp4'

            elif values["-TYPE-AUDIO-"]:
                self.streams = yt.streams.filter(only_audio=True).desc()
                self.ext = '.mp3'

            if len(self.streams) > 0:
                # Get file info
                self.title = self.streams[0].title
                self.download_path = str(values["-OUT-"])
                # self.filename = str(slugify(self.title)) + self.ext
                self.filename = str(slugify(self.title))

                # self.info['length'] =
                # dump(self.streams)

                # for stream in self.streams:
                #     print(stream.filesize_mb + "mb")

                # dump(self.streams[0])
                # title
                # filesize_mb
                # fps
                # resolution
                # url
                # video_codec

                # AUDIO
                # abr
                # bitrate
                # codecs
                # subtype

                # sys.exit(0)

                # get file qualities
                for stream in self.streams:
                    file_size = str(stream.filesize_mb) + " mb"

                    if values["-TYPE-VIDEO-"]:
                        self.resolutions.append(str(stream.resolution) + " (" + str(file_size) +")")

                    elif values["-TYPE-AUDIO-"]:
                        self.resolutions.append(str(stream.itag) + " (" + str(file_size)+")")

                # dump(self.streams[0])
                return True
        else:
            return False

    def main_window(self):

        layout = self.layout()
        # Gui.theme('Default1')
        # Gui.theme_previewer()
        window = Gui.Window("Youtube Downloader", layout, finalize=True)
        self.window = window

        window['-URL-'].set_focus(True)

        while True:

            event, values = window.read()
            print('Event:', event)

            if event in (Gui.WINDOW_CLOSED, "Exit"):
                self.cancel = True
                window.close()
                sys.exit(0)
                # break

            try:

                if event == "-FETCH-":

                        print("Getting qualities...")
                        window['-INFO-'].Update("Getting qualities...")

                        self.resolutions = []

                        if window['-TYPE-VIDEO-'].get():
                            self.type = '-TYPE-VIDEO-'

                        elif window['-TYPE-AUDIO-'].get():
                            self.type = '-TYPE-AUDIO-'

                        quality = self.fetch_quality(values)

                        if quality:

                            self.save_user_setting(values)
                            self.enable_inputs(window)

                            self.url = values['-URL-']

                            # Update form data
                            fileinfo = ""
                            for i in self.info:
                                fileinfo += ("-> "+str(i) + ":\t" + str(self.info[i]) + "\n")

                            window["-INFO-"].Update(fileinfo)

                            window["-RES-LIST-"].Update(self.resolutions, disabled=False, set_to_index=0)
                            window["-DOWNLOAD-"].Update(disabled=False)
                            window["-DOWNLOAD-"].set_focus(True)

                        else:
                            Gui.popup_error("File path or URL is not correct!")

                elif event == "-DOWNLOAD-":

                    self.save_user_setting(values)

                    window["-DOWNLOAD-"].Update(disabled=True)
                    res = window["-RES-LIST-"].get()

                    res = res[0].split()[0]
                    # raise Exception("Error")

                    if len(self.streams) > 0:
                        if values["-TYPE-VIDEO-"]:
                            self.resource = self.streams.get_by_resolution(resolution=res)
                        elif values["-TYPE-AUDIO-"]:
                            self.resource = self.streams.get_by_itag(itag=int(res))

                        # add resolution to filename
                        filename = self.filename + "@" + res + self.ext

                        self.resource.download(output_path=self.download_path, filename=filename)

                        window["-DOWNLOAD-"].Update(disabled=False)

                    else:
                        Gui.popup("Error", modal=True, auto_close=False)

                # if user change url input
                elif event == "-URL-":

                    self.disable_inputs(window)

                    if self.url == "":
                        self.disable_inputs(window)
                    elif len(self.url) > 5 and self.url == values['-URL-']:
                        self.enable_inputs(window)
                    else:
                        self.disable_inputs(window)

                elif event == "-TYPE-VIDEO-" or event == "-TYPE-AUDIO-":
                        if len(self.resolutions) > 0:
                            if self.type != str(event):
                                self.disable_inputs(window)
                            else:
                                self.enable_inputs(window)
                        # else:
                        #     self.enable_inputs(window)

                elif event == "Settings":
                    YTD_Settings(self.settings, window)


            except AgeRestrictionError as e:
                print("AgeRestrictionError")
                Gui.popup(str(e), modal=True, auto_close=False)

            except UnavailableError as e:
                show_error(e)
                print("UnavailableError")
                Gui.popup(str(e), modal=True, auto_close=False)

            except PytubeError as e:
                show_error(e)
                print("PyTubeError")
                Gui.popup(str(e), modal=True, auto_close=False)

            except Exception as e:
                print("End Error exception")
                show_error(e)
                Gui.popup(str(e), modal=True, auto_close=False)
                window.close()
                sys.exit(0)

    def download_progress(self, stream, chunk, bytes_remaining):
        # if self.cancel:
        #     sys.exit(0)

        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        progress = (bytes_downloaded / total_size) * 100

        self.window["-BAR-"].UpdateBar(progress)
        self.window["-BAR-TXT-"].Update(f"{progress:.2f}%")

    def complete_progress(self, stream, file_path):
        print("Downloaded Successfully")
        # Gui.popup_auto_close(title="Downloaded Successfully!")
        Gui.popup("Success", modal=True, auto_close=True, auto_close_duration=2)


if __name__ == "__main__":

    # Create config file for first run
    if not os.path.isfile('./config.ini'):
        try:
            f = open("config.ini", "a")
            f.write('[GUI]\n')
            f.write('downloads_dir = .\n')
            f.write('type = video\n')
            f.write('resolution = 360\n')
            f.write('theme = SystemDefaultForReal\n')
            f.close()
        except Exception as e:
            print(e)

    SETTINGS_PATH = str(Path.cwd())
    settings = Gui.UserSettings(
        path=SETTINGS_PATH, filename="config.ini", use_config_file=True, convert_bools_and_none=True
    )

    # Gui.set_options(settings['GUI']['Theme'])


    ytd = YTD(settings)
    ytd.main_window()

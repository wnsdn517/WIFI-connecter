from customtkinter import *
import urllib.request
import threading
from tkinter.messagebox import askyesno
from ezwifi import *
import subprocess


def get_current_wifi_ssid():
    try:
        output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("cp949")
        lines = output.split("\n")
        for line in lines:
            if "SSID" in line:
                ssid = line.split(":")[1].strip()
                return ssid
    except subprocess.CalledProcessError:
        return None

class MainWindow():
    def __init__(self) -> None:
        
        self.unknown_count = 0
        self.main_wifi_window = CTk()
        self.main_wifi_window.title("Wi-Fi Manager")
        self.main_wifi_window.resizable(False, False)

        self.connection_label = CTkLabel(self.main_wifi_window, text="Internet Connection Status: Checking...", font=("Arial", 20))
        self.connection_label.grid(row=0, column=0, padx=10, pady=5, sticky="nw")

        self.connection_label.bind("<Button-1>", command=self.disconnect_wifi)
        
        self.wifi_frame_inner = CTkScrollableFrame(self.main_wifi_window, label_text="WIFI SSID")
        self.wifi_frame_inner.grid(row=1, column=0, columnspan=2,padx=10, pady=5, sticky="nw")

        self.refresh_button = CTkButton(self.main_wifi_window, text="refresh", command=self.refresh_wifi_list, width=60)
        self.refresh_button.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.infoframe = CTkFrame(self.main_wifi_window)
        self.infoframe.grid(row=3, column=0,columnspan = 2, padx=10, pady=5, sticky="we")

        self.warning_label = CTkLabel(self.infoframe, text="")
        self.warning_label.pack(side=RIGHT, padx=5) 
        self.warning_label2 = CTkLabel(self.infoframe, text="")
        self.warning_label2.pack(side=LEFT, padx=5) 

        self.refresh_wifi_list()

        self.check_internet_connection()
    def disconnect_wifi(self, event=None):
        if askyesno("Disconnect from Wi-Fi", "Are you sure you want to disconnect from current Wi-Fi?"):
            self.disconnectwifi()
            self.connection_label.configure(text="◼ disconnected", text_color="red")
    def disconnectwifi(self,event = None):
        interface = getWirelessInterfaces()
        disconnect(interface[0])
        
    def check_internet_connection(self):
        if self.connected():
            self.connection_label.configure(text="◼connected", text_color="green")
        else:
            self.connection_label.configure(text="◼disconnected",text_color = "red")
        self.main_wifi_window.after(250, self.check_internet_connection)

    def connected(self, host='http://google.com'):
        try:
            urllib.request.urlopen(host)
            return True
        except:
            return False

    def refresh_wifi_list(self):
        for widget in self.wifi_frame_inner.winfo_children():
            widget.destroy()
        self.unknown_count = 0
        self.progress_bar = CTkProgressBar(self.wifi_frame_inner, mode="indeterminate")
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        t = threading.Thread(target=self.search_wifi_thread)
        t.start()

    def search_wifi_thread(self):
        wifi_networks = Wifi().get_list()

        unique_networks = []
        ssid_set = set()
        for network in wifi_networks:
            ssid = network["ssid"]
            if ssid != '' and ssid not in ssid_set:
                unique_networks.append(network)
                ssid_set.add(ssid)

        unique_networks = sorted(unique_networks, key=lambda x: x["signal_quality"], reverse=True)

        self.update_wifi_list(unique_networks)

    def update_wifi_list(self, wifi_networks2):

        self.networks2 = wifi_networks2
        longestssid = max(wifi_networks2, key=lambda x: len(x['ssid']))['ssid']
        self.width = len(longestssid)

        wifi_buttons = []
        for network in wifi_networks2:
            ssid = network["ssid"]
            if ssid != '':
                self.wifi_button = CTkButton(self.wifi_frame_inner, text=ssid, font=("Arial", 12), width=self.width)
                self.wifi_button.configure(command=lambda ssid=ssid: self.connect_wifi(ssid))
                wifi_buttons.append(ssid)
                self.wifi_button.pack(padx=1, pady=5, fill=X, anchor=W)
        current_ssid = get_current_wifi_ssid()
        print(current_ssid)
        for wifi_button in wifi_buttons:
            print(wifi_button)
            if wifi_button == current_ssid:
                self.wifi_button.configure(text=current_ssid + " | ✅")
                self.wifi_button.pack(padx=1, pady=5, fill=X, anchor=W)
                self.wifi_frame_inner.update()
        self.warning_label.configure(text=f"unknown {self.unknown_count} SSID",bg_color="transparent")

        duplicate_count = len(self.networks2) - len(wifi_networks2)
        self.warning_label2.configure(text=f"same {duplicate_count} SSID",bg_color="transparent")

        self.progress_bar.destroy()

    def connect_wifi(self, ssid):
        for widget in self.wifi_frame_inner.winfo_children():
            widget.destroy()
        for network in self.networks2:
            ssid2 = network["ssid"]
            if ssid == ssid2:
                self.progress_bar = CTkProgressBar(self.wifi_frame_inner, mode="indeterminate")
                self.progress_bar.pack(pady=10)
                self.progress_bar.start()
                continue
            self.wifi_button = CTkButton(self.wifi_frame_inner, text=ssid2, font=("Arial", 12), width=self.width, command=lambda ssid=ssid2: self.connect_wifi(ssid2))
            self.wifi_button.pack(padx=1, pady=5, fill=X, anchor=W)
        self.main_wifi_window.update()

        t = threading.Thread(target=self.wificonnect_thread, args=(ssid,))
        t.start()
        

    def wificonnect_thread(self, ssid):
        log = Wifi().connect(ssid)
        self.main_wifi_window.after(0, self.show_connection_result, ssid, log)

    def show_connection_result(self, ssid, log):
        if log == True:
            self.msg = CTk()
            label = CTkLabel(self.msg, text=f"{ssid} is connected")
            label.pack()
            button = CTkButton(self.msg, text="OK", command=self.re)
            button.pack(side=LEFT)
            button2 = CTkButton(self.msg, text="end", command=self.main_wifi_window.destroy)
            button2.pack(side=LEFT)
            self.msg.mainloop()

        else:
            dialog = CTkInputDialog(text=f"Please enter password for {ssid}", title=f"Connecting to {ssid}")
            Wifi().connect(ssid, dialog.get_input())

    def re(self):
        self.msg.destroy()
        self.refresh_wifi_list()

    def run(self):
        self.main_wifi_window.mainloop()

if __name__ == "__main__":
    main = MainWindow()
    main.run()
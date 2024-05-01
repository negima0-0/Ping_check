import tkinter as tk
from tkinter import ttk, messagebox, Scrollbar, Canvas
import subprocess
import concurrent.futures
import ipaddress

def calculate_ips(network):
    try:
        net = ipaddress.ip_network(network, strict=False)
        return [str(ip) for ip in net.hosts()]
    except ValueError:
        messagebox.showerror("エラー", "無効なネットワークセグメントです。")
        return []

def ping(ip, retries, timeout):
    for attempt in range(retries):
        try:
            command = ['ping', '-n', '1', '-w', str(timeout), ip] if subprocess.os.name == 'nt' else ['ping', '-c', '1', '-W', str(timeout / 1000), ip]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "TTL=" in result.stdout or "ttl=" in result.stdout:
                return True
        except Exception:
            pass
    return False

def update_status(ips, retries, timeout):
    global ip_labels
    ip_labels = {}
    for widget in frame.winfo_children():
        widget.destroy()

    if not ips:
        return

    num_cols = max(1, int(canvas.winfo_width() / 150))
    for i, ip in enumerate(ips):
        row, col = divmod(i, num_cols)
        label = tk.Label(frame, text=ip, bg='gray', width=18)
        label.grid(row=row, column=col, padx=5, pady=5)
        ip_labels[ip] = label

    progress['maximum'] = len(ips)
    root.update_idletasks()

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = {executor.submit(ping, ip, retries, timeout): ip for ip in ips}
        for future in concurrent.futures.as_completed(results):
            ip = results[future]
            alive = future.result()
            ip_labels[ip].config(bg='green' if alive else 'red')
            completed += 1
            progress['value'] = completed
            root.update_idletasks()

def on_submit():
    retries = int(retries_entry.get())
    timeout = int(timeout_entry.get())
    network = network_entry.get()
    if network:
        ips = calculate_ips(network)
        if ips:
            update_status(ips, retries, timeout)

def adjust_layout(event=None):
    if ip_labels:
        update_status(list(ip_labels.keys()), int(retries_entry.get()), int(timeout_entry.get()))

def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

root = tk.Tk()
root.title("Network Ping Checker")
root.geometry("800x600")

settings_frame = tk.Frame(root)
settings_frame.pack(pady=20, fill=tk.X, padx=20)

network_entry = tk.Entry(settings_frame, width=50)
network_entry.grid(row=0, column=0, columnspan=4, padx=(0, 5), pady=5)

submit_button = tk.Button(settings_frame, text="ネットワーク更新", command=on_submit)
submit_button.grid(row=0, column=5, padx=(5, 0), pady=5)

retries_label = tk.Label(settings_frame, text="リトライ回数:")
retries_label.grid(row=1, column=0, sticky='e')
retries_entry = tk.Entry(settings_frame, width=5)
retries_entry.insert(0, "2")
retries_entry.grid(row=1, column=1, sticky='w')

timeout_label = tk.Label(settings_frame, text="タイムアウト (ミリ秒):")
timeout_label.grid(row=1, column=2, sticky='e')
timeout_entry = tk.Entry(settings_frame, width=5)
timeout_entry.insert(0, "1000")
timeout_entry.grid(row=1, column=3, sticky='w', padx=(10, 0))

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=20)

canvas = Canvas(root)
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
canvas.bind_all("<MouseWheel>", on_mouse_wheel)

frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor='nw', tags="frame")
frame.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))

root.mainloop()

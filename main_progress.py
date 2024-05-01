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

def ping(ip):
    try:
        command = ['ping', '-n', '1', ip] if subprocess.os.name == 'nt' else ['ping', '-c', '1', ip]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "TTL=" in result.stdout or "ttl=" in result.stdout:
            return True
        return False
    except Exception:
        return False

def update_status(ips):
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
    root.update_idletasks()  # UIを更新

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = {executor.submit(ping, ip): ip for ip in ips}
        for future in concurrent.futures.as_completed(results):
            ip = results[future]
            alive = future.result()
            ip_labels[ip].config(bg='green' if alive else 'red')
            completed += 1
            progress['value'] = completed
            root.update_idletasks()  # プログレスバーを更新

def on_submit():
    network = network_entry.get()
    if network:
        ips = calculate_ips(network)
        if ips:
            update_status(ips)

def adjust_layout(event=None):
    if ip_labels:
        update_status(list(ip_labels.keys()))

def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

root = tk.Tk()
root.title("Network Ping Checker")
root.geometry("800x600")

ip_labels = {}

network_entry = tk.Entry(root)
network_entry.pack(pady=20, fill=tk.X, padx=20)

submit_button = tk.Button(root, text="ネットワーク更新", command=on_submit)
submit_button.pack(pady=10)

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

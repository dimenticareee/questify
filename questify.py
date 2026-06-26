import os
import sys
import time
import requests
import difflib
import multiprocessing
import setproctitle

url = "https://discord.com/api/applications/detectable"
try:
    gamelist = requests.get(url, timeout=10).json()
except Exception as e:
    print(f"[!] Errore di connessione API Discord: {e}")
    sys.exit(1)

banner = r"""
                      __          ___
                     /\ \__  __  /'___\
  __    __  __     __\ \ ,_\/\_\/\ \__/  __  __
/'__`\/\ \/\ \  /'__`\ /',__\\ \ \/\/\ \ \ ,__\/\ \/\ \
/\ \L\ \ \ \_\ \/\  __//\__, `\\ \ \_\ \ \ \ \_/\ \ \_\ \
\ \___, \ \____/\ \____\/\____/ \ \__\\ \_\ \_\  \/`____ \
 \/___/\ \/___/  \/____/\/___/   \/__/ \/_/\/_/   `/___/> \
      \ \_\                                          /\___/
       \/_/                                          \/__/
               >> Python Multiprocess Edition <<
"""

def spoof_process(exe_name, game_name):
    # Questo codice gira in un processo separato isolato
    clean_title = exe_name if not exe_name.endswith('.exe') else exe_name[:-4]
    setproctitle.setproctitle(clean_title)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass # Ignora il CTRL+C nel sottoprocesso per non sporcare il terminale

def start_questify(active_processes):
    names = [app["name"] for app in gamelist if app.get("name")]

    while True:
        q = input("\nCerca gioco (0 per tornare al menu principale): ").strip().lower()
        if q == "0":
            return

        exact    = [n for n in names if n.lower() == q]
        starts   = [n for n in names if n.lower().startswith(q) and n not in exact]
        contains = [n for n in names if q in n.lower() and n not in exact and n not in starts]
        rest     = [n for n in names if n not in exact and n not in starts and n not in contains]
        fuzzy    = difflib.get_close_matches(q, rest, n=10, cutoff=0.45)
        
        matches = (exact + starts + contains + fuzzy)[:5]

        if not matches:
            print("Nessuna corrispondenza.")
            continue

        for i, name in enumerate(matches, 1):
            print(f" [{i}] --> {name}")

        sel_raw = input("Seleziona numero (0 per annullare): ")
        if not sel_raw.isdigit() or int(sel_raw) < 1 or int(sel_raw) > len(matches):
            continue

        selected_name = matches[int(sel_raw) - 1]
        
        exename = None
        for app in gamelist:
            if app.get("name") == selected_name:
                for exe in app.get("executables", []):
                    if exe.get("os") == "win32" and not exe.get("is_launcher"):
                        exename = exe.get("name").split("/")[-1]
                        break
        
        if not exename:
            print("Nessun eseguibile Windows valido trovato.")
            continue

        p = multiprocessing.Process(target=spoof_process, args=(exename, selected_name))
        p.start()
        
        # Aggiungiamo 'start_time' per tracciare il momento dell'avvio
        active_processes.append({
            "process": p, 
            "name": selected_name, 
            "start_time": time.time()
        })
        
        print(f"\n[+] Avviato in background: {selected_name} (PID: {p.pid})")
        print("[*] Puoi cercare e avviare subito un altro gioco.")

def show_active(active_processes):
    print("\n--- Processi Attivi ---")
    if not active_processes:
        print("Nessun gioco in esecuzione.")
        return

    for i, item in enumerate(active_processes, 1):
        if item["process"].is_alive():
            # Calcolo del tempo trascorso
            elapsed = int(time.time() - item["start_time"])
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            
            # Formattazione in HH:MM:SS
            timer_str = f"{h:02d}:{m:02d}:{s:02d}"
            status = f"Attivo da {timer_str}"
        else:
            status = "Chiuso"
            
        print(f" [{i}] {item['name']} - {status} (PID: {item['process'].pid})")

def kill_all(active_processes):
    for item in active_processes:
        if item["process"].is_alive():
            item["process"].terminate()
    active_processes.clear()
    print("\n[-] Tutti i processi fittizi sono stati terminati.")

def menu():
    active_processes = []
    print(banner)
    
    try:
        while True:
            print("\n [1] Cerca e Avvia status")
            print(" [2] Vedi giochi in esecuzione")
            print(" [3] Ferma tutti i giochi")
            print(" [0] Esci")
            choice = input("> ")
            
            if choice == "1":
                start_questify(active_processes)
            elif choice == "2":
                show_active(active_processes)
            elif choice == "3":
                kill_all(active_processes)
            elif choice == "0":
                kill_all(active_processes)
                sys.exit(0)
    except KeyboardInterrupt:
        kill_all(active_processes)
        sys.exit(0)

if __name__ == "__main__":
    # Necessario per Windows quando si usa multiprocessing
    multiprocessing.freeze_support()
    menu()
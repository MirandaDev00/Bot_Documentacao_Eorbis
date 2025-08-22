# main.py
# -*- coding: utf-8 -*-

import os
import re
import threading
import queue
import traceback
import requests
import io
import markdown2

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# ---- Módulos locais e constantes ----
# Agora importa a função transformer da sua nova localização
from Transformer.transformerFile import transformar_html, obter_versao
from config import THEMES, URL_BASE_IMAGENS, VERSAO_URL, OUTPUT_DIR

# ---- Dependências opcionais ----
try:
    from tkhtmlview import HTMLLabel
except ImportError:
    HTMLLabel = None

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# URLs de imagens para o transformer
IMG_PADRAO_EORBIS = "https://raw.githubusercontent.com/MirandaDev00/Bot_Documentacao_Eorbis/main/Bot_/Assets/Logo%20eorbis.png"
IMG_PADRAO_METAPRIME = "https://raw.githubusercontent.com/MirandaDev00/Bot_Documentacao_Eorbis/main/Bot_/Assets/Logo%20metaprime.png"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Orbis • Processador de Markdown → HTML")
        self.root.geometry("1480x920")

        # Estado da Aplicação
        self.state = {
            'file_queue': [],
            'output_folder': "",
            'current_version': obter_versao(VERSAO_URL, "Logs/versao.txt"), 
            'is_processing': False,
            'stop_processing': False,
            'current_theme': 'light'
        }
        
        self.ui_queue = queue.Queue()
        self.styles = ttk.Style()
        self.thumb_images_cache = []

        self._build_ui()
        self._setup_styles()
        self._init_drag_and_drop()
        self._process_ui_queue()

    # --- Estilos e Temas ---
    def _setup_styles(self):
        try:
            self.styles.theme_use("clam")
        except tk.TclError:
            pass
        self._apply_theme()

    def _apply_theme(self):
        colors = THEMES[self.state['current_theme']]
        self.root.configure(bg=colors["bg"])
        self.styles.configure("TFrame", background=colors["panel"])
        self.styles.configure("TNotebook", background=colors["bg"])
        self.styles.configure("TNotebook.Tab", font=("Inter", 12, "bold"))
        self.styles.map("TNotebook.Tab",
                        background=[("selected", colors["panel"])],
                        foreground=[("selected", colors["text"])])

        for style in ["Primary.TButton", "Accent.TButton", "Danger.TButton", "Ghost.TButton"]:
            self.styles.configure(style, font=("Inter", 11, "bold"), padding=10)
        self.styles.configure("Ghost.TButton", font=("Inter", 11), padding=8)
        self.styles.configure("Horizontal.TProgressbar", thickness=10)
        self._repaint_widgets(colors)
    
    def _repaint_widgets(self, colors):
        widgets = [
            self.topbar, self.left_panel, self.right_panel, self.bottom_panel,
            self.frame_preview_tabs, self.frame_thumbs_container
        ]
        for w in widgets:
            w.configure(background=colors["panel"])
            
        code_bg = self._mix(colors["panel"], "#000000", 0.05) if self.state['current_theme'] == 'light' else colors['code_bg']

        self.logs.configure(bg=code_bg, fg=colors["text"], insertbackground=colors["text"])
        self.codigo_html.configure(bg=code_bg, fg=colors["text"], insertbackground=colors["text"])
        self.queue_list.configure(
            bg=self._mix(colors["panel"], "#000000", 0.02), fg=colors["text"],
            selectbackground=colors["list_sel"], selectforeground=colors["text"],
            highlightthickness=0, relief="flat"
        )
        self.preview_info.configure(fg=colors["muted"], bg=colors["panel"])
        self.logs.tag_config("INFO", foreground=colors["accent"])
        self.logs.tag_config("OK", foreground=colors["accent2"])
        self.logs.tag_config("ERRO", foreground=colors["danger"])
        self.logs.tag_config("WARN", foreground=colors["warn"])

    def toggle_theme(self):
        self.state['current_theme'] = 'dark' if self.state['current_theme'] == 'light' else 'light'
        self._apply_theme()
        
    def _mix(self, c1, c2, alpha):
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(r, g, b):
            return f"#{r:02x}{g:02x}{b:02x}"
        r1, g1, b1 = hex_to_rgb(c1)
        r2, g2, b2 = hex_to_rgb(c2)
        r = int(r1 * (1 - alpha) + r2 * alpha)
        g = int(g1 * (1 - alpha) + g2 * alpha)
        b = int(b1 * (1 - alpha) + b2 * alpha)
        return rgb_to_hex(r, g, b)

    # --- Construção da UI ---
    def _build_ui(self):
        colors = THEMES[self.state['current_theme']]

        # Topbar
        self.topbar = tk.Frame(self.root, bg=colors["panel"], padx=10, pady=10)
        self.topbar.pack(fill="x")

        self.btn_add_folder = ttk.Button(self.topbar, text="📁 Adicionar Pasta", style="Primary.TButton", command=self.add_folder)
        self.btn_add_folder.pack(side="left", padx=5)

        self.btn_add_files = ttk.Button(self.topbar, text="➕ Adicionar .MD", style="Ghost.TButton", command=self.add_files)
        self.btn_add_files.pack(side="left", padx=5)

        self.btn_remove = ttk.Button(self.topbar, text="🗑 Remover Selecionado", style="Danger.TButton", command=self.remove_selected)
        self.btn_remove.pack(side="left", padx=5)

        self.btn_clear = ttk.Button(self.topbar, text="🧹 Limpar Fila", style="Ghost.TButton", command=self.clear_queue)
        self.btn_clear.pack(side="left", padx=5)

        self.btn_output = ttk.Button(self.topbar, text="📂 Pasta de Saída", style="Accent.TButton", command=self.select_output_folder)
        self.btn_output.pack(side="left", padx=5)

        self.btn_exec = ttk.Button(self.topbar, text="▶️ Executar Fila", style="Primary.TButton", command=self.start_processing)
        self.btn_exec.pack(side="left", padx=5)

        self.btn_theme = ttk.Button(self.topbar, text="🌓 Tema", style="Ghost.TButton", command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)

        # Corpo dividido: esquerda (fila) | direita (preview)
        body = tk.Frame(self.root, bg=colors["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=8)

        self.left_panel = tk.Frame(body, bg=colors["panel"], bd=0, relief="flat")
        self.left_panel.pack(side="left", fill="y", padx=(0, 8))

        self.right_panel = tk.Frame(body, bg=colors["panel"], bd=0, relief="flat")
        self.right_panel.pack(side="right", fill="both", expand=True)

        # ---- Left: Fila + mover ↑↓ ----
        tk.Label(self.left_panel, text="Fila de Arquivos", font=("Inter", 13, "bold"),
                 bg=colors["panel"], fg=colors["text"]).pack(anchor="w", padx=10, pady=(10, 6))

        list_frame = tk.Frame(self.left_panel, bg=colors["panel"])
        list_frame.pack(fill="y", expand=False, padx=10, pady=(0, 10))

        self.queue_list = tk.Listbox(list_frame, height=28, width=50,
                                     bg=self._mix(colors["panel"], "#000000", 0.02), fg=colors["text"],
                                     selectbackground=colors["list_sel"], selectforeground=colors["text"],
                                     activestyle="none", font=("Consolas", 11))
        self.queue_list.pack(side="left", fill="y")
        self.queue_list.bind("<<ListboxSelect>>", self.on_select_file)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.queue_list.yview)
        scroll.pack(side="left", fill="y")
        self.queue_list.config(yscrollcommand=scroll.set)

        move_frame = tk.Frame(self.left_panel, bg=colors["panel"])
        move_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(move_frame, text="↑ Mover", style="Ghost.TButton", command=lambda: self.move_item(-1)).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(move_frame, text="↓ Mover", style="Ghost.TButton", command=lambda: self.move_item(1)).pack(side="left", fill="x", expand=True, padx=4)

        dd_text = "Arraste .md aqui para adicionar (Drag & Drop habilitado)" if DND_AVAILABLE else "Dica: clique em 'Adicionar .MD' ou 'Adicionar Pasta' para incluir arquivos."
        self.dd_hint = tk.Label(self.left_panel, text=dd_text, bg=colors["panel"], fg=colors["muted"], wraplength=340, justify="left")
        self.dd_hint.pack(anchor="w", padx=10, pady=(0, 10))

        # ---- Right: Preview + Thumbs + Código ----
        header_right = tk.Frame(self.right_panel, bg=colors["panel"])
        header_right.pack(fill="x")

        self.preview_info = tk.Label(header_right, text="Preview • selecione um arquivo na fila",
                                     bg=colors["panel"], fg=colors["muted"], font=("Inter", 11))
        self.preview_info.pack(side="left", padx=10, pady=(10, 0))

        self.frame_preview_tabs = tk.Frame(self.right_panel, bg=colors["panel"])
        self.frame_preview_tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(self.frame_preview_tabs)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Render
        frame_render = tk.Frame(self.notebook, bg=colors["panel"])
        self.notebook.add(frame_render, text="👁 Renderizado")

        if HTMLLabel:
            self.html_preview = HTMLLabel(frame_render, html="<p style='color:gray'>Sem preview ainda.</p>",
                                          background=colors["panel"])
            self.html_preview.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            lbl = tk.Label(frame_render, text="tkhtmlview não instalado.\nInstale com: pip install tkhtmlview",
                           fg=colors["danger"], bg=colors["panel"], font=("Inter", 12))
            lbl.pack(fill="both", expand=True, padx=10, pady=10)
            self.html_preview = None

        # Container para thumbnails (abaixo do render)
        self.frame_thumbs_container = tk.Frame(self.right_panel, bg=colors["panel"])
        self.frame_thumbs_container.pack(fill="x", padx=10)
        tk.Label(self.frame_thumbs_container, text="🖼 Imagens detectadas",
                 bg=colors["panel"], fg=colors["text"], font=("Inter", 12, "bold")).pack(anchor="w")

        self.frame_thumbs = tk.Frame(self.frame_thumbs_container, bg=colors["panel"])
        self.frame_thumbs.pack(fill="x", pady=(4, 10))

        # Tab 2: Código HTML
        frame_code = tk.Frame(self.notebook, bg=colors["panel"])
        self.notebook.add(frame_code, text="📝 Código HTML")
        self.codigo_html = ScrolledText(frame_code, wrap="none", font=("Consolas", 11),
                                        bg=self._mix(colors["panel"], "#000000", 0.05), fg=colors["text"],
                                        insertbackground=colors["text"])
        self.codigo_html.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- Bottom: Logs + Progresso ----
        self.bottom_panel = tk.Frame(self.root, bg=colors["panel"])
        self.bottom_panel.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(self.bottom_panel, text="Logs", bg=colors["panel"], fg=colors["text"], font=("Inter", 12, "bold")).pack(anchor="w")
        self.logs = ScrolledText(self.bottom_panel, height=8,
                                 bg=self._mix(colors["panel"], "#000000", 0.05),
                                 fg=colors["text"], font=("Consolas", 10), insertbackground=colors["text"])
        self.logs.pack(fill="both", expand=True, pady=(4, 8))
        self.logs.tag_config("INFO", foreground=colors["accent"])
        self.logs.tag_config("OK", foreground=colors["accent2"])
        self.logs.tag_config("ERRO", foreground=colors["danger"])
        self.logs.tag_config("WARN", foreground=colors["warn"])

        progress_frame = tk.Frame(self.bottom_panel, bg=colors["panel"])
        progress_frame.pack(fill="x")
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", expand=True, side="left")
        self.progress_label = tk.Label(progress_frame, text="0%", bg=colors["panel"], fg=colors["muted"])
        self.progress_label.pack(side="left", padx=8)

    # --- Callbacks UI ---
    def add_folder(self):
        folder_path = filedialog.askdirectory(title="Selecione a pasta com arquivos .md")
        if not folder_path:
            return
        
        md_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(".md")]
        self._add_files_to_queue(md_files)

    def add_files(self):
        files = filedialog.askopenfilenames(title="Selecione arquivos .md", filetypes=[("Markdown", "*.md")])
        if not files:
            return
        self._add_files_to_queue(files)

    def _add_files_to_queue(self, files):
        added_count = 0
        for file_path in files:
            if file_path not in self.state['file_queue']:
                self.state['file_queue'].append(file_path)
                self.queue_list.insert(tk.END, file_path)
                added_count += 1
        self._log(f"[INFO] {added_count} arquivo(s) adicionados.", "INFO")

    def remove_selected(self):
        sel = list(self.queue_list.curselection())
        if not sel:
            return
        for i in reversed(sel):
            file_path = self.queue_list.get(i)
            if file_path in self.state['file_queue']:
                self.state['file_queue'].remove(file_path)
            self.queue_list.delete(i)
        self._log("[INFO] Arquivo(s) removido(s) da fila.", "INFO")

    def clear_queue(self):
        self.queue_list.delete(0, tk.END)
        self.state['file_queue'].clear()
        self._log("[INFO] Fila limpa.", "INFO")

    def move_item(self, direction):
        sel = self.queue_list.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.state['file_queue']):
            self.state['file_queue'][idx], self.state['file_queue'][new_idx] = self.state['file_queue'][new_idx], self.state['file_queue'][idx]
            self.queue_list.delete(0, tk.END)
            for f in self.state['file_queue']:
                self.queue_list.insert(tk.END, f)
            self.queue_list.select_set(new_idx)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de saída")
        if folder:
            self.state['output_folder'] = folder
            messagebox.showinfo("Pasta de Saída", f"Pasta de saída definida:\n{folder}")
            self._log(f"[INFO] Pasta de saída definida: {folder}", "INFO")

    def on_select_file(self, event=None):
        selected_index = self.queue_list.curselection()
        if not selected_index:
            return
            
        file_path = self.queue_list.get(selected_index[0])
        self.preview_info.config(text=f"Preview • {os.path.basename(file_path)}")
        self._render_preview(file_path)

    def _render_preview(self, md_path):
        """Lê o Markdown, converte para HTML e atualiza o preview da UI."""
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                raw_markdown = f.read()

            html_content = markdown2.markdown(raw_markdown, extras=["tables", "fenced-code-blocks"])
            html_content = re.sub(r'!\[\[(.*?)\]\]', lambda m: f'<img src="{URL_BASE_IMAGENS}{m.group(1)}" alt="{m.group(1)}">', html_content)
            
            if self.html_preview:
                if isinstance(self.html_preview, HTMLLabel):
                    self.html_preview.set_html(html_content)
                else:
                    self._log("[WARN] tkhtmlview indisponível. Preview renderizado não será exibido.", "WARN")
                    
            self.codigo_html.delete("1.0", tk.END)
            self.codigo_html.insert(tk.END, html_content)

            self._populate_thumbnails(self._extract_image_urls(html_content))
            
        except FileNotFoundError:
            self._log(f"[ERRO] Arquivo não encontrado: {md_path}", "ERRO")
        except Exception as e:
            self._log(f"[ERRO] Falha ao renderizar preview: {e}\n{traceback.format_exc()}", "ERRO")
            
    def _extract_image_urls(self, html_content):
        return re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_content)

    def _populate_thumbnails(self, urls):
        for w in self.frame_thumbs.winfo_children():
            w.destroy()
        self.thumb_images_cache.clear()

        if not PIL_AVAILABLE:
            tk.Label(self.frame_thumbs, text="Pillow não instalado — thumbs indisponíveis.",
                     bg=THEMES[self.state['current_theme']]["panel"], fg=THEMES[self.state['current_theme']]["warn"]).pack(anchor="w", padx=6, pady=6)
            return

        if not urls:
            tk.Label(self.frame_thumbs, text="Nenhuma imagem detectada neste arquivo.",
                     bg=THEMES[self.state['current_theme']]["panel"], fg=THEMES[self.state['current_theme']]["muted"]).pack(anchor="w", padx=6, pady=6)
            return

        row = tk.Frame(self.frame_thumbs, bg=THEMES[self.state['current_theme']]["panel"])
        row.pack(fill="x")

        for i, url in enumerate(urls[:12]):
            try:
                resp = requests.get(url, timeout=6)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img.thumbnail((140, 140))
                tkimg = ImageTk.PhotoImage(img)
                self.thumb_images_cache.append(tkimg)
                wrap = tk.Frame(row, bg=THEMES[self.state['current_theme']]["panel"], padx=6, pady=6)
                wrap.pack(side="left")
                lbl = tk.Label(wrap, image=tkimg, bg=THEMES[self.state['current_theme']]["panel"])
                lbl.pack()
                cap = tk.Label(wrap, text=os.path.basename(url), bg=THEMES[self.state['current_theme']]["panel"], fg=THEMES[self.state['current_theme']]["muted"])
                cap.pack()
            except Exception:
                pass
            
    def start_processing(self):
        if self.state['is_processing']:
            self._log("[WARN] Processamento já está em andamento.", "WARN")
            return
            
        if not self.state['output_folder']:
            messagebox.showwarning("Atenção", "Defina a pasta de saída antes de executar.")
            return

        if not self.state['file_queue']:
            messagebox.showwarning("Atenção", "Adicione arquivos à fila antes de executar.")
            return

        self.state['is_processing'] = True
        self.state['stop_processing'] = False
        self._log("[INFO] Processamento iniciado.", "INFO")
        
        threading.Thread(target=self._process_queue_worker, daemon=True).start()

    def _process_queue_worker(self):
        total_files = len(self.state['file_queue'])
        processed_count = 0
        
        self._ui_update(lambda: self._set_progress(0, total_files))

        for file_path in self.state['file_queue']:
            if self.state['stop_processing']:
                self._log("[WARN] Processamento interrompido pelo usuário.", "WARN")
                break
            
            try:
                # md -> html bruto
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_markdown = f.read()
                
                html_content_bruto = markdown2.markdown(raw_markdown, extras=["tables", "fenced-code-blocks"])
                
                # Aplica as transformações do transformer
                transformed_html = transformar_html(
                    html_content_bruto, 
                    self.state['current_version'], 
                    IMG_PADRAO_EORBIS, 
                    IMG_PADRAO_METAPRIME
                )
                
                # Salva o arquivo final
                html_filename = os.path.splitext(os.path.basename(file_path))[0] + ".html"
                final_html_path = os.path.join(self.state['output_folder'], html_filename)
                
                os.makedirs(os.path.dirname(final_html_path), exist_ok=True)
                with open(final_html_path, "w", encoding="utf-8") as f:
                    f.write(transformed_html)
                
                processed_count += 1
                self._log(f"[OK] {os.path.basename(file_path)} → {final_html_path}", "OK")
                
            except Exception as e:
                self._log(f"[ERRO] Falha ao processar {os.path.basename(file_path)}: {e}\n{traceback.format_exc()}", "ERRO")
            finally:
                current_index = self.state['file_queue'].index(file_path) + 1
                self._ui_update(lambda: self._set_progress(current_index, total_files))

        self.state['is_processing'] = False
        self._ui_update(lambda: self._set_progress(total_files, total_files))
        self._ui_update(lambda: messagebox.showinfo("Concluído", f"Processamento finalizado. {processed_count}/{total_files} arquivos processados com sucesso."))

    # --- Métodos de Utilidade ---
    def _log(self, message, tag="INFO"):
        self.logs.insert(tk.END, message + "\n", tag)
        self.logs.see(tk.END)
        
    def _ui_update(self, func):
        self.ui_queue.put(func)

    def _process_ui_queue(self):
        try:
            while True:
                fn = self.ui_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.root.after(50, self._process_ui_queue)
        
    def _set_progress(self, current, total):
        self.progress["maximum"] = max(1, total)
        self.progress["value"] = current
        percentage = int((current / max(1, total)) * 100)
        self.progress_label.config(text=f"{percentage}%")

    def _init_drag_and_drop(self):
        if DND_AVAILABLE:
            self.queue_list.drop_target_register(DND_FILES)
            self.queue_list.dnd_bind('<<Drop>>', self._on_drop_files)

    def _on_drop_files(self, event):
        paths = self._parse_dnd_paths(event.data)
        added_count = 0
        for path in paths:
            if path.lower().endswith(".md") and path not in self.state['file_queue']:
                self.state['file_queue'].append(path)
                self.queue_list.insert(tk.END, path)
                added_count += 1
        self._log(f"[INFO] {added_count} arquivo(s) arrastados para a fila.", "INFO")

    def _parse_dnd_paths(self, data):
        return data.strip().split()

# --- Inicialização ---
def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = App(root) 
    
    root.mainloop()

if __name__ == "__main__":
    main()
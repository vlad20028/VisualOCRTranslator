import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pdf2image import convert_from_path
import pytesseract
from deep_translator import GoogleTranslator  # <-- Mantener import por compatibilidad
import sv_ttk  # Para interfaz moderna
import requests  # <-- Añadido para DeepL Web
import re  # <-- Añadido para preprocesamiento
import time # <-- Añadido para timestamp de DeepL

# Configuración de Tesseract (Intenta detectar ruta o usa la tuya por defecto)
import os
posibles_rutas = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\home\AppData\Local\Programs\Tesseract-OCR\tesseract.exe" # Tu ruta original
]
for ruta in posibles_rutas:
    if os.path.exists(ruta):
        pytesseract.pytesseract.tesseract_cmd = ruta
        break

class TextOverlay(tk.Text):
    """Caja de texto flotante y movible sobre el Canvas"""
    def __init__(self, master, x, y, w, h, initial_text, **kwargs):
        super().__init__(master, undo=True, wrap=tk.WORD, **kwargs)
        self.place(x=x, y=y, width=w, height=h)
        self.insert("1.0", initial_text)
        
        # Hacerla movible con el mouse (Click derecho para mover)
        self.bind("<Button-3>", self.start_move)
        self.bind("<B3-Motion>", self.do_move)
        
        # Guardar dimensiones originales para ajuste con zoom
        self.original_x = x
        self.original_y = y
        self.original_w = w
        self.original_h = h
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.place(x=x, y=y)

class ModernTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VisualOCRTranslator + DeepL")
        self.root.geometry("1400x900")
        
        self.pages = []
        self.thumbnails = []
        self.current_page = 0
        self.zoom_level = 1.0
        self.overlays = [] # Lista de cajas de texto activas
        
        # Guardar el estado original de las páginas
        self.original_pages = []
        
        self.setup_styles()
        self.setup_ui()
        self.setup_shortcuts()

    def setup_styles(self):
        try:
            sv_ttk.set_theme("dark")
        except:
            pass

    def setup_ui(self):
        # --- TOPBAR (Estilo Google Docs) ---
        top_bar = ttk.Frame(self.root)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(top_bar, text="📂 Abrir", command=self.load_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Contenedor para centrar los botones
        center_container = ttk.Frame(top_bar)
        center_container.pack(side=tk.LEFT, expand=True)
        
        # Herramientas de texto (centradas)
        self.font_size_var = tk.StringVar(value="20")
        ttk.Label(center_container, text="Tamaño:").pack(side=tk.LEFT)
        
        # Frame para spinbox y botones
        size_frame = ttk.Frame(center_container)
        size_frame.pack(side=tk.LEFT)
        
        # Botón para disminuir tamaño (más grueso)
        decrease_btn = ttk.Button(size_frame, text="−", width=3, 
                                  command=lambda: self.adjust_font_size(-1))
        decrease_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Spinbox para tamaño de texto
        self.spinbox = ttk.Spinbox(size_frame, from_=6, to=72, width=5, 
                                   textvariable=self.font_size_var, 
                                   command=self.update_text_style)
        self.spinbox.pack(side=tk.LEFT, padx=2)
        self.spinbox.bind("<Return>", self.update_text_style_from_enter)
        
        # Botón para aumentar tamaño (más grueso)
        increase_btn = ttk.Button(size_frame, text="+", width=3,
                                  command=lambda: self.adjust_font_size(1))
        increase_btn.pack(side=tk.LEFT, padx=(2, 10))

        # Botón principal de acción
        btn_translate = ttk.Button(center_container, text="⚡ Traducir (DeepL)", command=self.translate_selection)
        btn_translate.pack(side=tk.LEFT, padx=10)

        # --- CONTENEDOR PRINCIPAL ---
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Sidebar de Miniaturas (Fondo Negro)
        self.sidebar = tk.Canvas(main_container, width=200, bg="#1a1a1a", highlightthickness=0)
        self.side_scroll = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=self.sidebar.yview)
        self.sidebar.configure(yscrollcommand=self.side_scroll.set)
        
        self.thumb_frame = tk.Frame(self.sidebar, bg="#1a1a1a")
        self.sidebar.create_window((0,0), window=self.thumb_frame, anchor="nw")
        
        main_container.add(self.sidebar, weight=1)

        # 2. Area de Trabajo (Canvas)
        work_area = ttk.Frame(main_container)
        self.canvas = tk.Canvas(work_area, bg="#333", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        main_container.add(work_area, weight=4)

        # Eventos de selección
        self.canvas.bind("<ButtonPress-1>", self.on_start_rect)
        self.canvas.bind("<B1-Motion>", self.on_drag_rect)
        self.canvas.bind("<ButtonRelease-1>", self.on_end_rect)
        
        # Evento de click derecho para limpiar selección
        self.canvas.bind("<Button-3>", self.clear_selection)
        
        # Eventos de rueda del ratón
        self.canvas.bind("<MouseWheel>", self.on_canvas_mouse_wheel)  # Windows
        self.sidebar.bind("<MouseWheel>", self.on_sidebar_mouse_wheel)

    def setup_shortcuts(self):
        self.root.bind("<Control-plus>", lambda e: self.change_zoom(0.1))
        self.root.bind("<Control-minus>", lambda e: self.change_zoom(-0.1))

    # --- LÓGICA DE PDF Y MINIATURAS ---
    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path: return
        
        self.show_loading_indicator()
        self.root.update()
        
        try:
            # Intenta buscar poppler automáticamente si está en Program Files
            poppler_path = None
            if os.path.exists(r"C:\Program Files\poppler\Library\bin"):
                poppler_path = r"C:\Program Files\poppler\Library\bin"
            
            raw_images = convert_from_path(path, poppler_path=poppler_path)
            
            self.original_pages = [img.copy() for img in raw_images]
            self.pages = [img.copy() for img in raw_images]
            
            self.render_thumbnails()
            self.show_page(0)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir PDF:\n{e}\n\nAsegúrate de tener Poppler instalado.")
        
        self.hide_loading_indicator()

    def show_loading_indicator(self):
        self.loading_label = tk.Label(self.root, text="Procesando...", font=("Arial", 14, "bold"), bg="#333", fg="white")
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

    def hide_loading_indicator(self):
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()

    def render_thumbnails(self):
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        
        for i, img in enumerate(self.pages):
            thumb = img.copy()
            thumb.thumbnail((150, 200))
            tk_thumb = ImageTk.PhotoImage(thumb)
            self.thumbnails.append(tk_thumb)
            
            lbl = tk.Label(self.thumb_frame, image=tk_thumb, bg="#1a1a1a", pady=10)
            lbl.pack(fill=tk.X)
            lbl.bind("<Button-1>", lambda e, idx=i: self.show_page(idx))
            tk.Label(self.thumb_frame, text=f"Pág {i+1}", fg="white", bg="#1a1a1a").pack()

    def show_page(self, idx):
        self.current_page = idx
        if self.original_pages and idx < len(self.original_pages):
            self.pages[idx] = self.original_pages[idx].copy()
        for box in self.overlays:
            box.destroy()
        self.overlays = []
        self.render_canvas_page()

    def render_canvas_page(self):
        img = self.pages[self.current_page]
        w, h = img.size
        new_size = (int(w * self.zoom_level), int(h * self.zoom_level))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        
        self.tk_current_page = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_current_page, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.update_overlays_zoom()

    def change_zoom(self, delta):
        old_zoom = self.zoom_level
        self.zoom_level += delta
        self.zoom_level = max(0.2, min(3.0, self.zoom_level))
        self.adjust_overlays_for_zoom(old_zoom, self.zoom_level)
        self.render_canvas_page()

    def adjust_overlays_for_zoom(self, old_zoom, new_zoom):
        for overlay in self.overlays:
            current_x = overlay.winfo_x()
            current_y = overlay.winfo_y()
            current_w = overlay.winfo_width()
            current_h = overlay.winfo_height()
            
            original_x = current_x / old_zoom
            original_y = current_y / old_zoom
            original_w = current_w / old_zoom
            original_h = current_h / old_zoom
            
            new_x = original_x * new_zoom
            new_y = original_y * new_zoom
            new_w = original_w * new_zoom
            new_h = original_h * new_zoom
            
            overlay.place(x=new_x, y=new_y, width=new_w, height=new_h)
            if hasattr(overlay, 'original_x'):
                overlay.original_x = new_x
                overlay.original_y = new_y
                overlay.original_w = new_w
                overlay.original_h = new_h

    def update_overlays_zoom(self):
        for overlay in self.overlays:
            overlay.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            overlay_x = overlay.winfo_x()
            overlay_y = overlay.winfo_y()
            overlay_w = overlay.winfo_width()
            overlay_h = overlay.winfo_height()
            
            if overlay_x + overlay_w > canvas_width:
                overlay.place(x=max(0, canvas_width - overlay_w), y=overlay_y)
            if overlay_y + overlay_h > canvas_height:
                overlay.place(x=overlay_x, y=max(0, canvas_height - overlay_h))

    # --- FUNCIONALIDAD DE RUEDA DEL RATÓN ---
    def on_canvas_mouse_wheel(self, event):
        if event.num == 4 or event.delta > 0:
            if self.current_page > 0: self.show_page(self.current_page - 1)
        elif event.num == 5 or event.delta < 0:
            if self.current_page < len(self.pages) - 1: self.show_page(self.current_page + 1)

    def on_sidebar_mouse_wheel(self, event):
        if event.num == 4 or event.delta > 0: self.sidebar.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0: self.sidebar.yview_scroll(1, "units")

    # --- FUNCIONES PARA TAMAÑO DE TEXTO ---
    def adjust_font_size(self, delta):
        try:
            current = int(self.font_size_var.get())
            new_size = max(6, min(72, current + delta))
            self.font_size_var.set(str(new_size))
            self.update_text_style()
        except ValueError:
            self.font_size_var.set("20")

    def update_text_style_from_enter(self, event=None):
        self.update_text_style()
        return "break"

    def update_text_style(self):
        new_size = int(self.font_size_var.get())
        for box in self.overlays:
            box.configure(font=("Arial", new_size))
            box.update_idletasks()
            lines = int(float(box.index('end-1c')))
            line_height = new_size * 1.5
            needed_height = lines * line_height
            if needed_height > box.winfo_height():
                box.place(height=needed_height + 10)

    # --- NUEVAS FUNCIONES: PREPROCESAMIENTO OCR Y DEEPL WEB ---
    
    def preprocess_japanese_text(self, text):
        """Mejora el texto OCR para japonés antes de enviar a DeepL"""
        if not text: return ""
        
        # 1. Eliminar espacios innecesarios (el japonés no los usa entre palabras)
        text = text.strip()
        
        # 2. Unir líneas rotas manteniendo párrafos reales
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Si la línea NO termina en puntuación fuerte, asumimos que continúa
                if line and len(line) > 0 and line[-1] not in ['。', '！', '？', '」', '』']:
                    line = line + ' ' 
                cleaned_lines.append(line)
        
        text = ''.join(cleaned_lines)
        
        # 3. Correcciones de OCR comunes
        text = text.replace('|', 'I').replace('l', 'I') 
        return text.strip()

    def translate_with_deepl_web(self, text_jp):
        if not text_jp or len(text_jp.strip()) == 0:
            return ""
        
        # 1. PEQUEÑA PAUSA AUTOMÁTICA
        import time
        time.sleep(1.5) 

        try:
            # 2. HEADERS MÁS REALISTAS
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'Referer': 'https://www.deepl.com/translator',
                'Connection': 'keep-alive',
            }
            
            # Timestamp mágico para evitar errores 429/403 de DeepL
            timestamp = int(time.time() * 1000)
            if (timestamp % 2 == 0): timestamp += 1
            
            # Payload JSON-RPC
            data = {
                'jsonrpc': '2.0',
                'method': 'LMT_handle_texts',
                'params': {
                    'texts': [{'text': text_jp}],
                    'splitting': 'newlines',
                    'lang': {
                        'source_lang_user_selected': 'JA',
                        'target_lang': 'ES'
                    },
                    'timestamp': timestamp
                },
                'id': 1
            }
            
            response = requests.post('https://www2.deepl.com/jsonrpc', headers=headers, json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result and 'texts' in result['result']:
                    return result['result']['texts'][0]['text']
            
            # Si falla DeepL, lanzar error para usar fallback
            raise Exception(f"DeepL Status: {response.status_code}")
            
        except Exception as e:
            print(f"Fallo DeepL Web: {e}. Usando Google como respaldo.")
            # Fallback a Google
            try:
                return GoogleTranslator(source='ja', target='es').translate(text_jp)
            except:
                return "Error en traducción."

    # --- LÓGICA DE SELECCIÓN ---
    def on_start_rect(self, e):
        self.start_x = self.canvas.canvasx(e.x)
        self.start_y = self.canvas.canvasy(e.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline="#FF69B4", fill="#FF69B4", width=2, stipple="gray50", tags="selection"
        )

    def on_drag_rect(self, e):
        cur_x, cur_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_end_rect(self, e):
        self.end_x, self.end_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)

    def clear_selection(self, e):
        if hasattr(self, 'rect'):
            self.canvas.delete(self.rect)

    def translate_selection(self):
        if not hasattr(self, 'rect'):
            messagebox.showwarning("Sin selección", "Por favor, seleccione un área primero.")
            return
            
        # 1. Obtener coordenadas
        x1 = min(self.start_x, self.end_x) / self.zoom_level
        y1 = min(self.start_y, self.end_y) / self.zoom_level
        x2 = max(self.start_x, self.end_x) / self.zoom_level
        y2 = max(self.start_y, self.end_y) / self.zoom_level
        
        # 2. OCR Mejorado
        crop = self.pages[self.current_page].crop((x1, y1, x2, y2))
        
        # Configuración OCR optimizada para bloques de texto (PSM 6)
        custom_config = r'--oem 3 --psm 6'
        
        try:
            # Obtener texto crudo
            text_jp_raw = pytesseract.image_to_string(crop, lang='jpn', config=custom_config)
            
            # Limpiar texto (Pre-procesamiento)
            text_jp = self.preprocess_japanese_text(text_jp_raw)
            
            # Traducir con DeepL
            text_es = self.translate_with_deepl_web(text_jp)
            
        except Exception as e:
            print(e)
            text_es = "Error OCR/Trans"

        # 3. Borrar texto original (Inpainting)
        draw = ImageDraw.Draw(self.pages[self.current_page])
        bg_color = crop.resize((1, 1)).getpixel((0, 0))
        draw.rectangle([x1, y1, x2, y2], fill=bg_color)
        
        # 4. Crear Overlay
        new_box = TextOverlay(self.canvas, 
                              x=x1 * self.zoom_level, 
                              y=y1 * self.zoom_level, 
                              w=(x2-x1) * self.zoom_level, 
                              h=(y2-y1) * self.zoom_level,
                              initial_text=text_es,
                              font=("Arial", int(self.font_size_var.get())),
                              bg="white", fg="black", bd=0)
        
        self.overlays.append(new_box)
        self.canvas.delete(self.rect)
        self.render_canvas_page()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernTranslatorApp(root)

    root.mainloop()




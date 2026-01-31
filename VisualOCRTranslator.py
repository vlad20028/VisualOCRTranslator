import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
from pdf2image import convert_from_path
import pytesseract
import sv_ttk
import os
import subprocess
import threading

# Configuración de Tesseract
posibles_rutas = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\home\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
]
for ruta in posibles_rutas:
    if os.path.exists(ruta):
        pytesseract.pytesseract.tesseract_cmd = ruta
        break

class TextOverlay(tk.Text):
    def __init__(self, master, x, y, w, h, initial_text, original_coords, **kwargs):
        super().__init__(master, undo=True, wrap=tk.WORD, **kwargs)
        self.original_x = original_coords[0]  # Coordenada X original (sin zoom)
        self.original_y = original_coords[1]  # Coordenada Y original (sin zoom)
        self.original_w = original_coords[2]  # Ancho original (sin zoom)
        self.original_h = original_coords[3]  # Alto original (sin zoom)
        self.text_content = initial_text
        
        # Colocar con las coordenadas iniciales (ya ajustadas al zoom)
        self.place(x=x, y=y, width=w, height=h)
        self.insert("1.0", initial_text)
        self.bind("<Button-3>", self.start_move)
        self.bind("<B3-Motion>", self.do_move)
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.place(x=x, y=y)
        # Actualizar coordenadas originales cuando el usuario mueve el overlay
        self.original_x = x / app.zoom_level
        self.original_y = y / app.zoom_level

    def update_position(self, zoom_level):
        """Actualizar posición y tamaño según el nivel de zoom"""
        x = self.original_x * zoom_level
        y = self.original_y * zoom_level
        w = self.original_w * zoom_level
        h = self.original_h * zoom_level
        self.place(x=x, y=y, width=w, height=h)

class ModernTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VisualOCRTranslator")
        self.root.geometry("1400x900")
        
        self.pages = []
        self.thumbnails = []
        self.current_page = 0
        self.zoom_level = 1.0
        self.overlays = []
        self.original_pages = []
        self.rect = None
        self.temp_overlay = None
        
        self.setup_styles()
        self.setup_ui()
        self.setup_shortcuts()

    def setup_styles(self):
        try:
            sv_ttk.set_theme("dark")
        except:
            pass

    def setup_ui(self):
        top_bar = ttk.Frame(self.root)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=15)
        ttk.Button(top_bar, text="📂 Abrir", command=self.load_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        center_container = ttk.Frame(top_bar)
        center_container.pack(side=tk.LEFT, expand=True)
        
        self.font_size_var = tk.StringVar(value="18")
        ttk.Label(center_container, text="Tamaño:").pack(side=tk.LEFT)
        size_frame = ttk.Frame(center_container)
        size_frame.pack(side=tk.LEFT)
        
        ttk.Button(size_frame, text="−", width=3, command=lambda: self.adjust_font_size(-1)).pack(side=tk.LEFT, padx=(0, 2))
        self.spinbox = ttk.Spinbox(size_frame, from_=6, to=72, width=5, textvariable=self.font_size_var, command=self.update_text_style)
        self.spinbox.pack(side=tk.LEFT, padx=2)
        ttk.Button(size_frame, text="+", width=3, command=lambda: self.adjust_font_size(1)).pack(side=tk.LEFT, padx=(2, 10))

        ttk.Button(center_container, text="Traducir", command=self.translate_selection).pack(side=tk.LEFT, padx=10)

        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Canvas(main_container, width=200, bg="#1a1a1a", highlightthickness=0)
        self.side_scroll = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=self.sidebar.yview)
        self.sidebar.configure(yscrollcommand=self.side_scroll.set)
        self.thumb_frame = tk.Frame(self.sidebar, bg="#1a1a1a")
        self.sidebar.create_window((0,0), window=self.thumb_frame, anchor="nw")
        main_container.add(self.sidebar, weight=1)

        work_area = ttk.Frame(main_container)
        self.canvas = tk.Canvas(work_area, bg="#333", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        main_container.add(work_area, weight=4)

        self.canvas.bind("<ButtonPress-1>", self.on_start_rect)
        self.canvas.bind("<B1-Motion>", self.on_drag_rect)
        self.canvas.bind("<ButtonRelease-1>", self.on_end_rect)
        self.canvas.bind("<Button-3>", self.clear_selection)
        self.canvas.bind("<MouseWheel>", self.on_canvas_mouse_wheel)
        self.sidebar.bind("<MouseWheel>", self.on_sidebar_mouse_wheel)

    def setup_shortcuts(self):
        self.root.bind("<Control-plus>", lambda e: self.change_zoom(0.1))
        self.root.bind("<Control-minus>", lambda e: self.change_zoom(-0.1))

    # --- CARGA EN SEGUNDO PLANO ---
    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path: return
        self.show_loading_indicator("Procesando PDF...")
        threading.Thread(target=self._process_pdf_thread, args=(path,), daemon=True).start()

    def _process_pdf_thread(self, path):
        try:
            poppler_path = r"C:\Program Files\poppler\Library\bin" if os.path.exists(r"C:\Program Files\poppler\Library\bin") else None
            raw_images = convert_from_path(path, poppler_path=poppler_path)
            self.root.after(0, self._finalize_load, raw_images)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error: {e}"))
            self.root.after(0, self.hide_loading_indicator)

    def _finalize_load(self, raw_images):
        self.original_pages = [img.copy() for img in raw_images]
        self.pages = [img.copy() for img in raw_images]
        self.render_thumbnails()
        self.show_page(0)
        self.hide_loading_indicator()

    def show_loading_indicator(self, text="Cargando..."):
        # Crear una ventana flotante centrada
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("")
        self.loading_window.geometry("300x100")
        self.loading_window.configure(bg="#333")
        self.loading_window.resizable(False, False)
        
        # Centrar la ventana
        window_width = 300
        window_height = 100
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Hacerla modal y mantenerla encima
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()
        
        # Crear contenido
        frame = tk.Frame(self.loading_window, bg="#333")
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Spinner (simulado con texto)
        self.loading_label = tk.Label(
            frame, 
            text=text, 
            font=("Arial", 12, "bold"), 
            bg="#333", 
            fg="white",
            pady=10
        )
        self.loading_label.pack()
        
        # Añadir puntos animados
        self.loading_dots = tk.Label(
            frame,
            text="...",
            font=("Arial", 14, "bold"),
            bg="#333",
            fg="#FF69B4"
        )
        self.loading_dots.pack()
        
        # Animar los puntos
        self.dot_animation_step = 0
        self.animate_dots()

    def animate_dots(self):
        if hasattr(self, 'loading_dots') and self.loading_dots.winfo_exists():
            dots = ["", ".", "..", "..."]
            self.dot_animation_step = (self.dot_animation_step + 1) % len(dots)
            self.loading_dots.config(text=dots[self.dot_animation_step])
            self.root.after(500, self.animate_dots)

    def hide_loading_indicator(self):
        if hasattr(self, 'loading_window'):
            self.loading_window.destroy()
            delattr(self, 'loading_window')
        if hasattr(self, 'loading_label'):
            delattr(self, 'loading_label')
        if hasattr(self, 'loading_dots'):
            delattr(self, 'loading_dots')

    def render_thumbnails(self):
        for widget in self.thumb_frame.winfo_children(): widget.destroy()
        self.thumbnails = []
        for i, img in enumerate(self.pages):
            thumb = img.copy()
            thumb.thumbnail((150, 200))
            tk_thumb = ImageTk.PhotoImage(thumb)
            self.thumbnails.append(tk_thumb)
            lbl = tk.Label(self.thumb_frame, image=tk_thumb, bg="#1a1a1a", pady=10)
            lbl.pack(fill=tk.X)
            lbl.bind("<Button-1>", lambda e, idx=i: self.show_page(idx))

    def show_page(self, idx):
        self.current_page = idx
        if self.original_pages: self.pages[idx] = self.original_pages[idx].copy()
        for box in self.overlays: box.destroy()
        self.overlays = []
        self.render_canvas_page()

    def render_canvas_page(self):
        if not self.pages: return
        img = self.pages[self.current_page]
        new_size = (int(img.width * self.zoom_level), int(img.height * self.zoom_level))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_current_page = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_current_page, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Actualizar posición de todos los overlays para el nuevo zoom
        self.update_overlays_position()

    def change_zoom(self, delta):
        old_zoom = self.zoom_level
        self.zoom_level = max(0.2, min(3.0, self.zoom_level + delta))
        if old_zoom != self.zoom_level:
            self.render_canvas_page()

    def update_overlays_position(self):
        """Actualizar la posición de todos los overlays según el zoom actual"""
        for overlay in self.overlays:
            overlay.update_position(self.zoom_level)

    def on_canvas_mouse_wheel(self, event):
        if event.delta > 0 and self.current_page > 0: self.show_page(self.current_page - 1)
        elif event.delta < 0 and self.current_page < len(self.pages) - 1: self.show_page(self.current_page + 1)

    def on_sidebar_mouse_wheel(self, event):
        self.sidebar.yview_scroll(-1 * (event.delta // 120), "units")

    def adjust_font_size(self, delta):
        try:
            val = int(self.font_size_var.get())
            self.font_size_var.set(str(max(6, min(72, val + delta))))
            self.update_text_style()
        except: pass

    def update_text_style(self):
        for box in self.overlays: box.configure(font=("Inter", int(self.font_size_var.get())))

    # --- TRADUCCIÓN ASÍNCRONA ---
    def translate_selection(self):
        if not hasattr(self, 'rect') or not self.pages: 
            return
        
        # Obtener coordenadas ajustadas al zoom
        x1 = min(self.start_x, self.end_x) / self.zoom_level
        y1 = min(self.start_y, self.end_y) / self.zoom_level
        x2 = max(self.start_x, self.end_x) / self.zoom_level
        y2 = max(self.start_y, self.end_y) / self.zoom_level
        
        # Validar que las coordenadas sean válidas
        if x2 - x1 < 1 or y2 - y1 < 1:
            messagebox.showwarning("Advertencia", "Selección demasiado pequeña")
            return
        
        # Asegurar que las coordenadas estén dentro de los límites de la imagen
        img_width, img_height = self.pages[self.current_page].size
        x1 = max(0, min(x1, img_width - 1))
        y1 = max(0, min(y1, img_height - 1))
        x2 = max(0, min(x2, img_width))
        y2 = max(0, min(y2, img_height))
        
        # Verificar que el área sea válida
        if x2 <= x1 or y2 <= y1:
            messagebox.showwarning("Advertencia", "Selección inválida")
            return
        
        try:
            # Convertir a enteros
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Hacer el recorte con validación adicional
            crop = self.pages[self.current_page].crop((x1, y1, x2, y2))
            
            # Verificar que el recorte tenga dimensiones válidas
            if crop.width == 0 or crop.height == 0:
                messagebox.showwarning("Advertencia", "Área de selección vacía")
                return
            
            # Convertir a RGB si es necesario
            if crop.mode != 'RGB':
                crop = crop.convert('RGB')
            
            # Intentar OCR
            text_jp = pytesseract.image_to_string(crop, lang='jpn', config='--psm 6')
            text_jp = text_jp.replace(" ", "").replace("\n", "")
            
            if not text_jp.strip():
                messagebox.showwarning("Advertencia", "No se detectó texto en la selección")
                return
                
            self.show_loading_indicator("IA Traduciendo...")
            threading.Thread(target=self._async_translate, args=(text_jp, x1, y1, x2, y2, crop), daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar la imagen: {str(e)}")
            return

    def _async_translate(self, text, x1, y1, x2, y2, crop):
        try:
            prompt = f"Traduce este texto del japonés al español, no digas nada, no pongas notas, no expliques nada. solo pasalo al español con tono natural y preciso: {text}"
            res = subprocess.run(['ollama', 'run', 'qwen2.5:3b', prompt], 
                                capture_output=True, text=True, encoding='utf-8', timeout=40)
            translation = res.stdout.strip() if res.returncode == 0 else "Error en IA"
            self.root.after(0, self._apply_translation, translation, x1, y1, x2, y2, crop)
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: messagebox.showerror("Error", "Tiempo de espera agotado"))
            self.root.after(0, self.hide_loading_indicator)
        except Exception as e:
            self.root.after(0, lambda: self.hide_loading_indicator())
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error de traducción: {e}"))

    def _apply_translation(self, text_es, x1, y1, x2, y2, crop):
        draw = ImageDraw.Draw(self.pages[self.current_page])
        draw.rectangle([x1, y1, x2, y2], fill=crop.resize((1,1)).getpixel((0,0)))
        
        # Coordenadas originales (sin zoom) para el overlay
        original_coords = (x1, y1, x2-x1, y2-y1)
        
        # Coordenadas actuales (con zoom) para colocar el overlay
        current_x = x1 * self.zoom_level
        current_y = y1 * self.zoom_level
        current_w = (x2 - x1) * self.zoom_level
        current_h = (y2 - y1) * self.zoom_level
        
        new_box = TextOverlay(self.canvas, 
                             x=current_x, 
                             y=current_y, 
                             w=current_w, 
                             h=current_h,
                             initial_text=text_es, 
                             original_coords=original_coords,
                             font=("Inter", int(self.font_size_var.get())),
                             bg="white", fg="black", bd=0)
        self.overlays.append(new_box)
        
        # Limpiar selección
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
        if self.temp_overlay:
            self.canvas.delete(self.temp_overlay)
            self.temp_overlay = None
            
        self.render_canvas_page()
        self.hide_loading_indicator()

    def on_start_rect(self, e):
        self.start_x, self.start_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        
        # Crear rectángulo translúcido rosa
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#FF69B4",  # Rosa brillante
            width=2,
            stipple="gray50",  # Patrón para transparencia
            fill="#FF69B4"  # Color de relleno
        )
        
        # Hacerlo semitransparente configurando el stipple
        self.canvas.itemconfig(self.rect, stipple="gray50")

    def on_drag_rect(self, e):
        current_x, current_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, current_x, current_y)
        
        # Actualizar o crear overlay translúcido
        x1, y1, x2, y2 = self.start_x, self.start_y, current_x, current_y
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        # Crear overlay semitransparente rosa
        if self.temp_overlay:
            self.canvas.delete(self.temp_overlay)
        
        self.temp_overlay = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#FF69B4",  # Rosa
            stipple="gray50",  # 50% transparencia
            outline=""
        )

    def on_end_rect(self, e):
        self.end_x, self.end_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        
        # Verificar que la selección tenga un tamaño mínimo
        if abs(self.end_x - self.start_x) < 5 or abs(self.end_y - self.start_y) < 5:
            # Selección demasiado pequeña, limpiar
            self.clear_selection(e)
            return
        
        # Limpiar overlay temporal
        if self.temp_overlay:
            self.canvas.delete(self.temp_overlay)
            self.temp_overlay = None

    def clear_selection(self, e):
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
        if self.temp_overlay:
            self.canvas.delete(self.temp_overlay)
            self.temp_overlay = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernTranslatorApp(root)
    root.mainloop()
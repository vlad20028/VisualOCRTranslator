# VisualOCRTranslator
VisualOCRTranslator es una aplicación de escritorio moderna para traducir texto directamente en el documentos PDF mediante seleccion

# Descripción General
Es un visor de pdf con ocr y traduccion integrada que permite extraer, traducir y superponer texto directamente sobre documentos PDF. Es una herramienta diseñada específicamente para hacer traducciones simplemente seleccionando el area, fusiona teseract OCR Con qwen2.5:3b (https://ollama.com/library/qwen2.5:3b), debe tener instalado Ollama para que funcione, tambien podria ser adaptado para usar con otros modelos mas pesados

Lista de modelos: (https://ollama.com/search)

# Requisitos
1. tesseract-ocr (Instalado)
tessdata_best (Idiomas) (https://github.com/tesseract-ocr/tessdata_best/tree/main)
2. Poppler (instalado) para abrir los pdf
3. Python 3.14.2 (añadido al patch)

   ajusta la ubicacion en el codigo, ya viene una ruta por defecto en el archivo.py

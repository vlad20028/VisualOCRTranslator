# VisualOCRTranslator

VisualOCRTranslator es una aplicación de escritorio moderna para traducir texto directamente en documentos PDF mediante selección.
<img width="1920" height="1080" alt="Captura de pantalla (2020)" src="https://github.com/user-attachments/assets/0d0cd3b0-af4a-4ff2-8c3e-ab678ed5d313" />
<img width="1920" height="1080" alt="Captura de pantalla (2028)" src="https://github.com/user-attachments/assets/edf07d7e-e3dd-45de-8d67-da3e12742284" />
<img width="1920" height="1080" alt="Captura de pantalla (2031)" src="https://github.com/user-attachments/assets/98a97484-b339-4a1a-b764-b5d06ee8d834" />

# Descripción general
Es un visor de PDF con OCR y traducción integrados que permite extraer, traducir y superponer texto directamente sobre documentos PDF. Es una herramienta diseñada específicamente para realizar traducciones simplemente seleccionando el área. Fusiona Tesseract OCR con qwen2.5:3b ([https://ollama.com/library/qwen2.5:3b](https://ollama.com/library/qwen2.5:3b)). Debe tener instalado Ollama para que funcione; también podría adaptarse para usar otros modelos más pesados.

Lista de modelos: [https://ollama.com/search](https://ollama.com/search)

# Requisitos para ejecutar VisualOCRTranslator.py

1. tesseract-ocr (instalado)
   tessdata_best (idiomas): [https://github.com/tesseract-ocr/tessdata_best/tree/main](https://github.com/tesseract-ocr/tessdata_best/tree/main)
2. Poppler (instalado) para abrir los PDF
3. Python 3.14.2 (añadido al PATH)

Ajusta la ubicación en el código; ya viene una ruta por defecto en el archivo .py.

# Características clave
1. Selección manual del área a traducir
2. Tesseract OCR + qwen2.5:3b
3. Bajo consumo de CPU
4. No se requiere GPU dedicada (opcional)
5. Posibilidad de adaptar modelos más grandes


Considéralo el «santo grial» de los traductores de documentos.

# VisualOCRTranslator

VisualOCRTranslator es una aplicación de escritorio moderna para traducir texto directamente en documentos PDF mediante selección.

# Descripción general

Es un visor de PDF con OCR y traducción integrados que permite extraer, traducir y superponer texto directamente sobre documentos PDF. Es una herramienta diseñada específicamente para realizar traducciones simplemente seleccionando el área. Fusiona Tesseract OCR con qwen2.5:3b ([https://ollama.com/library/qwen2.5:3b](https://ollama.com/library/qwen2.5:3b)). Debe tener instalado Ollama para que funcione; también podría adaptarse para usar otros modelos más pesados.

Lista de modelos: [https://ollama.com/search](https://ollama.com/search)

# Requisitos para ejecutar VisualOCRTranslator.py

1. tesseract-ocr (instalado)
   tessdata_best (idiomas): [https://github.com/tesseract-ocr/tessdata_best/tree/main](https://github.com/tesseract-ocr/tessdata_best/tree/main)
2. Poppler (instalado) para abrir los PDF
3. Python 3.14.2 (añadido al PATH)

Ajusta la ubicación en el código; ya viene una ruta por defecto en el archivo .py.

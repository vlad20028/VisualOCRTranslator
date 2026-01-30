# VisualOCRTranslator
VisualOCRTranslator es una aplicación de escritorio moderna para traducir texto directamente en el documentos PDF
Visualizador PDF con Traducción OCR usando Tesseract

# Descripción General
Esta aplicación es un visor de PDF especializado con capacidades avanzadas de traducción OCR que permite extraer, traducir y superponer texto directamente sobre documentos PDF. Es una herramienta diseñada específicamente para trabajar con documentos en múltiples idiomas, especialmente útil para traductores, estudiantes e investigadores.
<img width="1920" height="1080" alt="Captura de pantalla (1950)" src="https://github.com/user-attachments/assets/0e09e9a9-da9b-439f-97c1-107d0e4a5e51" />


# Funcionalidades Principales
1. Visualización Avanzada de PDF.
<img width="1920" height="1080" alt="Captura de pantalla (1955)" src="https://github.com/user-attachments/assets/633e3d16-8201-4203-b828-55e039056074" />

2. seleccion de area a traducir.
<img width="1920" height="1080" alt="Captura de pantalla (1987)" src="https://github.com/user-attachments/assets/891d27f6-594f-41c9-9cb0-dee5c57b1508" />

4. Traduccion de texto directamente en el pdf.
<img width="1920" height="1080" alt="Captura de pantalla (1979)" src="https://github.com/user-attachments/assets/1eeaeaac-1d9e-4f1f-9cb2-fc397ab77e0d" />

# Sistema de miniaturas: Panel lateral con vistas previas de todas las páginas
1. Zoom adaptable: Control de zoom del 20% al 300% con renderizado de alta calidad

# Navegación intuitiva: Cambio de páginas mediante miniaturas o rueda del ratón

1. Motor OCR con Tesseract
2. Reconocimiento de texto preciso: Utiliza Tesseract OCR para extraer texto de imágenes

# Soporte multi-idioma: Configurable para diferentes idiomas (por defecto: japonés 'jpn')

1. Selección por áreas: Permite seleccionar regiones específicas del documento para OCR
2. Sistema de Traducción Integrado
3. Traducción automática: Conecta con Google Translate para convertir texto extraído

# Flujo integrado: OCR → Extracción → Traducción → Superposición en un solo paso

1. Soporte para múltiples pares de idiomas: Extensible a cualquier combinación soportada por Google Translate
2. Interfaz de Edición en Tiempo Real
3. Cuadros de texto superpuestos: Texto traducido que flota sobre el documento original
4. Texto editable: Modifica las traducciones directamente en la interfaz (No implementado)
5. Control tipográfico: Ajusta tamaño, fuente y formato del texto superpuesto
6. Gestión Inteligente del Documento
7. Preservación del original: Mantiene una copia intacta del PDF cargado
7. Borrado automático: Elimina el texto original después de la traducción usando detección de color de fondo
8. Sincronización con zoom: Los elementos superpuestos se ajustan automáticamente al nivel de zoom

# Flujo de Trabajo Típico

Paso 1: Cargar Documento
paso 2. Seleccionar un archivo PDF desde el sistema
paso 3. selecciona con el raton las areas que quieres traducir.

La traduccion aparece directamente sobre el texto original, al cambiar de pagina el pdf vuelve a su estado original, sin cuadros adicionales, sin copiar, ni pegar.

# Muestra miniaturas en el panel lateral

Paso 2: Navegar y Seleccionar
Navegar entre páginas usando miniaturas o rueda del ratón
Seleccionar un área de texto con el ratón (click y arrastrar)

# El área seleccionada se marca con un rectángulo rosa translúcido

Paso 3: Procesar con OCR y Traducir
Hacer clic en "Traducir Selección"

El sistema:
Extrae la imagen del área seleccionada
Aplica Tesseract OCR para reconocer el texto
Envía el texto a Google Translate para traducción
Borra el texto original del documento
Superpone el texto traducido en un cuadro editable

# (No implementado)
Paso 4: Editar y Ajustar
Modificar la traducción directamente en el cuadro de texto

# Ajustar fuente
1. Ajustar el tamaño de fuente usando los controles (+/- o spinbox)
2. Mover el cuadro de texto a una posición óptima (clic derecho + arrastre)
Cambiar el zoom para ver detalles o vista general


# Configuración y Requisitos

Dependencias Principales
Tesseract OCR: Motor de reconocimiento de texto

1. pdf2image: Conversión de PDF a imágenes
2. deep-translator: Integración con servicios de traducción
3. PIL/Pillow: Manipulación de imágenes
4. sv_ttk: Temas modernos para Tkinter

# Idiomas Soportados

# OCR: Cualquier idioma soportado por Tesseract (configurable)

Traducción: Todos los idiomas de deepl
Interfaz: Español (personalizable)

# Limitaciones por diseño minimalista y Consideraciones Técnicas

No guarda los cambios en el PDF original (función save_pdf deshabilitada)
Requiere conexión a internet para traducciones
Depende de la precisión de Tesseract para el OCR
El borrado de texto original es básico (basado en color promedio)
Prácticas, Ideal para documentos con fondo uniforme

Mejor rendimiento con documentos de texto (no escaneos complejos)
Recomendado para traducción por secciones, no documentos completos

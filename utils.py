# utils.py
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import sqlite3
import datetime
import tempfile
import os
import platform
import subprocess

DB_NAME = "rotulos.db"

COLORES = {
    "Blanco": "#FFFFFF",
    "Verde": "#D5F5E3",
    "Rojo": "#FADBD8",
    "Azul": "#D6EAF8"
}

def obtener_logo(tipo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT imagen FROM logos WHERE tipo = ?", (tipo,))
    row = c.fetchone()
    conn.close()
    if row:
        return Image.open(io.BytesIO(row[0]))
    return None

def generar_qr(data_dict):
    qr_text = "\n".join([f"{k.upper()}: {v}" for k, v in data_dict.items()])
    qr = qrcode.make(qr_text)
    return qr

def generar_vista_previa(cliente, producto, cantidad, num_paquete, codigo_lote, orden_compra, color_fondo):
    img = Image.new("RGB", (400, 250), COLORES.get(color_fondo, "#FFFFFF"))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    y = 10
    campos = {
        "Cliente": cliente,
        "Producto": producto,
        "Cantidad": cantidad,
        "N° Paquete": num_paquete,
        "Lote": codigo_lote,
        "Orden Compra": orden_compra
    }

    for k, v in campos.items():
        draw.text((10, y), f"{k}: {v}", fill="black", font=font)
        y += 20

    draw.text((10, y + 10), "hola@webspackging", fill="black", font=font)
    draw.text((10, y + 30), "WhatsApp: 952721936", fill="black", font=font)

    return img

def generar_pdf(cliente, producto, cantidad, num_paquete, codigo_lote, orden_compra, color_fondo):
    fecha_prod = datetime.datetime.now()
    fecha_venc = fecha_prod + datetime.timedelta(days=365)

    logos = {
        "izquierdo": obtener_logo("izquierdo"),
        "derecho": obtener_logo("derecho")
    }

    buffer = io.BytesIO()

    # Definir tamaño A4 en milímetros
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    A4_WIDTH = A4_WIDTH_MM * mm
    A4_HEIGHT = A4_HEIGHT_MM * mm

    c = canvas.Canvas(buffer, pagesize=(A4_WIDTH, A4_HEIGHT))
    w, h = A4_WIDTH, A4_HEIGHT

    cols, rows = 2, 4  # 2 columnas x 4 filas = 8 rótulos por hoja
    etiquetas_por_pag = cols * rows
    label_w, label_h = w / cols, h / rows
    color_hex = HexColor(COLORES.get(color_fondo, "#FFFFFF"))

    total = num_paquete
    for i in range(total):
        if i % etiquetas_por_pag == 0 and i != 0:
            c.showPage()

        row = (i % etiquetas_por_pag) // cols
        col = (i % etiquetas_por_pag) % cols
        x = col * label_w
        y = h - (row + 1) * label_h

        # Fondo de la etiqueta
        c.setFillColor(color_hex)
        c.rect(x, y, label_w, label_h, fill=1, stroke=0)

        # Borde de la etiqueta (opcional para depuración visual)
        c.setStrokeColor(HexColor("#000000"))
        c.rect(x, y, label_w, label_h, fill=0, stroke=1)

        # Texto
        c.setFillColor("black")
        c.setFont("Helvetica", 10)

        margin = 5 * mm
        tx = x + margin
        ty = y + label_h - margin

        # Texto del rótulo
        c.drawString(tx, ty - 25, f"CLIENTE: {cliente}")
        c.drawString(tx, ty - 35, f"PRODUCTO: {producto}")
        c.drawString(tx, ty - 45, f"CANTIDAD: {cantidad} unid                               N° PAQUETE: {i + 1}/{total}")
        c.drawString(tx, ty - 55, f"LOTE: {codigo_lote}                                     ORDEN COMPRA: {orden_compra}")
        c.drawString(tx, ty - 65, f"FECHA. PRODUCCIÓN: {fecha_prod.strftime('%d/%m/%Y')}    FECHA.VENCE: {fecha_venc.strftime('%d/%m/%Y')}")
        c.drawString(tx, ty - 85, "hola@webspackging | WhatsApp: 952721936")
        c.drawString(tx, ty - 105, "☂️ Mantener seco   🔄 FIFO   🏷️ Frágil ")

        # Código QR
        datos_qr = {
            "Cliente": cliente,
            "Producto": producto,
            "Cantidad": cantidad,
            "Paquete": f"{i+1}/{total}",
            "Lote": codigo_lote,
            "Orden": orden_compra
        }
        qr_img = generar_qr(datos_qr)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        qr_size = 16 * mm
        qr_x = x + label_w - qr_size - margin
        qr_y = y + margin
        c.drawImage(ImageReader(qr_buffer), qr_x, qr_y, qr_size, qr_size)

        # Logos
        if logos["izquierdo"]:
            logo_buf = io.BytesIO()
            logos["izquierdo"].save(logo_buf, format="PNG")
            logo_buf.seek(0)
            c.drawImage(ImageReader(logo_buf), x + margin, y + label_h - 12 * mm, 20 * mm, 8 * mm)

        if logos["derecho"]:
            logo_buf = io.BytesIO()
            logos["derecho"].save(logo_buf, format="PNG")
            logo_buf.seek(0)
            c.drawImage(ImageReader(logo_buf), x + label_w - 40 * mm, y + label_h - 12 * mm, 20 * mm, 8 * mm)

    c.save()
    buffer.seek(0)
    return buffer.read()

    
def imprimir_pdf(pdf_bytes):
    """Guarda temporalmente el PDF y lo envía a la impresora predeterminada."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name

    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(tmp_path, "print")
        elif sistema == "Darwin":  # macOS
            subprocess.run(["lp", tmp_path])
        elif sistema == "Linux":
            subprocess.run(["lpr", tmp_path])
        else:
            print("Sistema no compatible para impresión directa.")
    except Exception as e:
        print(f"Error al imprimir: {e}")

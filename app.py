# app.py
import base64  # Asegúrate de tener esta importación arriba
import streamlit as st
from utils import generar_vista_previa, generar_pdf, imprimir_pdf
from db import (
    init_db, insertar_rotulo, obtener_historial,
    eliminar_rotulo, exportar_excel,
    insertar_logo, obtener_logo
)
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Rótulo General 2025", layout="wide")
st.title("📦 Generador de Rótulos - Web Packaging")

init_db()

st.sidebar.header("🔧 Datos del Rótulo")

# Valores por defecto para campos de formulario
st.session_state.setdefault("cliente", "")
st.session_state.setdefault("producto", "")

# Formulario de entrada de datos
data = {
    "cliente": st.sidebar.text_input("Cliente", value=st.session_state["cliente"]),
    "producto": st.sidebar.text_input("Producto", value=st.session_state["producto"]),
    "cantidad": st.sidebar.number_input("Cantidad", min_value=1, value=1),
    "num_paquete": st.sidebar.number_input("Número de Paquete", min_value=1, value=1),
    "codigo_lote": st.sidebar.text_input("Código de Lote"),
    "orden_compra": st.sidebar.text_input("Número de Orden de Compra"),
    "color_fondo": st.sidebar.selectbox("Color de Fondo", ["Blanco", "Verde", "Rojo", "Azul"])
}

# Vista previa del rótulo
if all([data["cliente"], data["producto"], data["codigo_lote"], data["orden_compra"]]):
    try:
        preview_img = generar_vista_previa(**data)
        st.image(preview_img, caption="Vista previa del rótulo", width=400)
    except Exception as e:
        st.error(f"Error al generar vista previa: {e}")
else:
    st.warning("Completa todos los campos requeridos para ver la vista previa.")

# Botones para guardar y generar PDF
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📂 Guardar en Historial"):
        insertar_rotulo(**data)
        st.success("Guardado exitosamente.")



with col2:
    if st.button("📄 Generar y Mostrar PDF"):
        pdf_bytes = generar_pdf(**data)
        st.download_button("⬇️ Descargar Rótulo PDF", data=pdf_bytes, file_name="rotulo.pdf", mime="application/pdf")

        # Mostrar vista previa en un iframe
        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown("### Vista previa del PDF")
        st.markdown(pdf_display, unsafe_allow_html=True)

with col3:
    if st.button("🖨️ Imprimir directamente"):
        pdf_bytes = generar_pdf(**data)
        imprimir_pdf(pdf_bytes)
        st.success("Rótulo enviado a impresora")

# Mostrar historial de rótulos
st.markdown("---")
st.subheader("📋 Historial de Rótulos")
historial_df = obtener_historial()

if not historial_df.empty:
    st.dataframe(historial_df, use_container_width=True)

    selected_index = st.number_input("Selecciona fila del historial para reutilizar", min_value=0, max_value=len(historial_df)-1, step=1)
    if st.button("♻️ Volver a usar Cliente y Producto"):
        fila = historial_df.iloc[selected_index]
        st.session_state["cliente"] = fila["cliente"]
        st.session_state["producto"] = fila["producto"]
        st.rerun()
else:
    st.warning("No hay historial aún.")

# Eliminar registro o exportar a Excel
col4, col5 = st.columns(2)
with col4:
    eliminar_id = st.text_input("ID del registro a eliminar")
    if st.button("❌ Eliminar registro") and eliminar_id:
        if eliminar_rotulo(eliminar_id):
            st.success("Registro eliminado.")
        else:
            st.warning("ID no encontrado.")

with col5:
    if st.button("📄 Exportar historial a Excel"):
        excel_bytes = exportar_excel()
        st.download_button("Descargar Excel", data=excel_bytes, file_name="historial_rotulos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---- Gestión de logos ----
st.markdown("---")
st.subheader("🖼️ Gestión de Logos para Rótulo")

cambiar_logos = st.checkbox("🔄 Quiero cambiar los logos manualmente")

from db import logo_existe, obtener_logo
from PIL import Image
import io

if cambiar_logos:
    col_logo1, col_logo2 = st.columns(2)

    with col_logo1:
        st.write("📌 Logo Izquierdo actual:")
        logo_bytes_izq = obtener_logo("izquierdo")
        if logo_bytes_izq:
            st.image(Image.open(io.BytesIO(logo_bytes_izq)), width=150)
        logo_izq = st.file_uploader("Subir nuevo Logo Izquierdo", type=["png", "jpg", "jpeg"], key="logo_izq")
        if logo_izq:
            insertar_logo("izquierdo", logo_izq.read())
            st.success("✅ Logo izquierdo actualizado")

    with col_logo2:
        st.write("📌 Logo Derecho actual:")
        logo_bytes_der = obtener_logo("derecho")
        if logo_bytes_der:
            st.image(Image.open(io.BytesIO(logo_bytes_der)), width=150)
        logo_der = st.file_uploader("Subir nuevo Logo Derecho", type=["png", "jpg", "jpeg"], key="logo_der")
        if logo_der:
            insertar_logo("derecho", logo_der.read())
            st.success("✅ Logo derecho actualizado")

else:
    # Carga inicial automática solo si no están guardados
    if not logo_existe("izquierdo"):
        try:
            with open("logo_izquierdo.png", "rb") as f:
                insertar_logo("izquierdo", f.read())
        except FileNotFoundError:
            st.warning("No se encontró logo_izquierdo.png")

    if not logo_existe("derecho"):
        try:
            with open("logo_derecho.png", "rb") as f:
                insertar_logo("derecho", f.read())
        except FileNotFoundError:
            st.warning("No se encontró logo_derecho.png")

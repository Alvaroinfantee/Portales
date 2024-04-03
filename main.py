import streamlit as st
from datetime import datetime
import sqlite3
from PIL import Image
from io import BytesIO
import base64

# Initialize the database connection
DB_FILE = "construction_photos.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

def initialize_db():
    c.execute('''CREATE TABLE IF NOT EXISTS photos_new
                 (id INTEGER PRIMARY KEY, edificio TEXT, apartamento TEXT, fecha TEXT, imagen BLOB, anotaciones TEXT, titulo_anotacion TEXT)''')
    conn.commit()
    migrate_data_and_update_schema()

def migrate_data_and_update_schema():
    # Check if the old table exists and has the wrong schema
    c.execute("PRAGMA table_info(photos)")
    columns = [info[1] for info in c.fetchall()]
    if 'edificio' not in columns and columns:
        # Assuming the old schema used different column names; adjust accordingly
        try:
            # Transfer data to the new table with correct column names, if necessary
            c.execute('''INSERT INTO photos_new (id, edificio, apartamento, fecha, imagen, anotaciones, titulo_anotacion)
                         SELECT id, building AS edificio, apartment AS apartamento, date AS fecha, image AS imagen, annotations AS anotaciones, annotation_title AS titulo_anotacion
                         FROM photos''')
            conn.commit()
        except sqlite3.OperationalError as e:
            st.error("Error migrating data: " + str(e))
        # Remove the old table
        c.execute("DROP TABLE IF EXISTS photos")
        conn.commit()
        # Rename the new table only after the old one has been removed
        c.execute("ALTER TABLE photos_new RENAME TO photos")
        conn.commit()

initialize_db()

def insert_photo(edificio, apartamento, fecha, imagen, anotaciones, titulo_anotacion):
    c.execute("INSERT INTO photos (edificio, apartamento, fecha, imagen, anotaciones, titulo_anotacion) VALUES (?, ?, ?, ?, ?, ?)",
              (edificio, apartamento, fecha, imagen, anotaciones, titulo_anotacion))
    conn.commit()

def get_photos_by_annotation_title(edificio, apartamento, titulo_anotacion):
    c.execute("SELECT * FROM photos WHERE edificio=? AND apartamento=? AND titulo_anotacion=?", (edificio, apartamento, titulo_anotacion))
    return c.fetchall()

def app():
    st.title('Portales')

    edificio = st.sidebar.selectbox('Seleccionar Edificio', [f'Edificio {i}' for i in range(1, 37)])
    apartamento = st.sidebar.selectbox('Seleccionar Apartamento', [f'Apartamento {i}' for i in range(1, 21)])
    fecha = st.sidebar.date_input('Seleccionar Fecha', datetime.now())

    titulo_anotacion = st.text_input("Título de Anotación", "")
    anotaciones = st.text_area("Anotaciones", "")

    uploaded_file = st.file_uploader("Subir Imagen", type=["jpg", "png"])
    if uploaded_file is not None and titulo_anotacion:
        bytes_data = uploaded_file.getvalue()
        insert_photo(edificio, apartamento, fecha.strftime("%Y-%m-%d"), bytes_data, anotaciones, titulo_anotacion)
        st.success('Foto y anotación subidas exitosamente!')

    titles = [title[0] for title in c.execute("SELECT DISTINCT titulo_anotacion FROM photos WHERE edificio=? AND apartamento=?", (edificio, apartamento)).fetchall()]
    if titles:
        titulo_anotacion_para_ver = st.sidebar.selectbox('Seleccionar Título de Anotación para Ver', titles)
        if st.sidebar.button('Mostrar Anotación Seleccionada'):
            photos = get_photos_by_annotation_title(edificio, apartamento, titulo_anotacion_para_ver)
            for photo in photos:
                image = Image.open(BytesIO(photo[4]))
                st.image(image, caption=f"Título: {photo[6]}, Anotaciones: {photo[5]}")

    # Button to export the database
    if st.button('Exportar Base de Datos'):
        with open(DB_FILE, "rb") as file:
            st.download_button(label="Descargar Base de Datos", data=file, file_name="construction_photos.db", mime="application/octet-stream")

if __name__ == '__main__':
    app()

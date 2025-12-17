import sqlite3
import sys
import os

# Asegurar que estamos en la raíz para encontrar la DB
db_path = "hojas_de_vida.db"

if not os.path.exists(db_path):
    print(f"❌ No encuentro la base de datos en: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- 🕵️‍♂️ INSPECCIONANDO TABLA Url_HojaDeVida ---")

# 1. Verificar nombre de la tabla (a veces SQLModel pluraliza o cambia mayúsculas)
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
table_name = None
for t in tables:
    if "hojadevida" in t[0].lower(): # Buscamos algo parecido
        table_name = t[0]
        break

if not table_name:
    print("❌ No encontré ninguna tabla parecida a 'Url_HojaDeVida'. Tablas encontradas:", tables)
    sys.exit(1)

print(f"✅ Tabla encontrada: '{table_name}'")

# 2. Listar columnas actuales
print(f"\n--- COLUMNAS EN '{table_name}' ---")
columns_info = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
col_names = [c[1] for c in columns_info]

for col in columns_info:
    print(f" - {col[1]} ({col[2]})")

# 3. Detectar columna de URL
url_candidates = ['url', 'link', 'ruta', 'enlace', 'uri', 'path']
actual_url_col = None
for col in col_names:
    if col.lower() in url_candidates:
        actual_url_col = col
        break

if actual_url_col:
    print(f"\n✅ La columna de enlaces parece ser: '{actual_url_col}'")
else:
    print(f"\n⚠️ NO detecté una columna de URL obvia. Revisa la lista de arriba.")

# 4. Agregar columna faltante (Migración manual)
if 'resumen_estructurado' not in col_names:
    print("\n🛠️ Agregando columna faltante 'resumen_estructurado'...")
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN resumen_estructurado TEXT")
        conn.commit()
        print("✅ Columna agregada exitosamente.")
    except Exception as e:
        print(f"❌ Error al agregar columna: {e}")
else:
    print("\n✅ La columna 'resumen_estructurado' ya existe.")

conn.close()
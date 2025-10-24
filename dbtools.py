import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import mysql.connector
from mysql.connector import Error

def conectar_db(host, user, passwd, db):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=passwd,
            database=db,
            autocommit=False,
            charset='utf8'
        )
        return conn
    except Error as e:
        messagebox.showerror("Error de conexión", f"{host}/{db}: {e}")
        return None

def obtener_tablas(cursor, nombre_db):
    try:
        cursor.execute(f"SHOW TABLES FROM {nombre_db}")
        tablas = [tabla[0] for tabla in cursor.fetchall()]
        return tablas
    except Error as e:
        return []

def obtener_estructura_tabla(cursor, nombre_db, tabla):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {nombre_db}.{tabla}")
        columnas = []
        for col in cursor.fetchall():
            columnas.append({
                'nombre': col[0],
                'tipo': col[1],
                'nulo': col[2],
                'clave': col[3],
                'default': col[4],
                'extra': col[5]
            })
        return columnas
    except Error as e:
        return []

def verificar_compatibilidad(tipo_origen, tipo_destino):
    tipo_origen_norm = tipo_origen.lower().split('(')[0]
    tipo_destino_norm = tipo_destino.lower().split('(')[0]
    
    compatibilidad = {
        'varchar': ['varchar', 'text', 'char', 'longtext', 'mediumtext'],
        'text': ['text', 'varchar', 'longtext', 'mediumtext'],
        'int': ['int', 'bigint', 'smallint', 'tinyint', 'mediumint'],
        'bigint': ['bigint', 'int'],
        'decimal': ['decimal', 'float', 'double'],
        'float': ['float', 'decimal', 'double'],
        'double': ['double', 'decimal', 'float'],
        'date': ['date', 'datetime', 'timestamp'],
        'datetime': ['datetime', 'timestamp', 'date'],
        'timestamp': ['timestamp', 'datetime'],
        'time': ['time'],
        'year': ['year', 'int'],
        'char': ['char', 'varchar', 'text'],
        'tinyint': ['tinyint', 'int', 'smallint'],
        'smallint': ['smallint', 'int', 'tinyint'],
        'mediumint': ['mediumint', 'int', 'bigint'],
        'longtext': ['longtext', 'text', 'varchar'],
        'mediumtext': ['mediumtext', 'text', 'varchar'],
        'blob': ['blob', 'longblob', 'mediumblob'],
        'longblob': ['longblob', 'blob'],
        'mediumblob': ['mediumblob', 'blob']
    }
    
    if tipo_origen_norm == tipo_destino_norm:
        return True, "✅ Compatible"
    
    if tipo_origen_norm in compatibilidad:
        if tipo_destino_norm in compatibilidad[tipo_origen_norm]:
            return True, "⚠️ Compatible con conversión"
    
    return False, "❌ No compatible"

def mostrar_tablas_window(root, tablas_origen, tablas_destino, db_origen, db_destino, cursor_origen, cursor_destino, conn_origen, conn_destino, log_callback):
    ventana_tablas = tk.Toplevel(root)
    ventana_tablas.title("🚀 Migrador entre tablas")
    ventana_tablas.geometry("1000x700")
    ventana_tablas.resizable(True, True)
    ventana_tablas.configure(bg="#f5f5f5")
    
    ventana_tablas.tablas_seleccionadas = []
    ventana_tablas.mapeos_guardados = {}
    
    frame_principal = tk.Frame(ventana_tablas, bg="#f5f5f5")
    frame_principal.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    titulo = tk.Label(frame_principal, text="🗄️ Migrador de Bases de Datos", 
                     font=("Arial", 16, "bold"), bg="#f5f5f5", fg="#2c3e50")
    titulo.pack(pady=(0, 15))
    
    frame_seleccion = tk.Frame(frame_principal, bg="#f5f5f5")
    frame_seleccion.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    frame_origen = tk.LabelFrame(frame_seleccion, text=f"📤 Tablas Origen - {db_origen}", 
                                font=("Arial", 11, "bold"), bg="#e8f4fd", fg="#2980b9",
                                relief="raised", bd=2)
    frame_origen.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
    # Frame para botones de origen
    frame_botones_origen = tk.Frame(frame_origen, bg="#e8f4fd")
    frame_botones_origen.pack(fill=tk.X, padx=5, pady=5)
    
    btn_ver_estructura_origen = tk.Button(frame_botones_origen, text="🔍 Ver Estructura", 
                                         command=lambda: mostrar_estructura_tabla(ventana_tablas, tree_origen, cursor_origen, db_origen, "Origen"),
                                         bg="#5dade2", fg="white", font=("Arial", 9, "bold"),
                                         relief="raised", bd=2, padx=8, pady=4)
    btn_ver_estructura_origen.pack(side=tk.LEFT, padx=(0, 5))
    
    btn_ver_datos_origen = tk.Button(frame_botones_origen, text="📊 Ver Datos", 
                                    command=lambda: mostrar_datos_tabla(ventana_tablas, tree_origen, cursor_origen, db_origen, "Origen"),
                                    bg="#52be80", fg="white", font=("Arial", 9, "bold"),
                                    relief="raised", bd=2, padx=8, pady=4)
    btn_ver_datos_origen.pack(side=tk.LEFT, padx=(0, 5))
    
    tree_origen = ttk.Treeview(frame_origen, columns=("tipo", "columnas"), show="tree headings", height=12)
    tree_origen.heading("#0", text="📋 Nombre de Tabla")
    tree_origen.heading("tipo", text="📊 Tipo")
    tree_origen.heading("columnas", text="🔢 Columnas")
    tree_origen.column("#0", width=200)
    tree_origen.column("tipo", width=100)
    tree_origen.column("columnas", width=80)
    
    scrollbar_origen = ttk.Scrollbar(frame_origen, orient="vertical", command=tree_origen.yview)
    tree_origen.configure(yscrollcommand=scrollbar_origen.set)
    
    tree_origen.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
    scrollbar_origen.pack(side=tk.RIGHT, fill=tk.Y)
    
    for tabla in tablas_origen:
        cols = obtener_estructura_tabla(cursor_origen, db_origen, tabla)
        num_cols = len(cols) if cols else 0
        tree_origen.insert("", "end", text=f"📄 {tabla}", values=("Tabla", num_cols))
    
    frame_destino = tk.LabelFrame(frame_seleccion, text=f"📥 Tablas Destino - {db_destino}", 
                                 font=("Arial", 11, "bold"), bg="#e8f8f0", fg="#27ae60",
                                 relief="raised", bd=2)
    frame_destino.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
    
    # Frame para botones de destino
    frame_botones_destino = tk.Frame(frame_destino, bg="#e8f8f0")
    frame_botones_destino.pack(fill=tk.X, padx=5, pady=5)
    
    btn_ver_estructura_destino = tk.Button(frame_botones_destino, text="🔍 Ver Estructura", 
                                          command=lambda: mostrar_estructura_tabla(ventana_tablas, tree_destino, cursor_destino, db_destino, "Destino"),
                                          bg="#5dade2", fg="white", font=("Arial", 9, "bold"),
                                          relief="raised", bd=2, padx=8, pady=4)
    btn_ver_estructura_destino.pack(side=tk.LEFT, padx=(0, 5))
    
    btn_ver_datos_destino = tk.Button(frame_botones_destino, text="📊 Ver Datos", 
                                     command=lambda: mostrar_datos_tabla(ventana_tablas, tree_destino, cursor_destino, db_destino, "Destino"),
                                     bg="#52be80", fg="white", font=("Arial", 9, "bold"),
                                     relief="raised", bd=2, padx=8, pady=4)
    btn_ver_datos_destino.pack(side=tk.LEFT, padx=(0, 5))
    
    tree_destino = ttk.Treeview(frame_destino, columns=("tipo", "columnas"), show="tree headings", height=12)
    tree_destino.heading("#0", text="📋 Nombre de Tabla")
    tree_destino.heading("tipo", text="📊 Tipo")
    tree_destino.heading("columnas", text="🔢 Columnas")
    tree_destino.column("#0", width=200)
    tree_destino.column("tipo", width=100)
    tree_destino.column("columnas", width=80)
    
    scrollbar_destino = ttk.Scrollbar(frame_destino, orient="vertical", command=tree_destino.yview)
    tree_destino.configure(yscrollcommand=scrollbar_destino.set)
    
    tree_destino.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
    scrollbar_destino.pack(side=tk.RIGHT, fill=tk.Y)
    
    for tabla in tablas_destino:
        cols = obtener_estructura_tabla(cursor_destino, db_destino, tabla)
        num_cols = len(cols) if cols else 0
        tree_destino.insert("", "end", text=f"📄 {tabla}", values=("Tabla", num_cols))
    
    frame_analisis = tk.LabelFrame(frame_principal, text="🔍 Análisis de Compatibilidad y Migración", 
                                  font=("Arial", 11, "bold"), bg="#fff3cd", fg="#856404",
                                  relief="raised", bd=2)
    frame_analisis.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    scrollbar_analisis = ttk.Scrollbar(frame_analisis)
    scrollbar_analisis.pack(side=tk.RIGHT, fill=tk.Y)
    
    text_analisis = tk.Text(frame_analisis, yscrollcommand=scrollbar_analisis.set, 
                           font=("Consolas", 10), height=12, bg="#fefefe", 
                           fg="#2c3e50", relief="sunken", bd=1)
    text_analisis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar_analisis.config(command=text_analisis.yview)
    
    def analizar_compatibilidad():
        seleccion_origen = tree_origen.selection()
        seleccion_destino = tree_destino.selection()
        
        if not seleccion_origen or not seleccion_destino:
            messagebox.showwarning("⚠️ Selección Requerida", 
                                 "Selecciona al menos una tabla de origen y una de destino")
            return
        
        text_analisis.delete(1.0, tk.END)
        
        tablas_origen_sel = []
        tablas_destino_sel = []
        
        for item in seleccion_origen:
            texto = tree_origen.item(item, "text")
            tabla = texto.replace("📄 ", "")
            tablas_origen_sel.append(tabla)
        
        for item in seleccion_destino:
            texto = tree_destino.item(item, "text")
            tabla = texto.replace("📄 ", "")
            tablas_destino_sel.append(tabla)
        
        text_analisis.insert(tk.END, f"🚀 ANÁLISIS DE COMPATIBILIDAD MÚLTIPLE\n")
        text_analisis.insert(tk.END, f"{'='*70}\n\n")
        
        text_analisis.insert(tk.END, f"📤 TABLAS ORIGEN SELECCIONADAS ({len(tablas_origen_sel)}):\n")
        for tabla in tablas_origen_sel:
            text_analisis.insert(tk.END, f"   • {tabla}\n")
        
        text_analisis.insert(tk.END, f"\n📥 TABLAS DESTINO SELECCIONADAS ({len(tablas_destino_sel)}):\n")
        for tabla in tablas_destino_sel:
            text_analisis.insert(tk.END, f"   • {tabla}\n")
        
        text_analisis.insert(tk.END, f"\n{'='*70}\n")
        text_analisis.insert(tk.END, f"🔍 ANÁLISIS DETALLADO:\n\n")
        
        ventana_tablas.mapeos_guardados = {}
        total_compatibles = 0
        total_incompatibles = 0
        
        for tabla_origen in tablas_origen_sel:
            text_analisis.insert(tk.END, f"📊 Analizando: {tabla_origen}\n")
            text_analisis.insert(tk.END, f"{'-'*50}\n")
            
            cols_origen = obtener_estructura_tabla(cursor_origen, db_origen, tabla_origen)
            if not cols_origen:
                text_analisis.insert(tk.END, f"❌ Error al obtener estructura de {tabla_origen}\n\n")
                continue
            
            mejor_match = None
            mejor_puntuacion = 0
            
            for tabla_destino in tablas_destino_sel:
                cols_destino = obtener_estructura_tabla(cursor_destino, db_destino, tabla_destino)
                if not cols_destino:
                    continue
                
                mapeo_temp = {}
                compatibles_temp = 0
                incompatibles_temp = 0
                
                for col_origen in cols_origen:
                    nombre_origen = col_origen['nombre']
                    tipo_origen = col_origen['tipo']
                    
                    mejor_col_destino = None
                    mejor_compatibilidad = False, ""
                    
                    for col_destino in cols_destino:
                        nombre_destino = col_destino['nombre']
                        tipo_destino = col_destino['tipo']
                        
                        if nombre_origen.lower() == nombre_destino.lower():
                            compat, mensaje = verificar_compatibilidad(tipo_origen, tipo_destino)
                            mejor_col_destino = nombre_destino
                            mejor_compatibilidad = compat, mensaje
                            break
                    
                    if mejor_col_destino:
                        mapeo_temp[nombre_origen] = mejor_col_destino
                        compat, mensaje = mejor_compatibilidad
                        if compat:
                            compatibles_temp += 1
                        else:
                            incompatibles_temp += 1
                
                puntuacion = (compatibles_temp * 2) - incompatibles_temp
                
                if puntuacion > mejor_puntuacion:
                    mejor_match = tabla_destino
                    mejor_puntuacion = puntuacion
                    ventana_tablas.mapeos_guardados[tabla_origen] = {
                        'destino': tabla_destino,
                        'mapeo': mapeo_temp,
                        'compatibles': compatibles_temp,
                        'incompatibles': incompatibles_temp
                    }
            
            if mejor_match:
                info = ventana_tablas.mapeos_guardados[tabla_origen]
                text_analisis.insert(tk.END, f"✅ Mejor match: {mejor_match}\n")
                text_analisis.insert(tk.END, f"   📈 Compatibles: {info['compatibles']}\n")
                text_analisis.insert(tk.END, f"   ⚠️ Incompatibles: {info['incompatibles']}\n")
                text_analisis.insert(tk.END, f"   📋 Columnas mapeadas: {len(info['mapeo'])}\n")
                total_compatibles += info['compatibles']
                total_incompatibles += info['incompatibles']
            else:
                text_analisis.insert(tk.END, f"❌ Sin tabla compatible encontrada\n")
            
            text_analisis.insert(tk.END, "\n")
        
        text_analisis.insert(tk.END, f"{'='*70}\n")
        text_analisis.insert(tk.END, f"📈 RESUMEN GENERAL:\n")
        text_analisis.insert(tk.END, f"✅ Total columnas compatibles: {total_compatibles}\n")
        text_analisis.insert(tk.END, f"❌ Total columnas incompatibles: {total_incompatibles}\n")
        text_analisis.insert(tk.END, f"🔄 Migraciones configuradas: {len(ventana_tablas.mapeos_guardados)}\n")
        
        if ventana_tablas.mapeos_guardados:
            text_analisis.insert(tk.END, f"\n🎯 LISTO PARA MIGRAR!\n")
            text_analisis.insert(tk.END, f"Usa el botón 'Migrar Datos' para ejecutar las migraciones.\n")
    
    def migrar_datos():
        if not ventana_tablas.mapeos_guardados:
            messagebox.showwarning("⚠️ Sin Configuración", 
                                 "Primero analiza la compatibilidad de las tablas")
            return
        
        resumen = "🚀 RESUMEN DE MIGRACIÓN:\n\n"
        for origen, info in ventana_tablas.mapeos_guardados.items():
            resumen += f"📤 {origen} → 📥 {info['destino']}\n"
            resumen += f"   📋 {len(info['mapeo'])} columnas\n\n"
        
        respuesta = messagebox.askyesno("🚀 Confirmar Migración Múltiple", 
            f"{resumen}¿Proceder con la migración?")
        
        if respuesta:
            migraciones_exitosas = 0
            migraciones_fallidas = 0
            
            for origen, info in ventana_tablas.mapeos_guardados.items():
                try:
                    copy_table_map(cursor_origen, cursor_destino, conn_destino, 
                                 origen, info['destino'], info['mapeo'], log_callback)
                    migraciones_exitosas += 1
                except Exception as e:
                    log_callback(f"❌ Error migrando {origen}: {e}")
                    migraciones_fallidas += 1
            
            messagebox.showinfo("✅ Migración Completada", 
                f"Migraciones exitosas: {migraciones_exitosas}\n"
                f"Migraciones fallidas: {migraciones_fallidas}")
            
            if migraciones_exitosas > 0:
                ventana_tablas.destroy()
    
    frame_botones = tk.Frame(frame_principal, bg="#f5f5f5")
    frame_botones.pack(fill=tk.X, pady=(0, 10))
    
    btn_analizar = tk.Button(frame_botones, text="🔍 Analizar Compatibilidad", 
                            command=analizar_compatibilidad,
                            bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                            relief="raised", bd=3, padx=15, pady=8)
    btn_analizar.pack(side=tk.LEFT, padx=(0, 10))
    
    btn_migrar = tk.Button(frame_botones, text="🚀 Migrar Datos", 
                          command=migrar_datos,
                          bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                          relief="raised", bd=3, padx=15, pady=8)
    btn_migrar.pack(side=tk.LEFT, padx=(0, 10))
    
    btn_cerrar = tk.Button(frame_botones, text="❌ Cerrar", 
                          command=ventana_tablas.destroy,
                          bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
                          relief="raised", bd=3, padx=15, pady=8)
    btn_cerrar.pack(side=tk.RIGHT)
    
    info_text = f"📊 Total: {len(tablas_origen)} tablas origen | {len(tablas_destino)} tablas destino"
    lbl_info = tk.Label(frame_botones, text=info_text, font=("Arial", 10), 
                       fg="#7f8c8d", bg="#f5f5f5")
    lbl_info.pack(side=tk.LEFT, padx=(20, 0))

def mostrar_estructura_tabla(root, tree, cursor, db, tipo):
    """Muestra la estructura completa de una tabla seleccionada"""
    seleccion = tree.selection()
    
    if not seleccion:
        messagebox.showwarning("⚠️ Selección Requerida", 
                             f"Selecciona una tabla para ver su estructura")
        return
    
    item = seleccion[0]
    texto = tree.item(item, "text")
    tabla = texto.replace("📄 ", "")
    
    ventana_estructura = tk.Toplevel(root)
    ventana_estructura.title(f"🔍 Estructura de {tabla} ({tipo})")
    ventana_estructura.geometry("800x500")
    ventana_estructura.configure(bg="#f5f5f5")
    
    frame_titulo = tk.Frame(ventana_estructura, bg="#f5f5f5")
    frame_titulo.pack(fill=tk.X, padx=10, pady=10)
    
    titulo = tk.Label(frame_titulo, text=f"📊 Estructura de la tabla: {tabla}", 
                     font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#2c3e50")
    titulo.pack()
    
    subtitulo = tk.Label(frame_titulo, text=f"Base de datos: {db} ({tipo})", 
                        font=("Arial", 10), bg="#f5f5f5", fg="#7f8c8d")
    subtitulo.pack()
    
    frame_tree = tk.Frame(ventana_estructura, bg="#f5f5f5")
    frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    tree_estructura = ttk.Treeview(frame_tree, columns=("tipo", "nulo", "clave", "default", "extra"), 
                                   show="tree headings")
    tree_estructura.heading("#0", text="📋 Columna")
    tree_estructura.heading("tipo", text="📊 Tipo")
    tree_estructura.heading("nulo", text="❓ Null")
    tree_estructura.heading("clave", text="🔑 Clave")
    tree_estructura.heading("default", text="📌 Default")
    tree_estructura.heading("extra", text="ℹ️ Extra")
    
    tree_estructura.column("#0", width=200)
    tree_estructura.column("tipo", width=150)
    tree_estructura.column("nulo", width=80)
    tree_estructura.column("clave", width=100)
    tree_estructura.column("default", width=100)
    tree_estructura.column("extra", width=150)
    
    scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=tree_estructura.yview)
    tree_estructura.configure(yscrollcommand=scrollbar.set)
    
    tree_estructura.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Obtener estructura
    columnas = obtener_estructura_tabla(cursor, db, tabla)
    
    if not columnas:
        messagebox.showerror("❌ Error", f"No se pudo obtener la estructura de {tabla}")
        ventana_estructura.destroy()
        return
    
    # Insertar datos en el tree
    for col in columnas:
        default_val = col['default'] if col['default'] is not None else "NULL"
        extra_val = col['extra'] if col['extra'] else ""
        
        tree_estructura.insert("", "end", text=f"📌 {col['nombre']}", 
                             values=(col['tipo'], col['nulo'], col['clave'], default_val, extra_val))
    
    frame_info = tk.Frame(ventana_estructura, bg="#e8f4fd", relief="raised", bd=2)
    frame_info.pack(fill=tk.X, padx=10, pady=10)
    
    info_text = f"📊 Total columnas: {len(columnas)}"
    lbl_info = tk.Label(frame_info, text=info_text, font=("Arial", 10, "bold"), 
                       bg="#e8f4fd", fg="#2980b9")
    lbl_info.pack(pady=5)
    
    btn_cerrar = tk.Button(frame_info, text="❌ Cerrar", 
                          command=ventana_estructura.destroy,
                          bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                          relief="raised", bd=2, padx=20, pady=5)
    btn_cerrar.pack(pady=5)

def mostrar_datos_tabla(root, tree, cursor, db, tipo):
    """Muestra una muestra de datos de una tabla seleccionada"""
    seleccion = tree.selection()
    
    if not seleccion:
        messagebox.showwarning("⚠️ Selección Requerida", 
                             f"Selecciona una tabla para ver sus datos")
        return
    
    item = seleccion[0]
    texto = tree.item(item, "text")
    tabla = texto.replace("📄 ", "")
    
    ventana_datos = tk.Toplevel(root)
    ventana_datos.title(f"📊 Datos de {tabla} ({tipo})")
    ventana_datos.geometry("1000x600")
    ventana_datos.configure(bg="#f5f5f5")
    
    frame_titulo = tk.Frame(ventana_datos, bg="#f5f5f5")
    frame_titulo.pack(fill=tk.X, padx=10, pady=10)
    
    titulo = tk.Label(frame_titulo, text=f"📊 Datos de la tabla: {tabla}", 
                     font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#2c3e50")
    titulo.pack()
    
    subtitulo = tk.Label(frame_titulo, text=f"Base de datos: {db} ({tipo})", 
                        font=("Arial", 10), bg="#f5f5f5", fg="#7f8c8d")
    subtitulo.pack()
    
    try:
        # Obtener estructura para las columnas
        columnas = obtener_estructura_tabla(cursor, db, tabla)
        if not columnas:
            messagebox.showerror("❌ Error", f"No se pudo obtener la estructura de {tabla}")
            ventana_datos.destroy()
            return
        
        nom_columnas = [col['nombre'] for col in columnas]
        
        # Consultar datos (limitado a 100 registros para no sobrecargar)
        cursor.execute(f"SELECT * FROM {tabla} LIMIT 100")
        rows = cursor.fetchall()
        
        # Contar total de registros
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total_registros = cursor.fetchone()[0]
        
        frame_tree = tk.Frame(ventana_datos, bg="#f5f5f5")
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree_datos = ttk.Treeview(frame_tree, columns=nom_columnas, show="tree headings")
        tree_datos.heading("#0", text="#")
        tree_datos.column("#0", width=50)
        
        for col in nom_columnas:
            tree_datos.heading(col, text=col)
            tree_datos.column(col, width=100)
        
        scrollbar_vertical = ttk.Scrollbar(frame_tree, orient="vertical", command=tree_datos.yview)
        scrollbar_horizontal = ttk.Scrollbar(frame_tree, orient="horizontal", command=tree_datos.xview)
        tree_datos.configure(yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)
        
        tree_datos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_vertical.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Insertar datos
        for idx, row in enumerate(rows, 1):
            valores = [str(val) if val is not None else "NULL" for val in row]
            valores_cortos = [val[:50] + "..." if len(val) > 50 else val for val in valores]
            tree_datos.insert("", "end", text=str(idx), values=valores_cortos)
        
        frame_info = tk.Frame(ventana_datos, bg="#fff3cd", relief="raised", bd=2)
        frame_info.pack(fill=tk.X, padx=10, pady=10)
        
        if total_registros > 100:
            info_text = f"📊 Mostrando 100 de {total_registros} registros totales"
        else:
            info_text = f"📊 Total de registros: {total_registros}"
        
        lbl_info = tk.Label(frame_info, text=info_text, font=("Arial", 10, "bold"), 
                           bg="#fff3cd", fg="#856404")
        lbl_info.pack(pady=5)
        
        btn_cerrar = tk.Button(frame_info, text="❌ Cerrar", 
                              command=ventana_datos.destroy,
                              bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                              relief="raised", bd=2, padx=20, pady=5)
        btn_cerrar.pack(pady=5)
        
    except Error as e:
        messagebox.showerror("❌ Error", f"Error al obtener datos: {e}")
        ventana_datos.destroy()

def copy_table_map(cursor_origen, cursor_dest, conn_dest, tabla_origen, tabla_dest, col_map, log_callback):
    try:
        cursor_origen.execute(f"SELECT {', '.join(col_map.keys())} FROM {tabla_origen}")
        rows = cursor_origen.fetchall()
        cols_dest = ', '.join(col_map.values())
        placeholders = ', '.join(['%s'] * len(col_map))

        inserted = 0
        for row in rows:
            cursor_dest.execute(
                f"INSERT INTO {tabla_dest} ({cols_dest}) VALUES ({placeholders})",
                tuple(row)
            )
            inserted += 1
        conn_dest.commit()
        log_callback(f"✅ {inserted} registros insertados en {tabla_dest}")
    except Error as e:
        conn_dest.rollback()
        log_callback(f"❌ Error en {tabla_dest}: {e}")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Migrador Versátil con Mapeo de Columnas")

        frame_conf = tk.Frame(root)
        frame_conf.pack(pady=5)

        tk.Label(frame_conf, text="Host Origen").grid(row=0, column=0)
        tk.Label(frame_conf, text="Usuario").grid(row=1, column=0)
        tk.Label(frame_conf, text="Contraseña").grid(row=2, column=0)
        tk.Label(frame_conf, text="Base").grid(row=3, column=0)

        tk.Label(frame_conf, text="Host Destino").grid(row=0, column=2)
        tk.Label(frame_conf, text="Usuario").grid(row=1, column=2)
        tk.Label(frame_conf, text="Contraseña").grid(row=2, column=2)
        tk.Label(frame_conf, text="Base").grid(row=3, column=2)

        self.host_or = tk.Entry(frame_conf); self.host_or.grid(row=0, column=1); self.host_or.insert(0,"localhost")
        self.user_or = tk.Entry(frame_conf); self.user_or.grid(row=1, column=1); self.user_or.insert(0,"root")
        self.pass_or = tk.Entry(frame_conf, show="*"); self.pass_or.grid(row=2, column=1)
        self.db_or   = tk.Entry(frame_conf); self.db_or.grid(row=3, column=1); self.db_or.insert(0,"ejemploorigen")

        self.host_dest = tk.Entry(frame_conf); self.host_dest.grid(row=0, column=3); self.host_dest.insert(0,"localhost")
        self.user_dest = tk.Entry(frame_conf); self.user_dest.grid(row=1, column=3); self.user_dest.insert(0,"root")
        self.pass_dest = tk.Entry(frame_conf, show="*"); self.pass_dest.grid(row=2, column=3)
        self.db_dest   = tk.Entry(frame_conf); self.db_dest.grid(row=3, column=3); self.db_dest.insert(0,"ejemplodestino")

        tk.Button(root, text="Conectar", command=self.conectar).pack(pady=5)
        tk.Button(root, text="Salir", command=root.quit).pack(pady=5)

        self.log = tk.Text(root, height=12, width=80)
        self.log.pack(pady=10)

    def log_msg(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def conectar(self):
        self.conn_origen = conectar_db(self.host_or.get(), self.user_or.get(), self.pass_or.get(), self.db_or.get())
        self.conn_destino = conectar_db(self.host_dest.get(), self.user_dest.get(), self.pass_dest.get(), self.db_dest.get())
        if self.conn_origen and self.conn_destino:
            self.cursor_origen = self.conn_origen.cursor()
            self.cursor_destino = self.conn_destino.cursor()
            self.log_msg("✅ Conexión exitosa a ambas bases.")
            
            tablas_origen = obtener_tablas(self.cursor_origen, self.db_or.get())
            tablas_destino = obtener_tablas(self.cursor_destino, self.db_dest.get())
            
            mostrar_tablas_window(self.root, tablas_origen, tablas_destino, 
                                self.db_or.get(), self.db_dest.get(),
                                self.cursor_origen, self.cursor_destino,
                                self.conn_origen, self.conn_destino, self.log_msg)
            
            self.log_msg(f"📋 Encontradas {len(tablas_origen)} tablas en origen y {len(tablas_destino)} tablas en destino.")

    def migrar_tabla_map(self):
        if not hasattr(self, "cursor_origen") or not hasattr(self, "cursor_destino"):
            self.log_msg("⚠️ Primero conecta a las bases.")
            return

        tabla_origen = simpledialog.askstring("Tabla Origen", "Nombre de la tabla origen:")
        tabla_dest = simpledialog.askstring("Tabla Destino", "Nombre de la tabla destino:")

        if not tabla_origen or not tabla_dest:
            return

        try:
            self.cursor_origen.execute(f"SHOW COLUMNS FROM {tabla_origen}")
            cols_origen = [c[0] for c in self.cursor_origen.fetchall()]

            self.cursor_destino.execute(f"SHOW COLUMNS FROM {tabla_dest}")
            cols_dest = [c[0] for c in self.cursor_destino.fetchall()]
        except Error as e:
            self.log_msg(f"❌ Error al leer columnas: {e}")
            return

        col_map = {}
        for col in cols_origen:
            dest_col = simpledialog.askstring("Mapeo de Columnas", f"Columna origen '{col}' → columna destino (dejar vacío para ignorar):")
            if dest_col and dest_col in cols_dest:
                col_map[col] = dest_col

        if not col_map:
            self.log_msg("⚠️ No se definió ningún mapeo de columnas.")
            return

        copy_table_map(self.cursor_origen, self.cursor_destino, self.conn_destino, tabla_origen, tabla_dest, col_map, self.log_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

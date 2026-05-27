#!/usr/bin/env python
# coding: utf-8

# In[8]:


"""PRÁCTICA ETL - PART 1.1: Análisis de datos con RegEx y SQLite3"""

import urllib.request
import re
import csv
import sqlite3
import os
from pathlib import Path
from typing import List, Dict

# Patrones RegEx
PATRON_PLUS_62 = r'\+62'
PATRON_CORCHETES_GUION = r'^\[.*?\]-'
PATRON_ESPACIOS = r'\s+'

def encontrar_plus_62(phone_number: str) -> bool:
    return bool(re.search(PATRON_PLUS_62, phone_number))

def encontrar_corchetes_guion(texto: str) -> bool:
    return bool(re.match(PATRON_CORCHETES_GUION, texto))

def encontrar_espacios(texto: str) -> List[str]:
    return re.findall(PATRON_ESPACIOS, texto)

def tiene_espacios(texto: str) -> bool:
    return bool(re.search(PATRON_ESPACIOS, texto))

def procesar_csv_con_regex(archivo_csv: str, archivo_db: str = 'members.db') -> Dict:
    """Lee CSV, aplica patrones RegEx y almacena en SQLite3"""
    resultados = {
        'total_registros': 0, 'con_plus_62': [],
        'con_corchetes_guion': [], 'con_espacios': [], 'errores': []
    }

    try:
        conexion = sqlite3.connect(archivo_db)
        cursor = conexion.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                participant_id TEXT PRIMARY KEY,
                first_name TEXT, last_name TEXT, birth_date TEXT,
                address TEXT, phone_number TEXT, country TEXT,
                institute TEXT, occupation TEXT, register_time TEXT,
                tiene_plus_62 INTEGER, tiene_corchetes_guion INTEGER,
                tiene_espacios INTEGER
            )
        ''')

        with open(archivo_csv, 'r', encoding='utf-8') as csvfile:
            lector = csv.DictReader(csvfile)
            for fila in lector:
                resultados['total_registros'] += 1
                try:
                    participant_id = fila['participant_id']
                    nombre = f"{fila['first_name']} {fila['last_name']}"
                    phone = fila.get('phone_number', '')

                    t_plus = encontrar_plus_62(phone)
                    t_corchetes = encontrar_corchetes_guion(phone)
                    t_espacios = tiene_espacios(phone)

                    if t_plus: resultados['con_plus_62'].append({'id': participant_id, 'nombre': nombre, 'telefono': phone})
                    if t_corchetes: resultados['con_corchetes_guion'].append({'id': participant_id, 'nombre': nombre, 'telefono': phone})
                    if t_espacios: resultados['con_espacios'].append({'id': participant_id, 'nombre': nombre, 'telefono': phone})

                    cursor.execute('''
                        INSERT OR REPLACE INTO members VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        participant_id, fila['first_name'], fila['last_name'], fila['birth_date'],
                        fila['address'], phone, fila['country'], fila['institute'],
                        fila['occupation'], fila['register_time'],
                        1 if t_plus else 0, 1 if t_corchetes else 0, 1 if t_espacios else 0
                    ))
                except Exception as e:
                    resultados['errores'].append({'registro': resultados['total_registros'], 'error': str(e)})

        conexion.commit()

        cursor.execute('SELECT COUNT(*) FROM members WHERE tiene_plus_62 = 1')
        count_plus_62 = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM members WHERE tiene_corchetes_guion = 1')
        count_corchetes = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM members WHERE tiene_espacios = 1')
        count_espacios = cursor.fetchone()[0]

        resultados['estadisticas'] = {
            'total_procesados': resultados['total_registros'],
            'cantidad_plus_62': count_plus_62,
            'porcentaje_plus_62': round((count_plus_62 / resultados['total_registros'] * 100), 2) if resultados['total_registros'] > 0 else 0,
            'cantidad_corchetes_guion': count_corchetes,
            'porcentaje_corchetes_guion': round((count_corchetes / resultados['total_registros'] * 100), 2) if resultados['total_registros'] > 0 else 0,
            'cantidad_espacios': count_espacios,
            'porcentaje_espacios': round((count_espacios / resultados['total_registros'] * 100), 2) if resultados['total_registros'] > 0 else 0
        }
        conexion.close()
    except Exception as e:
        resultados['errores'].append({'error_general': str(e)})
    return resultados

def imprimir_resultados(resultados: Dict) -> None:
    print("\n" + "=" * 80)
    print("PRÁCTICA ETL - ANÁLISIS CON REGEX")
    print("=" * 80 + "\n")

    stats = resultados.get('estadisticas', {})
    print("ESTADÍSTICAS GENERALES")
    print("-" * 80)
    print(f"Total de registros procesados: {stats.get('total_procesados', 0)}\n")

    print("PATRÓN 1: NÚMEROS CON '+62'")
    print("-" * 80)
    print(f"Cantidad encontrada: {stats.get('cantidad_plus_62', 0)} ({stats.get('porcentaje_plus_62', 0)}%)\n")

    print("PATRÓN 2: PATRONES CON CORCHETES Y GUION '[]-'")
    print("-" * 80)
    print(f"Cantidad encontrada: {stats.get('cantidad_corchetes_guion', 0)} ({stats.get('porcentaje_corchetes_guion', 0)}%)\n")

    print("PATRÓN 3: ESPACIOS EN BLANCO")
    print("-" * 80)
    print(f"Cantidad encontrada: {stats.get('cantidad_espacios', 0)} ({stats.get('porcentaje_espacios', 0)}%)\n")
    print("=" * 80)

if __name__ == "__main__":
    archivo_csv = "members.csv"
    archivo_db = "members.db"

    # enlace directo a GitHub
    url_github = "https://raw.githubusercontent.com/NationalSpark37/Practica-ETL-part1.1/refs/heads/main/members.csv"

    print("Conectando a GitHub para descargar el archivo...")
    try:
        # Descargamos el archivo desde la URL
        urllib.request.urlretrieve(url_github, archivo_csv)
        print("✓ Archivo descargado exitosamente.")
    except Exception as e:
        print(f"✗ Error al descargar el archivo: {e}")
        exit() # Detenemos el código si no hay internet o falla la descarga

    print("\nIniciando procesamiento del archivo CSV...")

    resultados = procesar_csv_con_regex(archivo_csv, archivo_db)
    imprimir_resultados(resultados)

    if resultados.get('total_registros', 0) > 0:
        print("\n✓ Proceso completado exitosamente")
        print(f"✓ Base de datos creada/actualizada: {archivo_db}")
    else:
        print("\n✗ No se procesaron registros.")


# In[ ]:





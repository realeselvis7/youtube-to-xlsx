# YouTube to XLSX

Este proyecto permite **extraer información de todos los videos de un canal de YouTube** y exportarla a un archivo **Excel (.xlsx)**.  
Está pensado para administradores de canales o equipos de contenido que necesiten reportes rápidos de métricas de videos.

---

## 🚀 Requisitos previos

### 1. Tener acceso al canal de YouTube
Debes usar una cuenta que **tenga acceso al canal** desde YouTube Studio.

⚠️ Si el canal es de **Marca**, asegúrate de estar agregado como:
- **Propietario** o **Administrador** en la cuenta de marca.
  → https://myaccount.google.com/brandaccounts

---

### 2. Crear o usar un proyecto en **Google Cloud Console**

1. Ve a: https://console.cloud.google.com/
2. Crea un proyecto o selecciona uno existente.
3. Habilita la API:
```

API de datos de YouTube v3

```
4. Ve a **OAuth Consent Screen** y configúralo como:
- Tipo de usuario: **External**
  (Si lo usas solo dentro de la misma organización, puedes usar Internal)
- Añadir tu correo como **Test User**

---

### 3. Crear credenciales OAuth

1. En Google Cloud Console, ve a:  
**APIs & Services → Credentials → Create Credentials → OAuth Client ID**
2. Selecciona:
- **Application type:** Desktop App
3. Descarga el archivo:
```

credentials.json

```

🛑 **No subas este archivo al repositorio.**  
Está en `.gitignore` por seguridad.

---

## 📁 Estructura del Proyecto

```

youtube-to-xlsx/
│
├─ scripts/
│   └─ export_to_xlsx.py   # Script principal que obtiene datos y genera el XLSX
│
├─ data/
│   └─ output.xlsx         # Archivo generado (se crea al ejecutar)
│
├─ credentials.json        # Archivo privado OAUTH (NO SE INCLUYE EN EL REPO)
│
└─ requirements.txt

````

---

## 🔧 Instalación

Clona el repositorio:

```bash
git clone https://github.com/realeselvis7/youtube-to-xlsx.git
cd youtube-to-xlsx
````

Instala dependencias:

```bash
pip install -r requirements.txt
```

Coloca tu archivo `credentials.json` en la raíz del proyecto:

```
youtube-to-xlsx/
 └ credentials.json  ✅
```

---

## ▶️ Uso

Ejecuta el script:

```bash
python scripts/export_to_xlsx.py
```

La primera vez, se abrirá una ventana en el navegador para que **inicies sesión** y otorgues permisos de acceso.

Luego se generará el archivo:

```
./data/output.xlsx
```

---

## 📝 ¿Qué datos se exportan?

* Título del video
* ID del video
* URL
* Fecha de publicación
* Número de vistas
* Likes
* Comentarios
* Duración
* Estado (Público / No listado / Privado)
* etc.

Puedes editar las columnas modificando el archivo:

```
scripts/export_to_xlsx.py
```

---

## 🔐 Seguridad (IMPORTANTE)

* `credentials.json` **NO debe subirse al repositorio.**
* Mantén el archivo en tu máquina o en un entorno seguro.
* Si trabajas con múltiples personas, comparte el archivo **solo con miembros autorizados**.

---

## ❓ Problemas Comunes

| Error                              | Causa                                       | Solución                                                   |
| ---------------------------------- | ------------------------------------------- | ---------------------------------------------------------- |
| `Error 400: invalid_scope`         | Estás usando una cuenta sin acceso al canal | Agrega la cuenta en YouTube Studio como propietario/editor |
| La ventana OAuth no deja continuar | La cuenta no está en Test Users             | Agrega la cuenta en Google Cloud → OAuth → Test Users      |
| `Quota exceeded`                   | Se alcanzó el límite diario de la API       | Solicita cuota adicional en Cloud Console                  |

---

## 🧑‍💻 Autor

**Elvis Reales**
GitHub: [https://github.com/realeselvis7](https://github.com/realeselvis7)

---

## ⭐ Si te fue útil

Dale una estrella al repo 😊

```
⭐️ https://github.com/realeselvis7/youtube-to-xlsx
```

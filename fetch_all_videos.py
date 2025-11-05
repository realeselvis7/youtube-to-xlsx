#!/usr/bin/env python3
"""
fetch_all_videos.py

- Descarga todos los videoIds desde la playlist de uploads (uploads playlist).
- Llama a videos.list para obtener contentDetails + status.
- Si algunos IDs NO aparecen en la respuesta (p. ej. privados/eliminados), los marca.
- Opcional: si pasas --client-secrets, hace un OAuth2 (propietario del canal) y
  usa la API autenticada para leer la playlist (incluye privados).
"""

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
import isodate

# google client libs
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

YOUTUBE_PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def parse_args():
    p = argparse.ArgumentParser(description="Descarga videos + duration/type/privacy. Usa OAuth si quieres ver privados.")
    p.add_argument("--api-key", required=True, help="API Key (puede ser pública, pero no mostrará privados).")
    p.add_argument("--channel-id", required=True, help="ID del canal (ej: UCxxxx...)")
    p.add_argument("--output", default="all_videos.json", help="Archivo JSON de salida")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--client-secrets", default=None,
                   help="(opcional) Ruta a client_secrets.json para hacer OAuth y acceder a videos privados del canal.")
    return p.parse_args()


def make_uploads_playlist_id(channel_id: str) -> str:
    if not channel_id.startswith("UC"):
        raise ValueError("channelId debe comenzar por 'UC'")
    return "UU" + channel_id[2:]


def fetch_playlist_video_ids(api_key: str, playlist_id: str, verbose: bool, oauth_credentials: Optional[Any] = None) -> List[str]:
    """
    Si oauth_credentials se proporciona -> usa googleapiclient (autenticada) para leer la playlist (puede devolver privados).
    Si no -> usa requests + API key (solo públicos y unlisted).
    Devuelve lista de videoIds (strings).
    
    IMPORTANTE: Cuando oauth_credentials está presente, SIEMPRE usa OAuth para obtener todos los videos,
    incluyendo los privados. La paginación recorre todas las páginas hasta obtener todos los videos.
    """
    video_ids: List[str] = []
    next_token: Optional[str] = None
    page = 0

    if oauth_credentials:
        if verbose:
            print("[playlist] Usando OAuth para leer TODOS los videos (incluye privados).")
            print(f"[playlist] Playlist ID: {playlist_id}")
        
        # Refrescar credenciales si es necesario
        from google.auth.transport.requests import Request
        if oauth_credentials.expired and oauth_credentials.refresh_token:
            if verbose:
                print("[playlist] Refrescando credenciales OAuth...")
            oauth_credentials.refresh(Request())
        
        # Construir el cliente de YouTube con OAuth
        youtube = build("youtube", "v3", credentials=oauth_credentials)

        while True:
            page += 1
            if verbose:
                print(f"[playlist] Descargando página {page} (OAuth)...")

            try:
                req = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_token if next_token else None,
                )
                res = req.execute()

                items = res.get("items", [])
                page_video_count = 0
                for it in items:
                    vid = it.get("contentDetails", {}).get("videoId")
                    if vid:
                        video_ids.append(vid)
                        page_video_count += 1

                if verbose:
                    print(f"[playlist] Página {page}: {page_video_count} videos obtenidos (total acumulado: {len(video_ids)})")

                next_token = res.get("nextPageToken")
                if not next_token:
                    if verbose:
                        print("[playlist] No hay más páginas. Paginación completada.")
                    break
                    
            except Exception as e:
                if verbose:
                    print(f"[playlist] Error al obtener página {page}: {e}")
                raise
            
            time.sleep(0.1)

    else:
        if verbose:
            print("[playlist] Usando API key (solo públicos y unlisted).")
        session = requests.Session()
        while True:
            page += 1
            if verbose:
                print(f"[playlist] Descargando página {page} (API key)...")

            params = {
                "key": api_key,
                "playlistId": playlist_id,
                "part": "contentDetails",
                "maxResults": 50,
            }
            if next_token:
                params["pageToken"] = next_token

            resp = session.get(YOUTUBE_PLAYLIST_ITEMS_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                vid = item.get("contentDetails", {}).get("videoId")
                if vid:
                    video_ids.append(vid)

            next_token = data.get("nextPageToken")
            if not next_token:
                break
            time.sleep(0.1)

    if verbose:
        print(f"[playlist] Total videoIds obtenidos: {len(video_ids)}")
    return video_ids


def call_videos_list_with_session(session: requests.Session, api_key: Optional[str], ids: List[str], headers: Optional[Dict[str, str]] = None, verbose: bool = False) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    headers = headers or {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        params = {
            "part": "snippet,contentDetails,status",
            "id": ",".join(chunk)
        }
        if api_key:
            params["key"] = api_key

        if verbose:
            src = "API key" if api_key else "OAuth"
            print(f"[videos.list] solicitando {len(chunk)} ids con {src}...")

        resp = session.get(YOUTUBE_VIDEOS_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("items", []))
        time.sleep(0.1)
    return results


def fetch_videos_metadata(api_key: str, ids: List[str], verbose: bool, oauth_credentials: Optional[Any] = None):
    """
    1) intenta con API key (rápido).
    2) si faltan IDs y oauth_credentials está presente, reintenta esos con OAuth (Bearer token).
    3) marca los que siguen faltando como privados/eliminados/restrict.
    """
    session = requests.Session()
    raw_items = call_videos_list_with_session(session, api_key, ids, headers=None, verbose=verbose)

    found_ids: Set[str] = {it.get("id") for it in raw_items if it.get("id")}
    missing_ids = [vid for vid in ids if vid not in found_ids]

    if verbose:
        print(f"[metadata] Encontrados con API key: {len(found_ids)}. Faltantes: {len(missing_ids)}")

    oauth_items: List[Dict[str, Any]] = []
    if missing_ids and oauth_credentials:
        if verbose:
            print("[metadata] Reintentando IDs faltantes con OAuth (propietario del canal)...")
        token = oauth_credentials.token
        headers = {"Authorization": f"Bearer {token}"}
        oauth_items = call_videos_list_with_session(session, None, missing_ids, headers=headers, verbose=verbose)
        oauth_found = {it.get("id") for it in oauth_items if it.get("id")}
        if verbose:
            print(f"[metadata] Encontrados con OAuth: {len(oauth_found)}")
        found_ids |= oauth_found
        missing_ids = [vid for vid in missing_ids if vid not in oauth_found]

    all_items = raw_items + oauth_items

    for vid in missing_ids:
        all_items.append({
            "id": vid,
            "missing_reason": "private_or_deleted_or_restricted"
        })

    return all_items


def iso8601_to_seconds(duration: Optional[str]) -> Optional[int]:
    if not duration:
        return None
    try:
        return int(isodate.parse_duration(duration).total_seconds())
    except Exception:
        return None


def classify_type(duration_seconds: Optional[int]) -> str:
    if duration_seconds is None:
        return "unknown"
    return "short" if duration_seconds < 60 else "normal"


def run_oauth_flow(client_secrets_path: str, verbose: bool):
    scopes = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtubepartner"
    ]

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
    creds = flow.run_local_server(port=0)
    if verbose:
        print("[oauth] Credenciales obtenidas. Token expira en:", getattr(creds, "expiry", None))
    return creds


def main():
    args = parse_args()
    
    # Validar y construir el ID de la playlist de uploads
    playlist_id = make_uploads_playlist_id(args.channel_id)
    if args.verbose:
        print(f"[main] Channel ID: {args.channel_id}")
        print(f"[main] Playlist de uploads: {playlist_id}")
        print(f"[main] Verificación: UU + channelId[2:] = UU + {args.channel_id[2:]} = {playlist_id}")

    oauth_creds = None
    if args.client_secrets:
        if not Path(args.client_secrets).exists():
            raise FileNotFoundError("client_secrets.json no encontrado en: " + args.client_secrets)
        if args.verbose:
            print("[main] Iniciando flujo OAuth para acceso autenticado...")
        oauth_creds = run_oauth_flow(args.client_secrets, args.verbose)
        if args.verbose:
            print("[main] OAuth credentials obtenidas. Usando API autenticada para leer playlist.")
    else:
        if args.verbose:
            print("[main] No se proporcionó --client-secrets. Usando API key (solo videos públicos/unlisted).")

    # IMPORTANTE: Cuando oauth_creds está presente, fetch_playlist_video_ids SIEMPRE usa OAuth
    # para obtener todos los videos, incluyendo los privados
    video_ids = fetch_playlist_video_ids(args.api_key, playlist_id, args.verbose, oauth_credentials=oauth_creds)
    
    if args.verbose:
        print(f"[main] Total de video IDs obtenidos de la playlist: {len(video_ids)}")

    raw_items = fetch_videos_metadata(args.api_key, video_ids, args.verbose, oauth_credentials=oauth_creds)

    # Normalize / enriquecer
    enriched: List[Dict[str, Any]] = []
    for item in raw_items:
        vid = item.get("id")
        if item.get("missing_reason"):
            enriched.append({
                "id": vid,
                "title": None,
                "publishedAt": None,
                "duration": None,
                "duration_seconds": None,
                "type": None,
                "privacy": "private_or_deleted_or_restricted",
                "note": item.get("missing_reason")
            })
            continue

        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        status = item.get("status", {})

        duration_text = content.get("duration")
        duration_seconds = iso8601_to_seconds(duration_text)
        vtype = classify_type(duration_seconds)
        privacy = status.get("privacyStatus", "unknown")

        enriched.append({
            "id": vid,
            "title": snippet.get("title"),
            "publishedAt": snippet.get("publishedAt"),
            "duration": duration_text,
            "duration_seconds": duration_seconds,
            "type": vtype,
            "privacy": privacy
        })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Guardado {len(enriched)} items → {args.output}")


if __name__ == "__main__":
    main()
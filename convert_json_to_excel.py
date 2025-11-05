#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from openpyxl import Workbook


def parse_args():
    p = argparse.ArgumentParser(description="Convierte all_videos.json a Excel (.xlsx)")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()


def main():
    args = parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))

    # ✅ Ahora data es directamente una lista
    if not isinstance(data, list):
        raise ValueError("El JSON debe ser una lista de videos. Ejecuta el nuevo fetch_all_videos.py primero.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Videos"

    # Encabezados
    headers = [
        "id",
        "title",
        "publishedAt",
        "duration",
        "duration_seconds",
        "type",
        "privacy"
    ]
    ws.append(headers)

    # Filas
    for video in data:
        ws.append([
            video.get("id", ""),
            video.get("title", ""),
            video.get("publishedAt", ""),
            video.get("duration", ""),
            video.get("duration_seconds", ""),
            video.get("type", ""),
            video.get("privacy", "")
        ])

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)

    print(f"✅ Excel generado: {args.output}")


if __name__ == "__main__":
    main()

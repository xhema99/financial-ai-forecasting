import asyncio
import os
import sys

import winrt._winrt_windows_media_ocr as ocr
import winrt._winrt_windows_graphics_imaging as gi
import winrt._winrt_windows_storage as storage
import winrt._winrt_windows_storage_streams as streams

async def ocr_page(image_path):
    file = await storage.StorageFile.get_file_from_path_async(image_path)
    stream = await file.open_read_async()
    decoder = await gi.BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    from winrt._winrt_windows_globalization import Language
    lang = Language("es-ES")
    engine = ocr.OcrEngine.try_create_from_language(lang)
    if engine is None:
        engine = ocr.OcrEngine.try_create_from_language(Language("en-US"))
    if engine is None:
        return "No OCR engine available"

    result = await engine.recognize_async(bitmap)
    return result.text

async def main():
    base = r"C:\Users\Usuario\Desktop\financial-ai-forecasting-master\financial-ai-forecasting-master\enunciado\pages"
    for i in range(1, 13):
        path = os.path.join(base, f"page_{i}_hd.png")
        if not os.path.exists(path):
            path = os.path.join(base, f"page_{i}.png")
        if os.path.exists(path):
            print(f"\n{'='*60}")
            print(f"  PAGE {i}")
            print(f"{'='*60}")
            try:
                text = await ocr_page(path)
                if text.strip():
                    print(text)
                else:
                    print("[No text detected - image may be blank or unreadable]")
            except Exception as e:
                print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())

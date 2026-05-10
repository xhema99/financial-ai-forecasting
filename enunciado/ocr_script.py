import sys
import os
import asyncio
from winrt._winrt_windows_media_ocr import OcrEngine
from winrt._winrt_windows_graphics_imaging import (
    BitmapDecoder, SoftwareBitmap, BitmapPixelFormat
)
import winrt.system
from winrt.system import Object

async def ocr_image(image_path):
    # Load the file using Windows.Storage
    from winrt._winrt_windows_storage import StorageFile
    from winrt._winrt_windows_storage_streams import FileRandomAccessStream

    stream = FileRandomAccessStream.open_async_for_read_async(
        image_path
    )
    stream = await stream

    # Create bitmap decoder from stream
    decoder = await BitmapDecoder.create_async_async(stream)
    
    # Get software bitmap
    bitmap = await decoder.get_software_bitmap_async(BitmapPixelFormat.bgra8)
    
    # Try to create OCR engine for Spanish
    from winrt._winrt_windows_globalization import Language
    lang = Language("es-ES")
    engine = OcrEngine.try_create_from_language(lang)
    
    if engine is None:
        print("Spanish OCR not available, trying English...")
        lang = Language("en-US")
        engine = OcrEngine.try_create_from_language(lang)
    
    if engine is None:
        print("Falling back to default language...")
        engine = OcrEngine.try_create_from_language(Language(""))
    
    if engine is None:
        return "No OCR engine available"
    
    result = await engine.recognize_async(bitmap)
    return result.text

async def main():
    # Get the HD images
    base_dir = r"C:\Users\Usuario\Desktop\financial-ai-forecasting-master\financial-ai-forecasting-master\enunciado\pages"
    
    for i in range(9, 13):
        img_path = os.path.join(base_dir, f"page_{i}_hd.png")
        if os.path.exists(img_path):
            print(f"\n{'='*60}")
            print(f"  PAGE {i}")
            print(f"{'='*60}")
            try:
                text = await ocr_image(img_path)
                if text.strip():
                    print(text)
                else:
                    print("[No text detected]")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

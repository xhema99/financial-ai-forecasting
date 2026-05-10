Add-Type -AssemblyName System.Runtime.WindowsRuntime

$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]

$lang = [Windows.Globalization.Language]::new("es-ES")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)

if ($null -eq $engine) {
    Write-Host "Spanish OCR not available, trying English..."
    $lang = [Windows.Globalization.Language]::new("en-US")
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
}

if ($null -eq $engine) {
    Write-Host "No OCR engine available"
    exit 1
}

Write-Host "OCR Engine available for: $($engine.RecognizerLanguage)"
Write-Host ""

# Process pages 9-12
$basePath = "C:\Users\Usuario\Desktop\financial-ai-forecasting-master\financial-ai-forecasting-master\enunciado\pages"
for ($i = 9; $i -le 12; $i++) {
    $imgPath = Join-Path $basePath "page_${i}_hd.png"
    if (Test-Path $imgPath) {
        Write-Host "==================== PAGE $i ===================="
        
        # Load image
        $file = [Windows.Storage.StorageFile]::GetFileFromPathAsync($imgPath).GetAwaiter().GetResult()
        $stream = $file.OpenReadAsync().GetAwaiter().GetResult()
        
        # Decode
        $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetAwaiter().GetResult()
        $bitmap = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
        
        # OCR
        $result = $engine.RecognizeAsync($bitmap).GetAwaiter().GetResult()
        
        Write-Host $result.Text
        Write-Host ""
    }
}

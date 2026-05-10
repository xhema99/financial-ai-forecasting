Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime] | Out-Null
$lang = [Windows.Globalization.Language]::new("es-ES")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if ($engine -ne $null) {
    Write-Host "Spanish OCR available"
} else {
    Write-Host "Spanish OCR not available"
}

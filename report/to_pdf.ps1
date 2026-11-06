# Convert a .docx to PDF with Microsoft Word (exact rendering). Usage: to_pdf.ps1 <in.docx> <out.pdf>
param([string]$In, [string]$Out)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
  $doc = $word.Documents.Open((Resolve-Path $In).Path, $false, $true)
  $doc.SaveAs([ref]([IO.Path]::GetFullPath($Out)), [ref]17)
  "pages: " + $doc.ComputeStatistics(2)
  $doc.Close($false)
} finally { $word.Quit() }

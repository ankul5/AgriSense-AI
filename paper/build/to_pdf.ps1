# Converts every .docx in paper/out to PDF using installed Microsoft Word,
# refreshing the table of contents and fields first.
$out = Join-Path (Split-Path $PSScriptRoot -Parent) "out"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Get-ChildItem $out -Filter *.docx | Where-Object { $_.Name -notlike '~$*' } | ForEach-Object {
        $doc = $word.Documents.Open($_.FullName)
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
        $doc.Fields.Update() | Out-Null
        $doc.Repaginate()
        $doc.Save()
        $pdf = [IO.Path]::ChangeExtension($_.FullName, ".pdf")
        $doc.SaveAs([ref]$pdf, [ref]17)   # 17 = wdFormatPDF
        Write-Output ("{0}: {1} pages" -f $_.Name, $doc.ComputeStatistics(2))
        $doc.Close($false)
    }
} finally {
    $word.Quit()
}

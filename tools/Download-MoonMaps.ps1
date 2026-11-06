# Downloads every crescent visibility map listed on https://www.moonsighting.com/visibility.html
# into an organized folder next to this script. Safe to re-run: files already downloaded are skipped,
# and maps the site adds later (new Hijri years) are picked up automatically.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $here 'Moon Visibility Maps (moonsighting.com)'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$site = 'https://www.moonsighting.com/'

$months = @{
  muh = @(1,'Muharram');       sfr = @(2,'Safar');            rba = @(3,'Rabi al-Awwal');  rbt = @(4,'Rabi al-Thani')
  jmo = @(5,'Jumada al-Ula');  jmt = @(6,'Jumada al-Thani');  rjb = @(7,'Rajab');          shb = @(8,'Shaban')
  rmd = @(9,'Ramadan');        shw = @(10,'Shawwal');         zqd = @(11,'Dhul-Qadah');    zhj = @(12,'Dhul-Hijjah')
}
# Links on the site that point to a wrong filename -> the file that actually exists
$fix = @{
  '1451jmo_9-7-2029.gif'   = '1451jmo_9-10-2029.gif'
  '1455rmd_12-24-2033.gif' = '1455rmd_11-24-2033.gif'
  '1456jmt_8-18-2034.gif'  = '1456jmt_8-16-2034.gif'
}

Write-Host 'Reading the list of maps from moonsighting.com ...'
$html  = (Invoke-WebRequest -UseBasicParsing -Uri ($site + 'visibility.html')).Content
$fnRe  = New-Object Text.RegularExpressions.Regex('function\s+do(\d{4})([a-z]{3})\s*\(\)\s*\{(.*?)\}', [Text.RegularExpressions.RegexOptions]::Singleline)
$imgRe = New-Object Text.RegularExpressions.Regex('visibilitycurves/([^"]+?\.gif)')

$items = New-Object System.Collections.Generic.List[object]
foreach ($f in $fnRe.Matches($html)) {
  $ev = 0
  foreach ($m in $imgRe.Matches($f.Groups[3].Value)) {
    $ev++
    $orig = $m.Groups[1].Value
    $file = if ($fix.ContainsKey($orig)) { $fix[$orig] } else { $orig }
    $p = [regex]::Match($file, '^(\d{4})([a-z]{3})_(\d+)-(\d+)-(\d{4})\.gif$')
    if (-not $p.Success -or -not $months.ContainsKey($p.Groups[2].Value)) { continue }
    $c = $p.Groups[2].Value
    $items.Add([pscustomobject]@{
      Year = $p.Groups[1].Value; No = ('{0:00}' -f $months[$c][0]); Name = $months[$c][1]; Code = $c.ToUpper()
      Evening = $ev; Orig = $orig; File = $file
      Date = ('{0}-{1:00}-{2:00}' -f $p.Groups[5].Value, [int]$p.Groups[3].Value, [int]$p.Groups[4].Value)
    })
  }
}
Write-Host ("Found {0} maps. Downloading into:`n  {1}`n" -f $items.Count, $root)

$wc = New-Object Net.WebClient
$rows = New-Object System.Collections.Generic.List[object]
$i = 0; $saved = 0; $skipped = 0; $missing = 0
foreach ($it in $items) {
  $i++
  $sub  = '{0} AH\{1} {2} ({3})' -f $it.Year, $it.No, $it.Name, $it.Code
  $dir  = Join-Path $root $sub
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $fn   = '{0}-{1}_{2}_{3}_evening{4}.gif' -f $it.Year, $it.No, $it.Code, $it.Date, $it.Evening
  $dest = Join-Path $dir $fn
  $url  = $site + 'visibilitycurves/' + $it.File
  $status = if ($it.File -ne $it.Orig) { 'ok (site link broken; corrected filename)' } else { 'ok' }
  if ((Test-Path $dest) -and (Get-Item $dest).Length -gt 0) { $skipped++ }
  else {
    try { $wc.DownloadFile($url, $dest); $saved++ }
    catch { $status = 'missing on site'; $missing++; if (Test-Path $dest) { Remove-Item $dest -Force } }
  }
  $rel = if ($status -eq 'missing on site') { '' } else { ($sub -replace '\\','/') + '/' + $fn }
  $rows.Add([pscustomobject]@{ hijri_year=$it.Year; month_no=$it.No; month_name=$it.Name; code=$it.Code
    evening=$it.Evening; gregorian_date=$it.Date; file=$rel; source_url=$url; status=$status })
  if ($i % 25 -eq 0 -or $i -eq $items.Count) { Write-Host ("  {0,4} / {1}   {2}" -f $i, $items.Count, $sub) }
}

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $root 'index.csv')
@(
 'Crescent Moon Visibility Maps'
 'Source: https://www.moonsighting.com/visibility.html (OmegaHilalSighting, developed by Fawzi Kayali; criterion: Syed Khalid Shaukat)'
 ('Downloaded: ' + (Get-Date -Format 'yyyy-MM-dd'))
 ''
 'Layout:  <Hijri year> AH \ <month number> <month name> (<site code>) \ <file>'
 'File:    <year>-<month>_<CODE>_<Gregorian date YYYY-MM-DD>_evening<1-3>.gif'
 '         evening1 = day of the new moon (conjunction); evening2 and evening3 = the next two evenings.'
 '         Each map shows crescent visibility at local sunset on that evening.'
 ''
 'Legend:  A green = easily visible with naked eye  |  B cyan = visible if perfect conditions'
 '         C grey  = optical aid to find moon       |  D red  = visible with optical aid only'
 '         Yellow line = elongation 8 deg and moon altitude 5 deg'
 ''
 'index.csv lists every map with its Hijri month, evening, Gregorian date, file and original URL.'
 'Notes:   3 maps are linked on the site under wrong filenames; the correct files are downloaded instead'
 '         (1451 JMO evening1, 1455 RMD evening3, 1456 JMT evening3).'
 '         1463 Rabi al-Awwal evening3 (4 Mar 2041) does not exist on the site.'
 '         Re-run Download-MoonMaps.bat any time to fetch maps the site adds later.'
) | Set-Content -Encoding UTF8 -Path (Join-Path $root 'README.txt')

Write-Host ("`nDone. {0} downloaded, {1} already present, {2} missing on the site." -f $saved, $skipped, $missing)

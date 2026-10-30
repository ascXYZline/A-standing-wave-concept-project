param([string]$Project = '\\wsl.localhost\Ubuntu\home\ascline\seu\physics\wave')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$data = Get-Content -LiteralPath (Join-Path $Project 'narration/script.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
$synth.SelectVoice($data.voice)
$synth.Rate = $data.rate
$synth.Volume = 100
try {
    foreach ($cue in $data.cues) {
        $target = Join-Path $Project ('assets/audio/' + $cue.id + '.wav')
        $synth.SetOutputToWaveFile($target)
        $synth.Speak($cue.text)
        $synth.SetOutputToNull()
        Write-Output ('Recorded ' + $cue.id)
    }
} finally { $synth.Dispose() }

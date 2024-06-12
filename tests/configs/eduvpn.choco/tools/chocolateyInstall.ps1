$ErrorActionPreference = 'Stop';

$packageArgs = @{
  packageName     = 'eduvpn'
  fileType        = 'EXE'
  file            = "${ENV:TEMP}\eduvpn.exe"
  url             = 'https://app.eduvpn.org/windows/eduVPNClient_$VERSION.exe'
  checksum        = 'A596C3E4D9C3A2748202ED08D662D076'
  silentArgs      = '/install /quiet /norestart /log "C:\ProgramData\chocolatey\logs\eduvpn.log"'
  softwareName    = 'eduVPN Client*'
}

Get-ChocolateyWebFile @packageArgs
Install-ChocolateyInstallPackage @packageArgs
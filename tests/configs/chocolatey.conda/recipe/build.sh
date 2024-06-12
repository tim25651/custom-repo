cert-sync --user /etc/ssl/certs/ca-certificates.crt
bash build.sh
mkdir $PREFIX/opt
mv code_drop/temp/_PublishedApps/choco $PREFIX/opt/chocolatey
mv code_drop/temp/_PublishedLibs/chocolatey $PREFIX/opt/chocolatey/lib
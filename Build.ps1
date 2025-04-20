$protoInputDir = "In"
$protoOutputDir = "Out"

if (Test-Path $protoOutputDir) {
    Write-Host "Clearing output folder: $protoOutputDir"
    Remove-Item "$protoOutputDir\*" -Recurse -Force
} else {
    Write-Host "Creating output folder: $protoOutputDir"
    New-Item -ItemType Directory -Path $protoOutputDir | Out-Null
}

$protocPath = "protoc"

$protoFiles = Get-ChildItem -Path $protoInputDir -Filter *.proto

foreach ($file in $protoFiles) {
    Write-Host "Compiling $($file.Name)..."
    & $protocPath --cpp_out=lite:$protoOutputDir --proto_path=$protoInputDir $file
}

pause
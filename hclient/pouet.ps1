# Convertir la clé hexadécimale en tableau de bytes
$cleHex = "19e02982cd3b903aa94513659521a36502c5e4e4f80ddcc691a2e9d1d94c07e4"
$cleBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($cleHex))

# Créer un objet Clé AES
$cleAES = New-Object System.Security.Cryptography.AesManaged
$cleAES.Mode = [System.Security.Cryptography.CipherMode]::CBC
$cleAES.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7

# Définir la clé pour l'objet Clé AES
$cleAES.Key = $cleBytes

# Convertir le texte en bytes
$texte = [System.Text.Encoding]::UTF8.GetBytes("Bonjour, monde!")

# Créer un objet de chiffrement AES
$chiffrement = $cleAES.CreateEncryptor()

# Chiffrer le texte
$texteChiffre = $chiffrement.TransformFinalBlock($texte, 0, $texte.Length)

# Convertir le texte chiffré en base64
$texteChiffreBase64 = [System.Convert]::ToBase64String($texteChiffre)

Write-Host "Texte chiffré: $texteChiffreBase64"

# Déchiffrer le texte
$dechiffrement = $cleAES.CreateDecryptor()
$texteDechiffre = $dechiffrement.TransformFinalBlock($texteChiffre, 0, $texteChiffre.Length)

# Convertir le texte déchiffré en chaîne UTF-8
$texteDechiffreUTF8 = [System.Text.Encoding]::UTF8.GetString($texteDechiffre)

Write-Host "Texte déchiffré: $texteDechiffreUTF8"

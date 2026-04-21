# El ZIP se genera externamente con build_lambda.ps1 que incluye dependencias pip.
# terraform no puede instalar pip deps, así que referenciamos el ZIP pre-construido.
locals {
  user_zip_path = abspath("${path.module}/user_service.zip")
  user_zip_hash = fileexists(local.user_zip_path) ? filebase64sha256(local.user_zip_path) : "missing_zip"
}

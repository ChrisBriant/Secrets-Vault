# Vault Secret Rotation

A small Python project for experimenting with HashiCorp Vault and secret management, including storing and rotating credentials.

## Installing Vault

This project uses the local HashiCorp Vault Community Edition.

On Ubuntu/WSL:

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release) main" | \
sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt update
sudo apt install vault

## Check the Installation

vault version

## Running Vault

vault server -dev

The server will display a root token when it starts. Copy this value to the environment variable "VAULT TOKEN"


## RUNNING FASTAPI
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
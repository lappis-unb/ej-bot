#!/bin/bash

load_env_variable() {
  local var_name=$1
  if [ -f .env ]; then
    echo $(grep $var_name ../variables.env | cut -d '=' -f2-)
  else
    echo ""
  fi
}

is_empty() {
  local var_value=$1
  [ -z "$var_value" ]
}

download_files() {
  local repo_url=$1
  local temp_dir=$(mktemp -d)

  echo "Baixando arquivos do repositório Git..."
  curl -L $repo_url/archive/refs/heads/main.zip -o $temp_dir/main.zip
  unzip $temp_dir/main.zip -d $temp_dir

  echo "Copiando arquivos para o diretório do projeto..."
  cp -r $temp_dir/*/data .
  cp $temp_dir/*/domain.yml .

  echo "Limpando arquivos temporários..."
  rm -rf $temp_dir
}

train_rasa() {
  echo "Executando o treinamento do Rasa..."
  rasa train -vv --domain domain.yml
}

RASA_TRAIN_GIT_URL=$(load_env_variable "RASA_TRAIN_GIT_URL")

if is_empty "$RASA_TRAIN_GIT_URL"; then
  echo "RASA_TRAIN_GIT_URL não está definido ou está vazio no arquivo .env. Continuando com o treinamento sem baixar arquivos..."
  train_rasa
  exit 0
fi

if [ ! -d "data" ] || [ ! -f "domain.yml" ]; then
  echo "Diretório 'data' ou arquivo 'domain.yml' não encontrado."
  download_files $RASA_TRAIN_GIT_URL
else
  echo "Diretório 'data' e arquivo 'domain.yml' encontrados. Continuando com o treinamento..."
fi

train_rasa

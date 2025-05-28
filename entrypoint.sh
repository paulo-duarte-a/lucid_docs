#!/bin/bash
set -e

if [ "$ENVIRONMENT" = "dsv" ]; then
    echo "Ambiente de desenvolvimento (dsv) detectado. Executando testes e iniciando servidor de desenvolvimento..."
    pytest --maxfail=0 --disable-warnings || exit 1
    uvicorn lucid_docs.main:create_app --host 0.0.0.0 --port 8000 --reload
else
    echo "Ambiente de produção detectado. Iniciando servidor de produção..."
    uvicorn lucid_docs.main:create_app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --no-server-header
fi
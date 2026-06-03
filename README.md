# Guía Rápida: Ejecución y Pruebas con Docker (SBAC)

Este proyecto está empaquetado en un contenedor Docker para garantizar que el Sistema Básico de Administración de Configuración (SBAC) y sus pruebas automatizadas se ejecuten en un entorno Linux aislado y reproducible (Python 3.11).

## 1. Construir la Imagen de Docker

Antes de ejecutar el sistema o las pruebas, necesitas construir la imagen localmente. Abre tu terminal en la carpeta raíz del proyecto (donde se encuentra el archivo `Dockerfile`) y ejecuta el siguiente comando:

```bash
docker build -t sbac-tests .
```

**Nota:** Este proceso descargará las dependencias necesarias de manera automática, incluyendo `pytest` y `pytest-cov`.

## 2. Ejecutar las Pruebas Automatizadas

Para correr la batería de 15 pruebas automatizadas (Unitarias, Integración y Regresión) y ver el reporte de cobertura de código al 99%, ejecuta el contenedor de forma estándar. El contenedor correrá las pruebas y se eliminará automáticamente al terminar:

```bash
docker run --rm sbac-tests
```

## 3. Probar el Sistema Manualmente

Si deseas interactuar con la herramienta `sbac` manualmente, crear archivos, hacer commits y probar el flujo completo, debes abrir el contenedor en modo interactivo.

Ejecuta el siguiente comando para entrar a la terminal virtual del contenedor:

```bash
docker run -it --rm sbac-tests /bin/bash
```

Una vez dentro de la terminal del contenedor, puedes utilizar el sistema libremente siguiendo este ejemplo básico de flujo de trabajo:

```bash
# 1. Inicializa el repositorio
python sbac.py init

# 2. Crea un archivo de prueba rápido
echo "Hola Mundo" > prueba.txt

# 3. Añade el archivo al seguimiento
python sbac.py add prueba.txt

# 4. Revisa el estado del repositorio
python sbac.py status

# 5. Guarda tu primera versión
python sbac.py commit "Mi primer commit manual"

# 6. Revisa el historial de versiones registradas
python sbac.py history
```

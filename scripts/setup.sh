#!/bin/bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Bogotá Traffic - Setup Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Verificar .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env no encontrado${NC}"
    echo -e "${YELLOW}Creando .env desde .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env creado${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANTE: Configura las variables en .env antes de continuar${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example no encontrado${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ .env encontrado${NC}\n"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker instalado: $(docker --version)${NC}"

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose instalado: $(docker-compose --version)${NC}\n"

# Crear carpetas de datos si no existen
echo -e "${BLUE}📁 Creando carpetas de datos...${NC}"
mkdir -p data/pkls
mkdir -p data/snapshots
echo -e "${GREEN}✅ Carpetas creadas${NC}\n"

# Parar contenedores existentes
echo -e "${BLUE}🛑 Parando contenedores existentes...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ Contenedores parados${NC}\n"

# Construir imágenes
echo -e "${BLUE}🔨 Construyendo imágenes Docker...${NC}"
docker-compose build
echo -e "${GREEN}✅ Imágenes construidas${NC}\n"

# Levantar PostgreSQL y Redis
echo -e "${BLUE}🚀 Iniciando PostgreSQL y Redis...${NC}"
docker-compose up -d postgres redis
echo -e "${GREEN}✅ Servicios iniciados${NC}\n"

# Esperar a que PostgreSQL esté listo
echo -e "${BLUE}⏳ Esperando PostgreSQL (esto puede tomar 30-60 segundos)...${NC}"
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T postgres pg_isready -U traffic_admin &>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL está listo${NC}\n"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "\n${RED}❌ Timeout esperando PostgreSQL${NC}"
    docker-compose logs postgres
    exit 1
fi

# Ejecutar migraciones SQL
echo -e "${BLUE}📊 Ejecutando migraciones de base de datos...${NC}"
docker-compose exec -T postgres psql -U traffic_admin -d bogota_traffic -f /docker-entrypoint-initdb.d/schema.sql
docker-compose exec -T postgres psql -U traffic_admin -d bogota_traffic -f /docker-entrypoint-initdb.d/indexes.sql
echo -e "${GREEN}✅ Base de datos configurada${NC}\n"

# Verificar Redis
echo -e "${BLUE}⏳ Verificando Redis...${NC}"
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ Redis está listo${NC}\n"
else
    echo -e "${RED}❌ Redis no responde${NC}"
    exit 1
fi

# Mostrar estado de servicios
echo -e "${BLUE}📋 Estado de servicios:${NC}"
docker-compose ps

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Setup completado exitosamente${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Próximos pasos:${NC}"
echo -e "  1. Asegúrate de tener CARLA corriendo localmente en el puerto 2000"
echo -e "  2. Ejecuta: ${BLUE}docker-compose up app${NC}"
echo -e "  3. La API estará disponible en: ${BLUE}http://localhost:8000${NC}\n"

echo -e "${YELLOW}Comandos útiles:${NC}"
echo -e "  Ver logs:        ${BLUE}docker-compose logs -f app${NC}"
echo -e "  Parar servicios: ${BLUE}docker-compose down${NC}"
echo -e "  Reiniciar:       ${BLUE}docker-compose restart${NC}\n"

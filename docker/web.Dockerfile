# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copiar package files
COPY apps/web/package*.json ./

# Instalar patch-package globalmente y dependencias
RUN npm install -g patch-package && npm ci

# Copiar código fuente
COPY apps/web .

# Permitir configurar la API en build time (Vite lee variables VITE_*)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build de producción
RUN npm run build

# Production stage
FROM nginx:alpine

# Copiar build a nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración nginx personalizada si existe
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 80

# Comando por defecto
CMD ["nginx", "-g", "daemon off;"]

# 🚀 Instalación Rápida - AFOROS RILSA v3.0.2

## Estado Actual
✅ **Código compilado y listo**  
⚠️ **Dependencias pendientes de instalar**

## Por qué hay errores en el IDE

Los errores que ves (rojo en el editor) son **NORMALES**:
- React, Vite, Tailwind no están instalados aún
- Python type-checking es stricto (por diseño)
- **Desaparecerán después de la instalación**

## ⚡ Instalación (2 minutos)

### Opción 1: Automática (Windows)
```bash
cd c:\Users\David\aforos
start.bat
```
Luego abre: **http://localhost:3000?dataset=gx010323**

### Opción 2: Automática (Linux/Mac)
```bash
cd ~/aforos
chmod +x start.sh
./start.sh
```

### Opción 3: Manual

**Terminal 1 - Backend:**
```bash
cd c:\Users\David\aforos\api
pip install -r requirements.txt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd c:\Users\David\aforos\apps\web
npm install
npm run dev
```

## ✅ Verificación

Cuando veas esto, está funcionando:

```
✓ API en http://localhost:3004
✓ Frontend en http://localhost:3000
✓ Swagger docs en http://localhost:3004/docs
```

## 🔧 Si hay problemas

**Para limpiar y reinstalar:**
```bash
# Backend
cd api
pip cache purge
pip install -r requirements.txt

# Frontend
cd ../apps/web
rm -rf node_modules package-lock.json
npm install
```

**Para verificar instalación:**
```bash
cd aforos
python verify_install.py
```

## 📝 Notas

- Los errores rojos en VS Code desaparecerán tras instalar
- Ignora los warnings de Tailwind CSS (@tailwind)
- La app carga en **http://localhost:3000**
- API disponible en **http://localhost:3004**

---

**¿Necesitas ayuda?** Revisa:
- `INICIO_RAPIDO.md` (5 min)
- `ARQUITECTURA_TECNICA.md` (detalles)
- `CHECKLIST_VALIDACION.md` (validar paso a paso)

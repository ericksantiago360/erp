# ERP Digital

Un sistema ERP moderno para empresas digitales, desarrollado con Flask, SQLAlchemy y Bootstrap 5.

## Características

- Gestión de usuarios y roles
- Gestión de empresas
- Gestión de productos
- Gestión de clientes
- Gestión de ventas
- Reportes y análisis
- Interfaz moderna y responsive

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/erp-digital.git
cd erp-digital
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. Inicializar la base de datos:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Uso

1. Iniciar el servidor de desarrollo:
```bash
flask run
```

2. Acceder a la aplicación en tu navegador:
```
http://localhost:5000
```

3. Credenciales por defecto:
- Email: admin@sistema.com
- Contraseña: admin123

## Estructura del Proyecto

```
erp-digital/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias
├── static/            # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── img/
├── templates/         # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── dashboard.html
└── README.md
```

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@ejemplo.com

Link del Proyecto: [https://github.com/tu-usuario/erp-digital](https://github.com/tu-usuario/erp-digital) 
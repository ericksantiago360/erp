# app.py - Archivo principal de la aplicación Flask

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# Inicialización de la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_del_erp'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de la base de datos
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos de base de datos
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # 'admin', 'gerente', 'empleado'
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'digital', 'fisica'
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    usuarios = db.relationship('Usuario', backref='empresa', lazy=True)
    productos = db.relationship('Producto', backref='empresa', lazy=True)
    ventas = db.relationship('Venta', backref='empresa', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    tipo = db.Column(db.String(20))  # 'fisico', 'digital', 'servicio'
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    detalles_venta = db.relationship('DetalleVenta', backref='producto', lazy=True)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # 'pendiente', 'pagado', 'enviado', 'entregado'
    metodo_pago = db.Column(db.String(50))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

class DetalleVenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rutas
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = Usuario.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Email o contraseña incorrectos')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener estadísticas para el dashboard
    total_ventas = Venta.query.filter_by(empresa_id=current_user.empresa_id).count()
    total_clientes = Cliente.query.filter_by(empresa_id=current_user.empresa_id).count()
    total_productos = Producto.query.filter_by(empresa_id=current_user.empresa_id).count()
    
    # Calcular ingresos de hoy
    hoy = datetime.now().date()
    ventas_hoy = Venta.query.filter(
        Venta.empresa_id == current_user.empresa_id,
        db.func.date(Venta.fecha) == hoy
    ).all()
    ingresos_hoy = sum(venta.total for venta in ventas_hoy)
    
    # Obtener últimas ventas
    ultimas_ventas = Venta.query.filter_by(empresa_id=current_user.empresa_id)\
        .order_by(Venta.fecha.desc())\
        .limit(5)\
        .all()
    
    # Obtener productos con bajo stock
    productos_bajo_stock = Producto.query.filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.stock <= 10
    ).all()
    
    return render_template('dashboard.html',
                         total_ventas=total_ventas,
                         total_clientes=total_clientes,
                         total_productos=total_productos,
                         ingresos_hoy=ingresos_hoy,
                         ultimas_ventas=ultimas_ventas,
                         productos_bajo_stock=productos_bajo_stock)

@app.route('/empresas')
@login_required
def empresas():
    if current_user.rol != 'admin':
        flash('No tiene permisos para acceder a esta sección')
        return redirect(url_for('dashboard'))
    
    empresas = Empresa.query.all()
    return render_template('empresas.html', empresas=empresas)

@app.route('/nueva-empresa', methods=['GET', 'POST'])
@login_required
def nueva_empresa():
    if current_user.rol != 'admin':
        flash('No tiene permisos para acceder a esta sección')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo = request.form.get('tipo')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        
        nueva_empresa = Empresa(
            nombre=nombre,
            tipo=tipo,
            direccion=direccion,
            telefono=telefono,
            email=email
        )
        
        db.session.add(nueva_empresa)
        db.session.commit()
        flash('Empresa creada exitosamente')
        return redirect(url_for('empresas'))
    
    return render_template('nueva_empresa.html')

@app.route('/empresa/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_empresa(id):
    if current_user.rol != 'admin':
        flash('No tiene permisos para editar empresas')
        return redirect(url_for('dashboard'))
    
    empresa = Empresa.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            empresa.nombre = request.form.get('nombre')
            empresa.tipo = request.form.get('tipo')
            empresa.direccion = request.form.get('direccion')
            empresa.telefono = request.form.get('telefono')
            empresa.email = request.form.get('email')
            
            db.session.commit()
            flash('Empresa actualizada exitosamente')
            return redirect(url_for('empresas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la empresa: {str(e)}')
            return redirect(url_for('editar_empresa', id=id))
    
    return render_template('nueva_empresa.html', empresa=empresa)

@app.route('/productos')
@login_required
def productos():
    productos = Producto.query.filter_by(empresa_id=current_user.empresa_id).all()
    return render_template('productos.html', productos=productos)

@app.route('/nuevo-producto', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = float(request.form.get('precio'))
        stock = int(request.form.get('stock'))
        tipo = request.form.get('tipo')
        
        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            tipo=tipo,
            empresa_id=current_user.empresa_id
        )
        
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto creado exitosamente')
        return redirect(url_for('productos'))
    
    return render_template('nuevo_producto.html')

@app.route('/editar-producto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    # Verificar que el producto pertenece a la empresa del usuario
    if producto.empresa_id != current_user.empresa_id:
        flash('No tiene permisos para editar este producto')
        return redirect(url_for('productos'))
    
    if request.method == 'POST':
        producto.nombre = request.form.get('nombre')
        producto.descripcion = request.form.get('descripcion')
        producto.precio = float(request.form.get('precio'))
        producto.stock = int(request.form.get('stock'))
        producto.tipo = request.form.get('tipo')
        
        try:
            db.session.commit()
            flash('Producto actualizado exitosamente')
            return redirect(url_for('productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}')
            return redirect(url_for('editar_producto', id=id))
    
    return render_template('nuevo_producto.html', producto=producto)

@app.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.filter_by(empresa_id=current_user.empresa_id).all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/nuevo-cliente', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        
        nuevo_cliente = Cliente(
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            empresa_id=current_user.empresa_id
        )
        
        try:
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash('Cliente creado exitosamente')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el cliente: {str(e)}')
            return redirect(url_for('nuevo_cliente'))
    
    return render_template('nuevo_cliente.html')

@app.route('/editar-cliente/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Verificar que el cliente pertenece a la empresa del usuario
    if cliente.empresa_id != current_user.empresa_id:
        flash('No tiene permisos para editar este cliente')
        return redirect(url_for('clientes'))
    
    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.email = request.form.get('email')
        cliente.telefono = request.form.get('telefono')
        cliente.direccion = request.form.get('direccion')
        
        try:
            db.session.commit()
            flash('Cliente actualizado exitosamente')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {str(e)}')
            return redirect(url_for('editar_cliente', id=id))
    
    return render_template('nuevo_cliente.html', cliente=cliente)

@app.route('/ventas')
@login_required
def ventas():
    ventas = Venta.query.filter_by(empresa_id=current_user.empresa_id).all()
    return render_template('ventas.html', ventas=ventas)

@app.route('/nueva-venta', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    if request.method == 'POST':
        cliente_id = int(request.form.get('cliente_id'))
        metodo_pago = request.form.get('metodo_pago')
        
        # Crear la venta
        nueva_venta = Venta(
            total=0,  # Se actualizará después de agregar los detalles
            estado='pendiente',
            metodo_pago=metodo_pago,
            cliente_id=cliente_id,
            empresa_id=current_user.empresa_id
        )
        
        db.session.add(nueva_venta)
        db.session.flush()  # Para obtener el ID de la venta
        
        # Procesar los productos vendidos
        productos = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        
        total_venta = 0
        
        for i in range(len(productos)):
            producto_id = int(productos[i])
            cantidad = int(cantidades[i])
            
            producto = Producto.query.get(producto_id)
            subtotal = producto.precio * cantidad
            
            detalle = DetalleVenta(
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal,
                venta_id=nueva_venta.id,
                producto_id=producto_id
            )
            
            db.session.add(detalle)
            total_venta += subtotal
            
            # Actualizar el stock del producto
            producto.stock -= cantidad
        
        nueva_venta.total = total_venta
        db.session.commit()
        flash('Venta creada exitosamente')
        return redirect(url_for('ventas'))
    
    clientes = Cliente.query.filter_by(empresa_id=current_user.empresa_id).all()
    productos = Producto.query.filter_by(empresa_id=current_user.empresa_id).all()
    return render_template('nueva_venta.html', clientes=clientes, productos=productos)

@app.route('/reportes')
@login_required
def reportes():
    return render_template('reportes.html')

@app.route('/api/ventas-por-mes')
@login_required
def ventas_por_mes():
    # Aquí iría la lógica para obtener las ventas por mes
    # Este es un ejemplo simplificado
    data = [
        {"mes": "Enero", "ventas": 12000},
        {"mes": "Febrero", "ventas": 15000},
        {"mes": "Marzo", "ventas": 18000},
        # ... más datos
    ]
    return jsonify(data)

@app.route('/venta/<int:id>')
@login_required
def detalle_venta(id):
    venta = Venta.query.get_or_404(id)
    
    # Verificar que la venta pertenece a la empresa del usuario
    if venta.empresa_id != current_user.empresa_id:
        flash('No tiene permisos para ver esta venta')
        return redirect(url_for('ventas'))
    
    return render_template('detalle_venta.html', venta=venta)

@app.route('/venta/<int:id>/pagar', methods=['POST'])
@login_required
def marcar_como_pagado(id):
    venta = Venta.query.get_or_404(id)
    
    # Verificar que la venta pertenece a la empresa del usuario
    if venta.empresa_id != current_user.empresa_id:
        flash('No tiene permisos para modificar esta venta')
        return redirect(url_for('ventas'))
    
    venta.estado = 'pagado'
    db.session.commit()
    flash('Venta marcada como pagada')
    return redirect(url_for('detalle_venta', id=id))

@app.route('/venta/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_venta(id):
    venta = Venta.query.get_or_404(id)
    
    # Verificar que la venta pertenece a la empresa del usuario
    if venta.empresa_id != current_user.empresa_id:
        flash('No tiene permisos para eliminar esta venta')
        return redirect(url_for('ventas'))
    
    try:
        # Eliminar los detalles de la venta
        for detalle in venta.detalles:
            # Restaurar el stock de los productos
            producto = detalle.producto
            producto.stock += detalle.cantidad
            db.session.delete(detalle)
        
        db.session.delete(venta)
        db.session.commit()
        flash('Venta eliminada exitosamente')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la venta: {str(e)}')
    
    return redirect(url_for('ventas'))

@app.route('/venta/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_venta(id):
    venta = Venta.query.get_or_404(id)
    
    # Verificar que la venta pertenece a la empresa del usuario
    if venta.empresa_id != current_user.empresa_id:
        flash('No tiene permisos para editar esta venta')
        return redirect(url_for('ventas'))
    
    if request.method == 'POST':
        try:
            # Obtener los datos del formulario
            cliente_id = int(request.form.get('cliente_id'))
            metodo_pago = request.form.get('metodo_pago')
            
            # Verificar que el cliente pertenece a la empresa
            cliente = Cliente.query.get_or_404(cliente_id)
            if cliente.empresa_id != current_user.empresa_id:
                flash('Cliente no válido')
                return redirect(url_for('editar_venta', id=id))
            
            # Actualizar datos básicos de la venta
            venta.cliente_id = cliente_id
            venta.metodo_pago = metodo_pago
            
            # Procesar los productos
            productos = request.form.getlist('producto_id[]')
            cantidades = request.form.getlist('cantidad[]')
            
            # Eliminar detalles existentes y restaurar stock
            for detalle in venta.detalles:
                producto = detalle.producto
                producto.stock += detalle.cantidad
                db.session.delete(detalle)
            
            # Agregar nuevos detalles
            total_venta = 0
            for i in range(len(productos)):
                producto_id = int(productos[i])
                cantidad = int(cantidades[i])
                
                producto = Producto.query.get_or_404(producto_id)
                if producto.empresa_id != current_user.empresa_id:
                    flash('Producto no válido')
                    return redirect(url_for('editar_venta', id=id))
                
                if cantidad > producto.stock:
                    flash(f'No hay suficiente stock para el producto {producto.nombre}')
                    return redirect(url_for('editar_venta', id=id))
                
                subtotal = producto.precio * cantidad
                total_venta += subtotal
                
                detalle = DetalleVenta(
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    subtotal=subtotal,
                    venta_id=venta.id,
                    producto_id=producto_id
                )
                
                db.session.add(detalle)
                producto.stock -= cantidad
            
            venta.total = total_venta
            db.session.commit()
            flash('Venta actualizada exitosamente')
            return redirect(url_for('detalle_venta', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la venta: {str(e)}')
            return redirect(url_for('editar_venta', id=id))
    
    # Obtener datos para el formulario
    clientes = Cliente.query.filter_by(empresa_id=current_user.empresa_id).all()
    productos = Producto.query.filter_by(empresa_id=current_user.empresa_id).all()
    
    return render_template('nueva_venta.html', 
                         venta=venta,
                         clientes=clientes,
                         productos=productos)

def init_app():
    # Crear las tablas e inicializar la base de datos
    with app.app_context():
        db.create_all()
        
        # Crear empresa por defecto si no existe
        empresa_default = Empresa.query.filter_by(nombre='Empresa Default').first()
        if not empresa_default:
            empresa_default = Empresa(
                nombre='Empresa Default',
                tipo='digital',
                direccion='Dirección por defecto',
                telefono='0000000000',
                email='default@empresa.com'
            )
            db.session.add(empresa_default)
            db.session.commit()
        
        # Crear usuario administrador si no existe
        admin = Usuario.query.filter_by(email='admin@sistema.com').first()
        if not admin:
            admin = Usuario(
                nombre='Administrador',
                email='admin@sistema.com',
                rol='admin',
                empresa_id=empresa_default.id  # Asignar la empresa por defecto
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_app()
    app.run(debug=True)
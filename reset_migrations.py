import os

def delete_migrations():
    apps = [
        'app_ventas',
        'app_finanzas',
        'app_usuarios',
        'app_inventario',
        'app_eventos',
        'app_administracion',
        'app_pedidos',
        'app_reportes'
    ]
    
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            for filename in os.listdir(migrations_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    os.remove(os.path.join(migrations_dir, filename))
            print(f"Deleted migrations for {app}")

if __name__ == '__main__':
    delete_migrations()
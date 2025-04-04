import os
import shutil

def clean_migrations():
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
        migrations_path = os.path.join(app, 'migrations')
        if os.path.exists(migrations_path):
            # Remove migrations folder
            shutil.rmtree(migrations_path)
            # Create new migrations folder
            os.makedirs(migrations_path)
            # Create __init__.py
            open(os.path.join(migrations_path, '__init__.py'), 'w').close()
            print(f"Cleaned migrations for {app}")

if __name__ == '__main__':
    clean_migrations()
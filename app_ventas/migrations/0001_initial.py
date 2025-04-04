# Generated by Django 5.1.1 on 2025-03-31 03:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_inventario', '0001_initial'),
        ('app_usuarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('completada', 'Completada'), ('cancelada', 'Cancelada')], default='pendiente', max_length=20)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('creado_por', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ventas_creadas', to='app_usuarios.profile')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_usuarios.profile')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ventas_modificadas', to='app_usuarios.profile')),
            ],
        ),
        migrations.CreateModel(
            name='VentaDetalle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_inventario.producto')),
                ('venta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='app_ventas.venta')),
            ],
        ),
    ]

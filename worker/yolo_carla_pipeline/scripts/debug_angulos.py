"""
Debug de cálculo de ángulos
"""

import numpy as np

# Centro
cx, cy = 500, 500

# Puntos de prueba
puntos = {
    'Norte (arriba)': (500, 200),
    'Sur (abajo)': (500, 800),
    'Oeste (izquierda)': (200, 500),
    'Este (derecha)': (800, 500)
}

print("=" * 80)
print("DEBUG: Cálculo de Ángulos")
print("=" * 80)
print(f"\nCentro: ({cx}, {cy})")

for nombre, (x, y) in puntos.items():
    dx = x - cx
    dy_original = y - cy
    dy_invertido = -(y - cy)

    angulo_original = np.degrees(np.arctan2(dy_original, dx))
    angulo_invertido = np.degrees(np.arctan2(dy_invertido, dx))

    if angulo_original < 0:
        angulo_original += 360
    if angulo_invertido < 0:
        angulo_invertido += 360

    print(f"\n{nombre}: ({x}, {y})")
    print(f"  dx = {dx}, dy_orig = {dy_original}, dy_inv = {dy_invertido}")
    print(f"  Ángulo (método original): {angulo_original:.1f}°")
    print(f"  Ángulo (dy invertido):    {angulo_invertido:.1f}°")

    # Determinar acceso con rangos corregidos (dy invertido)
    if 45 <= angulo_invertido < 135:
        acceso = "NORTE"
    elif 135 <= angulo_invertido < 225:
        acceso = "OESTE"  # CORREGIDO
    elif 225 <= angulo_invertido < 315:
        acceso = "SUR"    # CORREGIDO
    else:
        acceso = "ESTE"

    correcto = nombre.split()[0].upper()
    print(f"  Acceso detectado: {acceso} {'✓' if acceso == correcto else '❌ (esperaba ' + correcto + ')'}")

print("\n" + "=" * 80)
print("Rangos de ángulos (con dy invertido):")
print("=" * 80)
print("Norte:  45° - 135°  (arriba)")
print("Sur:   135° - 225°  (abajo)")
print("Oeste: 225° - 315°  (izquierda)")
print("Este:  315° - 45°   (derecha)")
print("=" * 80)

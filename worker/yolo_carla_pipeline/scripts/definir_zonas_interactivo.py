"""
Script Interactivo para Definir Zonas de Acceso RILSA
=====================================================

Herramienta simple para crear archivos de zonas haciendo click en un frame del video.

Uso:
    python definir_zonas_interactivo.py --video video.mp4 --salida zonas.json
    python definir_zonas_interactivo.py --frame frame.jpg --salida zonas.json

Instrucciones:
    1. Haz click en las 4 esquinas de cada zona de acceso
    2. Presiona ESPACIO para guardar la zona actual
    3. Presiona R para resetear la zona actual
    4. Presiona Q para terminar y guardar

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import cv2
import json
import argparse
import sys
from pathlib import Path

class DefinidorZonas:
    def __init__(self, imagen_path: str):
        self.imagen = cv2.imread(imagen_path)
        if self.imagen is None:
            raise ValueError(f"No se pudo cargar imagen: {imagen_path}")

        self.imagen_display = self.imagen.copy()
        self.puntos_actuales = []
        self.zonas = {}
        self.zona_actual = None
        self.accesos_pendientes = ['norte', 'sur', 'este', 'oeste']

        self.colores = {
            'norte': (255, 0, 0),    # Azul
            'sur': (0, 255, 0),       # Verde
            'este': (0, 0, 255),      # Rojo
            'oeste': (255, 255, 0)    # Cian
        }

    def click_handler(self, event, x, y, flags, param):
        """Maneja clicks del mouse"""
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.puntos_actuales) < 4:
                self.puntos_actuales.append([x, y])
                print(f"  Punto {len(self.puntos_actuales)}: [{x}, {y}]")

                # Dibujar punto
                cv2.circle(self.imagen_display, (x, y), 5, (0, 255, 0), -1)

                # Dibujar línea al punto anterior
                if len(self.puntos_actuales) > 1:
                    cv2.line(
                        self.imagen_display,
                        tuple(self.puntos_actuales[-2]),
                        tuple(self.puntos_actuales[-1]),
                        (0, 255, 0),
                        2
                    )

                cv2.imshow('Definir Zonas', self.imagen_display)

                # Si completamos 4 puntos, cerrar polígono
                if len(self.puntos_actuales) == 4:
                    cv2.line(
                        self.imagen_display,
                        tuple(self.puntos_actuales[3]),
                        tuple(self.puntos_actuales[0]),
                        (0, 255, 0),
                        2
                    )
                    cv2.imshow('Definir Zonas', self.imagen_display)
                    print(f"\n✓ Zona completa. Presiona ESPACIO para guardar o R para resetear.\n")

    def resetear_zona_actual(self):
        """Resetea la zona actual"""
        self.puntos_actuales = []
        self.imagen_display = self.imagen.copy()

        # Re-dibujar zonas guardadas
        for nombre, puntos in self.zonas.items():
            color = self.colores.get(nombre, (255, 255, 255))
            pts = [[int(p[0]), int(p[1])] for p in puntos]
            cv2.polylines(self.imagen_display, [cv2.UMat(pts)], True, color, 2)

            # Etiqueta
            centroid_x = sum(p[0] for p in pts) // len(pts)
            centroid_y = sum(p[1] for p in pts) // len(pts)
            cv2.putText(
                self.imagen_display,
                nombre.upper(),
                (centroid_x - 30, centroid_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        cv2.imshow('Definir Zonas', self.imagen_display)

    def guardar_zona(self):
        """Guarda la zona actual"""
        if len(self.puntos_actuales) != 4:
            print("⚠ Necesitas marcar 4 puntos para completar la zona")
            return False

        if not self.accesos_pendientes:
            print("⚠ Ya definiste todas las zonas")
            return False

        acceso = self.accesos_pendientes.pop(0)
        self.zonas[acceso] = self.puntos_actuales.copy()

        color = self.colores.get(acceso, (255, 255, 255))

        # Re-dibujar con color final
        self.imagen_display = self.imagen.copy()
        for nombre, puntos in self.zonas.items():
            pts = [[int(p[0]), int(p[1])] for p in puntos]
            cv2.polylines(self.imagen_display, [cv2.UMat(pts)], True, self.colores[nombre], 2)

            centroid_x = sum(p[0] for p in pts) // len(pts)
            centroid_y = sum(p[1] for p in pts) // len(pts)
            cv2.putText(
                self.imagen_display,
                nombre.upper(),
                (centroid_x - 30, centroid_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                self.colores[nombre],
                2
            )

        cv2.imshow('Definir Zonas', self.imagen_display)

        print(f"✓ Zona '{acceso}' guardada: {self.puntos_actuales}")
        self.puntos_actuales = []

        if self.accesos_pendientes:
            print(f"\nAhora define: {self.accesos_pendientes[0].upper()}")
            print("Haz click en 4 puntos para marcar la zona...\n")
        else:
            print("\n✅ Todas las zonas definidas. Presiona Q para guardar y salir.\n")

        return True

    def ejecutar(self):
        """Loop principal"""
        print("\n" + "=" * 80)
        print("DEFINIDOR INTERACTIVO DE ZONAS RILSA")
        print("=" * 80)
        print("\nInstrucciones:")
        print("  - Haz click en 4 puntos para marcar cada zona de acceso")
        print("  - ESPACIO: Guardar zona actual y pasar a la siguiente")
        print("  - R: Resetear zona actual (borrar puntos)")
        print("  - Q: Terminar y guardar archivo JSON")
        print("\nOrden de definición: Norte → Sur → Este → Oeste")
        print("\n" + "=" * 80)
        print(f"\nAhora define: {self.accesos_pendientes[0].upper()}")
        print("Haz click en 4 puntos para marcar la zona...\n")

        cv2.namedWindow('Definir Zonas')
        cv2.setMouseCallback('Definir Zonas', self.click_handler)
        cv2.imshow('Definir Zonas', self.imagen_display)

        while True:
            key = cv2.waitKey(1) & 0xFF

            # ESPACIO: Guardar zona
            if key == ord(' '):
                self.guardar_zona()

            # R: Resetear
            elif key == ord('r') or key == ord('R'):
                print("↺ Reseteando zona actual...")
                self.resetear_zona_actual()

            # Q: Salir
            elif key == ord('q') or key == ord('Q'):
                if len(self.zonas) == 4:
                    break
                else:
                    print(f"\n⚠ Aún faltan zonas por definir: {self.accesos_pendientes}")
                    print("Define todas las zonas antes de salir (o cierra la ventana para cancelar)\n")

        cv2.destroyAllWindows()
        return self.zonas


def extraer_frame_video(video_path: str, output_path: str, timestamp: float = 5.0):
    """Extrae un frame del video"""
    print(f"Extrayendo frame del video en t={timestamp}s...")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir video: {video_path}")

    # Ir al timestamp
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_num = int(timestamp * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError(f"No se pudo extraer frame del video")

    cv2.imwrite(output_path, frame)
    print(f"✓ Frame guardado en: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Define zonas de acceso RILSA interactivamente',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s --frame frame.jpg --salida zonas.json
  %(prog)s --video video.mp4 --salida zonas.json --timestamp 10
        """
    )

    grupo_entrada = parser.add_mutually_exclusive_group(required=True)
    grupo_entrada.add_argument('--video', help='Archivo de video (se extraerá un frame)')
    grupo_entrada.add_argument('--frame', help='Imagen/frame del video')

    parser.add_argument('--salida', '-o', required=True, help='Archivo JSON de salida')
    parser.add_argument('--timestamp', type=float, default=5.0,
                       help='Timestamp en segundos para extraer frame (default: 5.0)')

    args = parser.parse_args()

    try:
        # Determinar imagen a usar
        if args.video:
            temp_frame = 'temp_frame.jpg'
            imagen_path = extraer_frame_video(args.video, temp_frame, args.timestamp)
        else:
            imagen_path = args.frame

        # Ejecutar definidor interactivo
        definidor = DefinidorZonas(imagen_path)
        zonas = definidor.ejecutar()

        # Guardar JSON
        with open(args.salida, 'w', encoding='utf-8') as f:
            json.dump(zonas, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 80)
        print(f"✅ Zonas guardadas en: {args.salida}")
        print("=" * 80)
        print("\nContenido:")
        print(json.dumps(zonas, indent=2))
        print("\n💡 Ahora puedes generar el aforo con:")
        print(f"   python generar_aforo_rilsa.py tracks.json --zonas {args.salida}")
        print()

        # Limpiar archivo temporal
        if args.video and Path(temp_frame).exists():
            Path(temp_frame).unlink()

        return 0

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

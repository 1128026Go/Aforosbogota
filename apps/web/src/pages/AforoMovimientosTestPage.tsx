/**
 * Página de prueba para el sistema de Aforo por Movimientos RILSA
 * Esta página demuestra el uso completo del sistema con datos reales
 */

import React from 'react';
// import { AforoMovimientosDemo } from '@/components/aforos/AforoMovimientosDemo';

export default function AforoMovimientosTestPage() {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '40px 20px',
      }}
    >
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div
          style={{
            marginBottom: '30px',
            textAlign: 'center',
            color: 'white',
          }}
        >
          <h1
            style={{
              fontSize: '36px',
              fontWeight: 'bold',
              marginBottom: '12px',
            }}
          >
            📊 Aforo por Movimientos RILSA
          </h1>
          <p style={{ fontSize: '16px', opacity: 0.9, marginBottom: '8px' }}>
            Sistema de visualización de volúmenes vehiculares por movimiento
          </p>
          <p style={{ fontSize: '14px', opacity: 0.7 }}>
            Intervalos de 15 minutos | Clasificación por tipo de vehículo | Exportación CSV
          </p>
        </div>

        {/* Instrucciones */}
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '24px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}
        >
          <h3 style={{ marginBottom: '12px', color: '#2c3e50', fontSize: '18px' }}>
            🎯 Instrucciones de Uso
          </h3>
          <ul
            style={{
              color: '#7f8c8d',
              fontSize: '14px',
              lineHeight: '1.8',
              paddingLeft: '24px',
            }}
          >
            <li>
              <strong>Pestañas:</strong> Navegue entre "Volúmenes Totales" y movimientos individuales
              usando las pestañas en la parte superior
            </li>
            <li>
              <strong>Tabla:</strong> Cada tabla muestra conteos de vehículos por intervalos de 15
              minutos
            </li>
            <li>
              <strong>Exportar:</strong> Use el botón "Exportar CSV" en cada tabla para descargar los
              datos
            </li>
            <li>
              <strong>Movimientos RILSA:</strong> Solo se muestran movimientos con datos reales
              detectados
            </li>
            <li>
              <strong>Categorías:</strong> Autos, Buses, Camiones, Motos y Bicicletas (peatones
              excluidos)
            </li>
          </ul>
        </div>

        {/* Componente principal - Temporalmente comentado hasta implementar AforoMovimientosDemo */}
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '24px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            textAlign: 'center',
          }}
        >
          <h3 style={{ color: '#e67e22', marginBottom: '16px' }}>
            🚧 Componente en Desarrollo
          </h3>
          <p style={{ color: '#7f8c8d', fontSize: '14px' }}>
            El componente AforoMovimientosDemo está siendo desarrollado.
            <br />
            Esta página estará disponible una vez que se complete la implementación.
          </p>
        </div>
        
        {/* 
        <AforoMovimientosDemo
          datasetId="f8144347"
          csvUrl="/volumenes_15min_por_movimiento.csv"
          metadata={{
            ubicacion: 'Intersección Bogotá',
            fecha: '13 de agosto de 2025',
          }}
        />
        */}

        {/* Footer con información adicional */}
        <div
          style={{
            marginTop: '40px',
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '8px',
            textAlign: 'center',
          }}
        >
          <h4 style={{ color: '#34495e', marginBottom: '12px', fontSize: '16px' }}>
            📖 Información Adicional
          </h4>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '20px',
              marginTop: '16px',
            }}
          >
            <div style={{ padding: '16px', background: '#ecf0f1', borderRadius: '6px' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3498db' }}>10</div>
              <div style={{ fontSize: '13px', color: '#7f8c8d', marginTop: '4px' }}>
                Movimientos RILSA
              </div>
            </div>
            <div style={{ padding: '16px', background: '#ecf0f1', borderRadius: '6px' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2ecc71' }}>15'</div>
              <div style={{ fontSize: '13px', color: '#7f8c8d', marginTop: '4px' }}>
                Intervalos de tiempo
              </div>
            </div>
            <div style={{ padding: '16px', background: '#ecf0f1', borderRadius: '6px' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e74c3c' }}>5</div>
              <div style={{ fontSize: '13px', color: '#7f8c8d', marginTop: '4px' }}>
                Categorías vehiculares
              </div>
            </div>
          </div>

          <div
            style={{
              marginTop: '20px',
              paddingTop: '20px',
              borderTop: '1px solid #d0d0d0',
              color: '#95a5a6',
              fontSize: '12px',
            }}
          >
            <p>
              💡 <strong>Tip:</strong> Los datos mostrados provienen del procesamiento automático de
              trayectorias detectadas por visión computacional
            </p>
            <p style={{ marginTop: '8px' }}>
              🔍 Para más detalles, consulte el archivo{' '}
              <code style={{ background: '#e0e0e0', padding: '2px 6px', borderRadius: '3px' }}>
                AFORO_POR_MOVIMIENTOS_README.md
              </code>
            </p>
          </div>
        </div>

        {/* Navegación */}
        <div style={{ marginTop: '30px', textAlign: 'center' }}>
          <button
            onClick={() => (window.location.href = '/library')}
            style={{
              padding: '12px 24px',
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              border: '2px solid white',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'white';
              e.currentTarget.style.color = '#667eea';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
              e.currentTarget.style.color = 'white';
            }}
          >
            ← Volver a Biblioteca de Aforos
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Para integrar esta página en el router, agregar en main.tsx:
 *
 * else if (path === '/test-movimientos' || path === '/test-movimientos/') {
 *   component = <AforoMovimientosTestPage />;
 * }
 */

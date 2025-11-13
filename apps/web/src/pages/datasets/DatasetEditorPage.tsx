import React, { useState } from 'react';
import { useParams } from '../../main';
import { useEvents } from '../../hooks/useEvents';
import { LoadingSpinner } from '../../components/shared/LoadingSpinner';
import { Button } from '../../components/shared/Button';
import { Badge } from '../../components/shared/Badge';
import { Modal } from '../../components/shared/Modal';
import { useToast } from '../../components/shared/Toast';
import { StepNavigation } from '../../components/shared/StepNavigation';

export function DatasetEditorPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [filters, setFilters] = useState({ skip: 0, limit: 50 });
  const { events, total, loading, updateEvent, deleteEvent } = useEvents(datasetId, filters);
  const [editingEvent, setEditingEvent] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const { showToast, ToastComponent } = useToast();

  const handleSaveEdit = async () => {
    if (!editingEvent) return;
    try {
      await updateEvent(editingEvent.track_id, {
        class: editingEvent.class,
        origin_cardinal: editingEvent.origin_cardinal,
        destination_cardinal: editingEvent.destination_cardinal,
      });
      showToast('Evento actualizado', 'success');
      setEditingEvent(null);
    } catch (err) {
      showToast('Error al actualizar', 'error');
    }
  };

  const handleDelete = async (trackId: string | number) => {
    try {
      await deleteEvent(trackId);
      showToast('Evento eliminado', 'success');
      setDeleteConfirm(null);
    } catch (err) {
      showToast('Error al eliminar', 'error');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div style={{ padding: '40px' }}>
      {/* Navegación por pasos */}
      <StepNavigation currentStepKey="editor" datasetId={datasetId} />
      
      {ToastComponent}

      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '600', marginBottom: '8px' }}>
          Editor de Eventos - {datasetId}
        </h1>
        <p style={{ color: '#6b7280' }}>Total de eventos: {total}</p>
      </div>

      {/* Tabla */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <tr>
              <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Track ID</th>
              <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Clase</th>
              <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Origen</th>
              <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Destino</th>
              <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Movimiento</th>
              <th style={{ padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event, idx) => (
              <tr key={event.track_id} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: idx % 2 === 0 ? 'white' : '#f9fafb' }}>
                <td style={{ padding: '12px', color: '#374151' }}>{event.track_id}</td>
                <td style={{ padding: '12px' }}>
                  <Badge>{event.class}</Badge>
                </td>
                <td style={{ padding: '12px', color: '#374151' }}>{event.origin_cardinal || '-'}</td>
                <td style={{ padding: '12px', color: '#374151' }}>{event.destination_cardinal || '-'}</td>
                <td style={{ padding: '12px', color: '#374151' }}>{event.movimiento_rilsa || '-'}</td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  <Button size="sm" variant="secondary" onClick={() => setEditingEvent(event)} style={{ marginRight: '8px' }}>
                    Editar
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => setDeleteConfirm(String(event.track_id))}>
                    Eliminar
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Paginación */}
        <div style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #e5e7eb' }}>
          <span style={{ color: '#6b7280', fontSize: '14px' }}>
            Mostrando {filters.skip + 1} - {Math.min(filters.skip + filters.limit, total)} de {total}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              size="sm"
              variant="secondary"
              disabled={filters.skip === 0}
              onClick={() => setFilters({ ...filters, skip: Math.max(0, filters.skip - filters.limit) })}
            >
              Anterior
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={filters.skip + filters.limit >= total}
              onClick={() => setFilters({ ...filters, skip: filters.skip + filters.limit })}
            >
              Siguiente
            </Button>
          </div>
        </div>
      </div>

      {/* Modal de edición */}
      {editingEvent && (
        <Modal
          isOpen={true}
          onClose={() => setEditingEvent(null)}
          title="Editar Evento"
          footer={
            <>
              <Button variant="secondary" onClick={() => setEditingEvent(null)}>Cancelar</Button>
              <Button variant="primary" onClick={handleSaveEdit}>Guardar</Button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>Clase:</label>
              <select
                value={editingEvent.class}
                onChange={(e) => setEditingEvent({ ...editingEvent, class: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
              >
                <option value="car">car</option>
                <option value="motorcycle">motorcycle</option>
                <option value="truck">truck</option>
                <option value="bus">bus</option>
                <option value="bicycle">bicycle</option>
                <option value="person">person</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>Origen:</label>
              <select
                value={editingEvent.origin_cardinal || ''}
                onChange={(e) => setEditingEvent({ ...editingEvent, origin_cardinal: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
              >
                <option value="">Seleccionar...</option>
                <option value="N">Norte (N)</option>
                <option value="S">Sur (S)</option>
                <option value="E">Este (E)</option>
                <option value="O">Oeste (O)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>Destino:</label>
              <select
                value={editingEvent.destination_cardinal || ''}
                onChange={(e) => setEditingEvent({ ...editingEvent, destination_cardinal: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
              >
                <option value="">Seleccionar...</option>
                <option value="N">Norte (N)</option>
                <option value="S">Sur (S)</option>
                <option value="E">Este (E)</option>
                <option value="O">Oeste (O)</option>
              </select>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal de confirmación de eliminación */}
      {deleteConfirm !== null && (
        <Modal
          isOpen={true}
          onClose={() => setDeleteConfirm(null)}
          title="Confirmar Eliminación"
          size="sm"
          footer={
            <>
              <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>Cancelar</Button>
              <Button variant="danger" onClick={() => handleDelete(deleteConfirm)}>Eliminar</Button>
            </>
          }
        >
          <p>¿Estás seguro de que deseas eliminar el evento con Track ID {deleteConfirm}?</p>
          <p style={{ color: '#ef4444', marginTop: '8px', fontSize: '14px' }}>Esta acción no se puede deshacer.</p>
        </Modal>
      )}
    </div>
  );
}

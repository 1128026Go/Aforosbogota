/**
 * Título clicable sobre el gráfico
 * Navega al detalle del aforo
 */

interface TitleOverlayProps {
  aforoId: string;
  title: string;
}

export default function TitleOverlay({ aforoId, title }: TitleOverlayProps) {
  const handleClick = () => {
    window.location.href = `/aforo/${aforoId}`;
  };

  return (
    <div
      onClick={handleClick}
      style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        background: 'rgba(0, 0, 0, 0.7)',
        color: 'white',
        padding: '10px 16px',
        borderRadius: '8px',
        cursor: 'pointer',
        fontSize: '16px',
        fontWeight: 'bold',
        zIndex: 10,
        textDecoration: 'underline',
        textDecorationStyle: 'dotted',
        transition: 'all 0.2s',
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(0, 0, 0, 0.9)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'rgba(0, 0, 0, 0.7)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {title} →
    </div>
  );
}

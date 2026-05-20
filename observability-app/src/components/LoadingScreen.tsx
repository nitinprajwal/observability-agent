import Loader from './Loader'

interface LoadingScreenProps {
  message?: string
  subtitle?: string
}

export default function LoadingScreen({
  message = 'Loading observability data…',
  subtitle = 'Connecting to observability backends…'
}: LoadingScreenProps) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e8edf5 100%)',
        zIndex: 9999,
        gap: '28px',
      }}
    >
      {/* Animated glow ring behind the loader */}
      <div
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            position: 'absolute',
            width: 160,
            height: 160,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(87,39,204,0.12) 0%, transparent 70%)',
            animation: 'pulse-glow 2s ease-in-out infinite',
          }}
        />
        <Loader />
      </div>

      {/* Text */}
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <p style={{ fontSize: 15, fontWeight: 700, color: '#1e293b', letterSpacing: '-0.01em' }}>
          {message}
        </p>
        <p style={{ fontSize: 12, color: '#94a3b8' }}>{subtitle}</p>
      </div>

      {/* Dotted progress indicator */}
      <div style={{ display: 'flex', gap: 6 }}>
        {[0, 1, 2].map(i => (
          <div
            key={i}
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: '#5727cc',
              opacity: 0.7,
              animation: `dot-bounce 1.4s ease-in-out infinite`,
              animationDelay: `${i * 0.22}s`,
            }}
          />
        ))}
      </div>

      <style>{`
        @keyframes pulse-glow {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.15); opacity: 1; }
        }
        @keyframes dot-bounce {
          0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
          40% { transform: scale(1.2); opacity: 1; }
        }
      `}</style>
    </div>
  )
}

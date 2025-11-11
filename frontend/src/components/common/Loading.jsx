const Loading = ({ fullScreen = false, size = 'md' }) => {
  const sizes = {
    sm: '20px',
    md: '40px',
    lg: '60px'
  };

  const spinnerStyle = {
    width: sizes[size],
    height: sizes[size],
    border: '4px solid #f3f4f6',
    borderTop: '4px solid #2563eb',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite'
  };

  if (fullScreen) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f9fafb'
      }}>
        <div style={spinnerStyle} />
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '40px'
    }}>
      <div style={spinnerStyle} />
    </div>
  );
};

export default Loading;
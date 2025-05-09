function HtmlViewer() {
    return (
      <div style={{ margin: 0, padding: 0 }}>
        <iframe
          src="/demo.html"
          title="HTML Page"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100vh',
            border: 'none',
            margin: 0,
            padding: 0,
            overflow: 'hidden',
            zIndex: 999
          }}
        ></iframe>
      </div>
    );
  }
  
  export default HtmlViewer;
  
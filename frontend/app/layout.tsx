import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: { default: 'Privacy Eye — AI Deepfake Detection', template: '%s | Privacy Eye' },
  description: 'AI Can Fake It. Privacy Eye Can Check It. Privacy-first deepfake & synthetic media detection platform.',
  keywords: ['deepfake detection', 'AI authenticity', 'synthetic media', 'voice clone detection', 'cybersecurity'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Bebas+Neue&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body style={{ background: '#0a0a0a', color: '#ffffff' }}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1a1a1a',
              color: '#ffffff',
              border: '1px solid rgba(220,38,38,0.3)',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: '500',
            },
            success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#dc2626', secondary: '#fff' } },
          }}
        />
      </body>
    </html>
  )
}

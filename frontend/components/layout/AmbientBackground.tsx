import React from 'react'

export const AmbientBackground: React.FC = () => {
  return (
    <div className="ambient-glow" aria-hidden="true">
      {/* Dynamic ambient radial gradients */}
      <div className="absolute top-[-10%] left-[-5%] w-[45vw] h-[45vw] rounded-full bg-brand-blue/8 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[50vw] h-[50vw] rounded-full bg-brand-violet/7 blur-[140px] pointer-events-none" />
      <div className="absolute top-[40%] right-[20%] w-[35vw] h-[35vw] rounded-full bg-brand-cyan/4 blur-[100px] pointer-events-none" />
    </div>
  )
}

export default AmbientBackground

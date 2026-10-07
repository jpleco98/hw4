// Handsome Dan: the chat assistant's avatar, a hand-drawn bulldog in Yale blue (named after Yale's mascot).
// Pure SVG, so it is crisp at any size and needs no image file.
export default function DanAvatar({ size = 40, className = '' }: { size?: number; className?: string }) {
  return (
    <svg
      className={`dan-avatar ${className}`}
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="Handsome Dan, the Campus Customs bulldog"
    >
      <circle cx="32" cy="32" r="32" fill="#00356b" />
      {/* ears */}
      <path d="M13 20c-4 1-6 7-4 12 3-1 6-4 8-8z" fill="#5b4636" />
      <path d="M51 20c4 1 6 7 4 12-3-1-6-4-8-8z" fill="#5b4636" />
      {/* head */}
      <path d="M32 13c-11 0-19 7-19 18 0 9 5 15 9 18 3 2 6 3 10 3s7-1 10-3c4-3 9-9 9-18 0-11-8-18-19-18z" fill="#f4ede1" />
      {/* brindle patch over one eye */}
      <path d="M38 19c5 0 9 4 9 9 0 2-1 3-3 3-4 0-8-3-8-7 0-3 0-5 2-5z" fill="#c9a77f" />
      {/* brow wrinkles */}
      <path d="M26 20c2-1 4-1 6 0M30 17c2-1 3-1 5 0" stroke="#b9a58c" strokeWidth="1.3" fill="none" strokeLinecap="round" />
      {/* eyes */}
      <circle cx="25.5" cy="28" r="2.6" fill="#1b1b1b" />
      <circle cx="38.5" cy="28" r="2.6" fill="#1b1b1b" />
      <circle cx="26.3" cy="27.2" r="0.8" fill="#fff" />
      <circle cx="39.3" cy="27.2" r="0.8" fill="#fff" />
      {/* jowls / muzzle */}
      <path d="M20 38c0-5 5-8 12-8s12 3 12 8c0 6-5 9-12 9s-12-3-12-9z" fill="#fbf7f0" />
      {/* nose */}
      <path d="M27.5 33.5c0-2 2-3 4.5-3s4.5 1 4.5 3c0 2-2.2 3.4-4.5 3.4s-4.5-1.4-4.5-3.4z" fill="#2a2420" />
      <path d="M32 37v3" stroke="#2a2420" strokeWidth="1.2" strokeLinecap="round" />
      {/* underbite smile with two little teeth */}
      <path d="M25 41c2 3 4.5 4 7 4s5-1 7-4" stroke="#2a2420" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      <path d="M28 41.5l1-2 1 2.3zM34 41.8l1-2.3 1 2z" fill="#fff" />
      {/* Yale-blue collar with a white "Y" tag */}
      <path d="M21 49c3 2.5 7 3.5 11 3.5s8-1 11-3.5l1.5 3c-3.5 3-8 4.5-12.5 4.5s-9-1.5-12.5-4.5z" fill="#286dc0" />
      <circle cx="32" cy="55" r="3.4" fill="#fff" />
      <path d="M30.6 53.4l1.4 1.8 1.4-1.8M32 55.2v2" stroke="#00356b" strokeWidth="0.9" fill="none" strokeLinecap="round" />
    </svg>
  )
}

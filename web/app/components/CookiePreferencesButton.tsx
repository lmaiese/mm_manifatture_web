'use client'

export default function CookiePreferencesButton() {
  const handleClick = () => {
    localStorage.removeItem('mm_cookie_consent')
    window.location.reload()
  }

  return (
    <button onClick={handleClick} className="footer-link bg-transparent border-0 p-0 cursor-pointer">
      Gestisci preferenze cookie
    </button>
  )
}

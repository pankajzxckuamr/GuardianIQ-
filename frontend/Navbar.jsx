function Navbar() {
  return (
    <nav className="bg-black text-white p-4 flex justify-between">

      <h1 className="text-2xl font-bold">
        GuardianIQ
      </h1>

      <ul className="flex gap-6">
        <li>Dashboard</li>
        <li>Alerts</li>
        <li>Profile</li>
      </ul>

    </nav>
  )
}

export default Navbar
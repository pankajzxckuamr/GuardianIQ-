import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="h-screen w-64 bg-black text-white p-5">

      <h1 className="text-2xl font-bold mb-6">
        GuardianIQ
      </h1>

      <div className="flex flex-col gap-4">

        <Link to="/dashboard">Dashboard</Link>
        <Link to="/profile">Profile</Link>

      </div>

    </div>
  );
}

export default Sidebar;
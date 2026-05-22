import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("login");
    navigate("/");
  };

  return (
    <div className="flex">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="p-6 w-full bg-gray-100 min-h-screen">

        {/* Header */}
        <div className="flex justify-between items-center mb-6">

          <h1 className="text-3xl font-bold">
            GuardianIQ Dashboard
          </h1>

          <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-4 py-2 rounded"
          >
            Logout
          </button>

        </div>

        {/* Cards */}
        <div className="grid grid-cols-3 gap-4">

          <div className="bg-red-500 text-white p-5 rounded-xl">
            Alerts
          </div>

          <div className="bg-blue-500 text-white p-5 rounded-xl">
            Active Users
          </div>

          <div className="bg-green-500 text-white p-5 rounded-xl">
            System Health
          </div>

        </div>

      </div>

    </div>
  );
}

export default Dashboard;
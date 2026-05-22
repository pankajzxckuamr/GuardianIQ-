import { useNavigate } from "react-router-dom";

function Profile() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("login");
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">

      <h1 className="text-3xl font-bold mb-6">
        User Profile
      </h1>

      <div className="bg-white p-6 rounded-2xl shadow-md max-w-xl">

        {/* Name */}
        <div className="mb-4">
          <p className="text-gray-500">Name</p>
          <p className="text-xl font-semibold">Sangita Nayek</p>
        </div>

        {/* Email */}
        <div className="mb-4">
          <p className="text-gray-500">Email</p>
          <p className="text-xl font-semibold">Sangita@example.com</p>
        </div>

        {/* Status */}
        <div className="mb-4">
          <p className="text-gray-500">Session Status</p>
          <p className="text-green-600 font-semibold">Active</p>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="mt-4 bg-red-500 text-white px-4 py-2 rounded-lg"
        >
          Logout
        </button>

      </div>

    </div>
  );
}

export default Profile;
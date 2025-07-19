import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, Share2, Trash2, User, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom'; 



const Navbar = ({ onSidebarToggle }) => {
  const navigate = useNavigate();
  const { user, logout, loading} = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);


  // Show loading state or nothing while checking auth
  if (loading) {
    return null; // Or return a loading spinner
  }


  if (!user) {
    return (
      <nav className="bg-gray-900 text-white px-6 py-4 shadow-md flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold text-white">
          noyo.ai
        </Link>
        <div className="space-x-4">
          <Link to="/login" className="hover:underline">Login</Link>
          <Link to="/signup" className="hover:underline">Signup</Link>
        </div>
      </nav>
    );
  }

  return (
    <div className="w-full h-16 bg-white shadow flex justify-between items-center px-4">
      <div className="flex items-center gap-4">
        <Menu className="cursor-pointer" onClick={onSidebarToggle} />
        <button
            onClick={() => window.location.href = 'http://localhost:5000'}
            className="bg-green-600 text-white px-6 py-3 rounded-lg"
          >
          Web 2 PDF
        </button>
      </div>
      <div className="flex items-center gap-4">
        <Share2 />
        <Trash2 />
        <div className="relative">
          <User onClick={() => setDropdownOpen(!dropdownOpen)} className="cursor-pointer" />
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-40 bg-white shadow rounded z-10">
              <ul className="text-sm text-gray-700">
                <li className="px-4 py-2 hover:bg-gray-100 cursor-pointer">Settings</li>
                <li className="px-4 py-2 hover:bg-gray-100 cursor-pointer">My Files</li>
                <li className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-red-600" onClick={
                  ()=> {
                    logout();
                    navigate('/login');
                  }
                }>Logout</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Navbar;

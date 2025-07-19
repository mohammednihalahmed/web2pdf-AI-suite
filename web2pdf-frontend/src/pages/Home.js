import React from 'react';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-[80vh] text-center px-4">
      <h1 className="text-4xl font-bold mb-6">Welcome to noyo.ai</h1>
      <div className="flex flex-col sm:flex-row gap-4">
        <button onClick={() => navigate('/login')} className="bg-blue-600 text-white px-6 py-3 rounded-lg">
          Login
        </button>
        <button onClick={() => navigate('/signup')} className="bg-gray-300 text-black px-6 py-3 rounded-lg">
          Signup
        </button>
        <button
            onClick={() => window.location.href = 'http://localhost:5000'}
            className="bg-green-600 text-white px-6 py-3 rounded-lg"
          >
          Web 2 PDF
        </button>

      </div>
    </div>
  );
};

export default Home;




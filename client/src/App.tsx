import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ItemList from './components/ItemList';

// Home page component
function Home() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center py-12 px-4">
      <div className="max-w-4xl w-full">
        {/* Central Card */}
        <div className=" rounded-2xl shadow-2xl p-12">
          {/* Logo Block */}
          <div className="text-center mb-8">
            <div className="mb-8">
              <img
                src="/devshack.png"
                alt="DevShack Logo"
                className="mx-auto w-500 h-50 object-contain"
              />
            </div>
            <h1 className="text-4xl font-bold text-black mb-4">
              Welcome to DevShack Hackathon 2026
            </h1>
            <p className="text-2xl text-white-600 font-light">Happy Building!</p>
          </div>
        </div>

        <div className="text-center">
          <Link
            to="/items"
            className="inline-block bg-black text-white px-8 py-4 rounded-lg font-semibold hover:bg-gray-800 transition-colors text-lg"
          >
            View Items →
          </Link>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-black flex flex-col">
        {/* Main Content Area */}
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/items" element={<ItemList />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

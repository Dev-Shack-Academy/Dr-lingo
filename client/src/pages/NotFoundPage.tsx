import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center text-white p-4">
      <h1 className="text-9xl font-bold text-gray-800">404</h1>
      <p className="text-2xl mt-4 mb-8">Oops! The page you're looking for doesn't exist.</p>
      <Link
        to="/"
        className="bg-white text-black px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
      >
        Back to Home
      </Link>
    </div>
  );
}

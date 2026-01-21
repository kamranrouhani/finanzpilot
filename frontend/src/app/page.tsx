export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-blue-600 mb-4">FinanzPilot</h1>
        <p className="text-xl text-slate-600 mb-8">
          Local AI Financial Advisor
        </p>
        <div className="space-x-4">
          <a
            href="/login"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Login
          </a>
          <a
            href="/register"
            className="inline-block px-6 py-3 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition"
          >
            Register
          </a>
        </div>
      </div>
    </div>
  );
}

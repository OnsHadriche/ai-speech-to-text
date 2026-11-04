import { useEffect, useState } from "react";

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {

  const [status, setStatus] = useState("Checking...");
  const [error, setError] = useState("");

  useEffect(() => {

    async function checkBackend() {

      try {

        const response = await fetch(
          `${API_URL}/api/health`
        );

        if (!response.ok) {
          throw new Error("Backend request failed");
        }

        const data = await response.json();

        setStatus(data.status);

      } catch {

        setStatus("Disconnected");

        setError("Cannot connect to FastAPI");
      }
    }

    checkBackend();

  }, []);

  return (

    <main className="min-h-screen flex items-center justify-center p-6">

      <div className="bg-white rounded-2xl shadow-lg p-10 max-w-lg w-full">

        <h1 className="text-2xl font-bold mb-3">
          AI Speech to Word
        </h1>

        <p className="text-gray-500 mb-6">
          Project development environment
        </p>

        <div className="p-4 bg-gray-100 rounded-lg">

          <p className="font-medium">
            Backend status:
          </p>

          <p className="mt-2">
            {status}
          </p>

          {error && (
            <p className="text-red-500 mt-2">
              {error}
            </p>
          )}

        </div>

      </div>

    </main>

  );
}

export default App;
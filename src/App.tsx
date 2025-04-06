import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen, Event } from "@tauri-apps/api/event";
import "./App.css";

// State Payload Interface matching Rust's StatePayload
interface StatePayload {
  count: number;
}

function App() {
  // Removed greetMsg and name state
  const [count, setCount] = useState<number>(0); // Counter state initialized to 0

  // Fetch initial state and listen for updates
  useEffect(() => {
    let unlisten: (() => void) | undefined;

    async function setupCounter() {
      try {
        // Fetch initial state
        console.log("Fetching initial state...");
        const initialCount = await invoke<number>('get_initial_state');
        setCount(initialCount);
        console.log("Initial count set to:", initialCount);

        // Listen for state changes from Rust backend
        console.log("Setting up listener for state_changed event...");
        const unlistener = await listen<StatePayload>('state_changed', (event: Event<StatePayload>) => {
          console.log("state_changed event received:", event.payload);
          setCount(event.payload.count);
        });
        unlisten = unlistener; // Store the unlisten function for cleanup
        console.log("Listener setup complete.");

      } catch (error) {
        console.error("Failed to setup counter:", error);
      }
    }

    setupCounter();

    // Cleanup listener on component unmount
    return () => {
      if (unlisten) {
        unlisten();
        console.log("Unlistened from state_changed event on component unmount.");
      }
    };
  }, []); // Empty dependency array ensures this runs only once on mount

  // Removed greet function

  // Action dispatchers (fire and forget)
  const handleIncrement = () => {
    console.log("Invoking increment command...");
    invoke('increment').catch(error => console.error("Error invoking increment:", error));
  };

  const handleDecrement = () => {
    console.log("Invoking decrement command...");
    invoke('decrement').catch(error => console.error("Error invoking decrement:", error));
  };

  return (
    <main className="container">
      <div className="row">
        <button onClick={handleIncrement}>Increment</button>
        <h2>{count}</h2>
        <button onClick={handleDecrement}>Decrement</button>
      </div>
    </main>
  );
}

export default App;

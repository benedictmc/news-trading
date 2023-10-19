import React, { useState } from 'react';
import logo from './logo.svg';
import './App.css';

const App = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [data, setData] = useState(null); // Add this line to store retrieved data

  const login = async () => {
    setIsLoading(true);

      // URL-encode the parameters
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    // Send a POST request to the Flask backend
    const response = await fetch('https://localhost:5001/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    const data = await response.json();
    setIsLoading(false);

    if (data.success) {
      setIsAuthenticated(true);
    } else {
      alert('Invalid credentials');
    }
  };

  const fetchData = async () => {
    setIsLoading(true);

    try {
      const response = await fetch('/test-endpoint');
      const result = await response.json();

      setData(result);
    } catch (error) {
      console.error("Error fetching data:", error);
    }

    setIsLoading(false);
  };

  const logout = () => {
    // Implement your logout logic here (e.g., remove tokens, reset states)
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return <div>Loading ...</div>;
  }

  return (
    <div>
      {isAuthenticated ? (
        <>
          <button onClick={logout}>Log Out</button>
        </>
      ) : (
        <>
          <input 
            type="text" 
            placeholder="Username" 
            value={username} 
            onChange={e => setUsername(e.target.value)}
          />
          <input 
            type="password" 
            placeholder="Password" 
            value={password} 
            onChange={e => setPassword(e.target.value)}
          />
          <button onClick={login}>Log In</button>
        </>
      )}
      <button onClick={fetchData}>Fetch Data</button> {/* Add this button */}
      <div>Last Ping: {data.last_ping}</div>
    </div>
  );
};

export default App;

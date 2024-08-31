import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, Navigate } from 'react-router-dom';
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import JobApplicationForm from './components/JobApplicationForm';
import Login from './components/Login';
import PostJob from './components/PostJob';
import EditJob from './components/EditJob';

function App() {
    const [token, setToken] = useState(null);

    useEffect(() => {
        const savedToken = localStorage.getItem('access_token');
        if (savedToken) {
            setToken(savedToken);
        }
    }, []);

    const handleLogin = (accessToken) => {
        setToken(accessToken);
        localStorage.setItem('access_token', accessToken);
    };

    const handleLogout = () => {
        setToken(null);
        localStorage.removeItem('access_token');
    };

    return (
        <Router>
            <div>
                <nav>
                    <Link to="/">Job Listings</Link>
                    {token ? (
                        <>
                            <Link to="/post-job">Post Job</Link>
                            <button onClick={handleLogout}>Logout</button>
                        </>
                    ) : (
                        <Link to="/login">Login</Link>
                    )}
                </nav>
                <Routes>
                    <Route path="/" element={<JobList token={token} />} />
                    <Route path="/jobs/:id" element={<JobDetail />} />
                    <Route path="/apply/:id" element={<JobApplicationForm />} />
                    <Route path="/login" element={<Login onLogin={handleLogin} />} />
                    <Route path="/post-job" element={token ? <PostJob token={token} /> : <Navigate to="/login" />} />
                    <Route path="/edit-job/:id" element={token ? <EditJob token={token} /> : <Navigate to="/login" />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;

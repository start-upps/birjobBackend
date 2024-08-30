import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import JobApplicationForm from './components/JobApplicationForm';
import Login from './components/Login';
import PostJob from './components/PostJob';

function App() {
    const [token, setToken] = useState(null);

    const handleLogin = (accessToken) => {
        setToken(accessToken);
    };

    return (
        <Router>
            <div>
                <nav>
                    <Link to="/">Job Listings</Link>
                    {token ? (
                        <>
                            <Link to="/post-job">Post Job</Link>
                            <button onClick={() => setToken(null)}>Logout</button>
                        </>
                    ) : (
                        <Link to="/login">Login</Link>
                    )}
                </nav>
                <Routes>
                    <Route path="/" element={<JobList />} />
                    <Route path="/jobs/:id" element={<JobDetail />} />
                    <Route path="/apply/:id" element={<JobApplicationForm />} />
                    <Route path="/login" element={<Login onLogin={handleLogin} />} />
                    <Route path="/post-job" element={<PostJob token={token} />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;

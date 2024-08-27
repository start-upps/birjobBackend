import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import JobApplicationForm from './components/JobApplicationForm';
import Login from './components/Login';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<JobList />} />
                <Route path="/jobs/:id" element={<JobDetail />} />
                <Route path="/apply/:id" element={<JobApplicationForm />} />
                <Route path="/login" element={<Login />} />
            </Routes>
        </Router>
    );
}

export default App;

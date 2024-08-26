import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import JobList from './JobList';
import JobDetail from './JobDetail';
import JobApplicationForm from './JobApplicationForm';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<JobList />} />
                <Route path="/jobs/:id" element={<JobDetail />} />
                <Route path="/apply/:id" element={<JobApplicationForm />} />
            </Routes>
        </Router>
    );
}

export default App;

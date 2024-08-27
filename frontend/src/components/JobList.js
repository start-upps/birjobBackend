import React, { useEffect, useState } from 'react';
import { fetchJobs } from '../api/api';

const JobList = () => {
    const [jobs, setJobs] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchJobs()
            .then(response => {
                setJobs(response.data);
            })
            .catch(error => {
                setError('Failed to fetch jobs');
                console.error('There was an error!', error);
            });
    }, []);

    if (error) {
        return <div>{error}</div>;
    }

    if (jobs.length === 0) {
        return <div>No jobs available.</div>;
    }

    return (
        <div>
            <h1>Job Listings</h1>
            <ul>
                {jobs.map(job => (
                    <li key={job.id}>
                        <h2>{job.title}</h2>
                        <p><strong>Company:</strong> {job.company}</p>
                        <p><strong>Location:</strong> {job.location}</p>
                        <p><strong>Description:</strong> {job.description}</p>
                        <p><strong>Requirements:</strong> {job.requirements}</p>
                        <p><strong>Posted At:</strong> {new Date(job.posted_at).toLocaleString()}</p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default JobList;
